"""Post-processing validation and normalization for agent output.

This layer runs *after* an agent returns its parsed JSON and *before* the result
is persisted. It is fully decoupled from the agents — nothing here is passed to
``create_deep_agent`` or a model ``response_format``. Its job is to guarantee a
consistent, downstream-friendly shape:

1. **Normalize** — fill missing structural keys with typed defaults, and repair
   a few known model deviations (top-level ``agency_warnings`` that belongs under
   ``reasoning``; a truncated ``verbi`` evidence key).
2. **Validate** — check the per-agent contract from ``references/output-schema.md``
   (envelope keys, ``result`` keys, evidence-entry completeness) and the
   traceability contract (every ``evidence_refs`` id resolves to an ``evidence[]``
   entry — no dangling refs).
3. **Report** — return a :class:`ValidationResult` and embed a ``validation`` block
   in the normalized output so downstream sees both the data and a quality signal.

The policy is **normalize + flag**, with **fail-fast on critical breakage only**
(missing ``result``/``status``, dangling refs, or — for classification — a missing
``encounters`` list). Content is never fabricated: absent values are filled with
``None``/``[]``, never invented evidence.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any

from .detection import AgentName
from .logging_setup import get_logger

logger = get_logger(__name__)


# --- Shape constants ---------------------------------------------------------

SHAPE_ENVELOPE = "envelope"  # 7 F2F agents + poc-485-extraction
SHAPE_CLASSIFICATION = "classification"
SHAPE_SELECTION = "selection"  # transaction-level encounter-selection agent

# The three decision states encounter-selection may emit; anything else is a
# schema deviation (warned, not fatal).
_SELECTION_DECISIONS: frozenset[str] = frozenset(
    {"SELECTED", "NEEDS_HUMAN_REVIEW", "NO_ELIGIBLE_ENCOUNTER"}
)

# Top-level keys shared by every "envelope" agent. ``encounter_index`` is handled
# separately (filled but not flagged) because it is pipeline-owned, and the
# document-level poc extraction does not carry one at all.
_ENVELOPE_KEYS: tuple[str, ...] = (
    "schema_version",
    "parameter_id",
    "client_id",
    "evaluated_at",
    "status",
    "confidence",
    "result",
    "evidence",
    "rules_applied",
    "reasoning",
)

# Canonical top-of-file order for the envelope header fields. After normalization
# these are emitted first, in this exact order (those that exist); every other key
# (result, evidence, rules_applied, reasoning, validation, plus any extras) follows
# in its existing order. This keeps every stored result scannable and puts
# ``encounter_index`` near the top instead of wherever the model happened to place
# it (or where a late fill appended it).
_ENVELOPE_HEADER_ORDER: tuple[str, ...] = (
    "schema_version",
    "parameter_id",
    "client_id",
    "encounter_index",
    "evaluated_at",
    "status",
    "confidence",
)

# Evidence-entry keys. The 7 F2F agents use the ``field`` back-pointer contract;
# poc extraction predates it and uses ``anchor``.
_EVIDENCE_KEYS_FIELD: tuple[str, ...] = (
    "evidence_id",
    "field",
    "verbiage",
    "page",
    "line_start",
    "line_end",
)
_EVIDENCE_KEYS_ANCHOR: tuple[str, ...] = (
    "evidence_id",
    "anchor",
    "verbiage",
    "page",
    "line_start",
    "line_end",
)

_CLASSIFICATION_ENCOUNTER_KEYS: tuple[str, ...] = (
    "encounter_index",
    "encounter_category",
    "encounter_subcategory",
    "encounter_label",
    "pages",
    "page_start",
    "page_end",
    "provider_name",
    "encounter_date",
    "classification_confidence",
    "classification_notes",
)


@dataclass(frozen=True)
class AgentSchemaSpec:
    """The machine-readable contract for one agent's output.

    Mirrors that agent's ``references/output-schema.md``. This registry — not the
    markdown — is the authoritative spec the validator enforces; a drift-guard
    test asserts the two stay in sync.
    """

    shape: str
    result_keys: tuple[str, ...] = ()
    requires_encounter_index: bool = False
    evidence_item_keys: tuple[str, ...] = ()
    encounter_item_keys: tuple[str, ...] = ()


AGENT_SCHEMA_SPECS: dict[AgentName, AgentSchemaSpec] = {
    AgentName.CLASSIFICATION: AgentSchemaSpec(
        shape=SHAPE_CLASSIFICATION,
        encounter_item_keys=_CLASSIFICATION_ENCOUNTER_KEYS,
    ),
    AgentName.POC_485_EXTRACTION: AgentSchemaSpec(
        shape=SHAPE_ENVELOPE,
        result_keys=(
            "primary_diagnosis",
            "skilled_services",
            "homebound",
            "f2f_encounter_date",
            "certification",
        ),
        requires_encounter_index=False,
        evidence_item_keys=_EVIDENCE_KEYS_ANCHOR,
    ),
    AgentName.ENCOUNTER_IDENTITY: AgentSchemaSpec(
        shape=SHAPE_ENVELOPE,
        result_keys=("encounter_date", "signature", "eligible_provider"),
        requires_encounter_index=True,
        evidence_item_keys=_EVIDENCE_KEYS_FIELD,
    ),
    AgentName.PRIMARY_DIAGNOSIS: AgentSchemaSpec(
        shape=SHAPE_ENVELOPE,
        result_keys=(
            "is_documented",
            "f2f_primary_diagnosis",
            "f2f_secondary_diagnoses",
            "poc_diagnosis",
            "alignment",
            "clinical_relevance_met",
            "specificity_met",
            "medical_necessity_met",
            "pathways_met",
        ),
        requires_encounter_index=True,
        evidence_item_keys=_EVIDENCE_KEYS_FIELD,
    ),
    AgentName.SKILLED_SERVICES: AgentSchemaSpec(
        shape=SHAPE_ENVELOPE,
        result_keys=("poc_ordered_services", "is_documented", "services", "flags"),
        requires_encounter_index=True,
        evidence_item_keys=_EVIDENCE_KEYS_FIELD,
    ),
    AgentName.HOMEBOUND: AgentSchemaSpec(
        shape=SHAPE_ENVELOPE,
        result_keys=(
            "is_documented",
            "prong_1",
            "prong_2",
            "allowable_absences_noted",
            "allowable_absences",
        ),
        requires_encounter_index=True,
        evidence_item_keys=_EVIDENCE_KEYS_FIELD,
    ),
    AgentName.INPATIENT_DETECTION: AgentSchemaSpec(
        shape=SHAPE_ENVELOPE,
        result_keys=(
            "inpatient_flag",
            "setting_type",
            "facility_name",
            "admission_date",
            "discharge_date",
            "discharge_disposition",
            "community_physician",
            "flags",
        ),
        requires_encounter_index=True,
        evidence_item_keys=_EVIDENCE_KEYS_FIELD,
    ),
    AgentName.TELEHEALTH_IDENTITY: AgentSchemaSpec(
        shape=SHAPE_ENVELOPE,
        result_keys=(
            "telehealth_indicator",
            "modality",
            "platform",
            "patient_location",
            "provider_location",
            "consent",
            "conducting_provider",
            "signature",
            "flags",
        ),
        requires_encounter_index=True,
        evidence_item_keys=_EVIDENCE_KEYS_FIELD,
    ),
    AgentName.SURGICAL_NOTE: AgentSchemaSpec(
        shape=SHAPE_ENVELOPE,
        result_keys=(
            "note_type",
            "note_type_evidence_refs",
            "note_type_valid",
            "surgical_procedure",
            "setting_type",
            "hh_relevant_content",
            "f2f_adequate",
            "flags",
        ),
        requires_encounter_index=True,
        evidence_item_keys=_EVIDENCE_KEYS_FIELD,
    ),
    # Transaction-level selector: not an envelope. Validation is intentionally
    # light — it checks only the fields downstream routes on, and never forces the
    # envelope result keys onto the selection-specific ``result`` block.
    AgentName.ENCOUNTER_SELECTION: AgentSchemaSpec(shape=SHAPE_SELECTION),
}


@dataclass
class ValidationResult:
    """Structured outcome of validating one agent output."""

    agent: str
    schema_valid: bool = True
    critical: bool = False
    missing_keys: list[str] = field(default_factory=list)
    repaired_keys: list[str] = field(default_factory=list)
    dangling_refs: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        """Serializable form embedded into the processed output as ``validation``."""
        return {
            "agent": self.agent,
            "schema_valid": self.schema_valid,
            "critical": self.critical,
            "missing_keys": self.missing_keys,
            "repaired_keys": self.repaired_keys,
            "dangling_refs": self.dangling_refs,
            "warnings": self.warnings,
        }


class SchemaValidator:
    """Normalizes and validates agent output against the per-agent registry.

    Stateless: one instance can validate every agent. ``validate`` returns the
    normalized copy (with an embedded ``validation`` block) plus the
    :class:`ValidationResult`; the raw input is never mutated.
    """

    def validate(
        self, agent_name: AgentName, raw_output: dict[str, Any]
    ) -> tuple[dict[str, Any], ValidationResult]:
        """Return ``(processed, result)`` for ``raw_output`` of ``agent_name``."""
        spec = AGENT_SCHEMA_SPECS.get(agent_name)
        result = ValidationResult(agent=str(agent_name))
        if spec is None:
            result.warnings.append(f"No schema spec registered for '{agent_name}'.")
            processed = copy.deepcopy(raw_output)
            processed["validation"] = result.as_dict()
            return processed, result

        processed = copy.deepcopy(raw_output)
        if spec.shape == SHAPE_CLASSIFICATION:
            self._validate_classification(processed, spec, result)
        elif spec.shape == SHAPE_SELECTION:
            self._validate_selection(processed, result)
        else:
            self._validate_envelope(agent_name, processed, spec, result)

        result.schema_valid = not (
            result.missing_keys or result.dangling_refs or result.critical
        )
        processed["validation"] = result.as_dict()
        if spec.shape == SHAPE_ENVELOPE:
            processed = self._reorder_envelope_header(processed)

        if result.critical:
            logger.error(
                "Agent output failed critical validation",
                extra={
                    "agent": str(agent_name),
                    "missing_keys": result.missing_keys,
                    "dangling_refs": result.dangling_refs,
                },
            )
        elif not result.schema_valid:
            logger.warning(
                "Agent output normalized with schema gaps",
                extra={
                    "agent": str(agent_name),
                    "missing_keys": result.missing_keys,
                    "repaired_keys": result.repaired_keys,
                },
            )
        return processed, result

    # --- Envelope agents (7 F2F + poc) --------------------------------------

    def _validate_envelope(
        self,
        agent_name: AgentName,
        output: dict[str, Any],
        spec: AgentSchemaSpec,
        result: ValidationResult,
    ) -> None:
        self._repair_known_deviations(output, result)

        self._fill_missing(output, list(_ENVELOPE_KEYS), self._envelope_default, agent_name, result)

        # ``encounter_index`` is pipeline-owned, not model-owned: each agent sees only
        # its single-encounter chunk and cannot know its position in the document, so
        # a missing index is expected — not a schema deviation. Normalize a placeholder
        # (keeps header ordering and downstream shape) but never record it as
        # missing/repaired; the pipeline overwrites it with the authoritative index.
        if spec.requires_encounter_index and "encounter_index" not in output:
            output["encounter_index"] = self._envelope_default("encounter_index")

        # Critical: result must exist and be an object to be useful downstream.
        if not isinstance(output.get("result"), dict):
            output["result"] = {} if output.get("result") is None else output["result"]
            result.critical = True
            result.warnings.append("`result` missing or not an object.")
        else:
            self._fill_missing(
                output["result"], list(spec.result_keys), lambda _k: None, agent_name, result,
                prefix="result.",
            )

        # Critical: a status is required for downstream routing.
        if not output.get("status"):
            result.critical = True

        self._check_evidence_completeness(output, spec, result)
        self._check_dangling_refs(output, result)

    @staticmethod
    def _repair_known_deviations(output: dict[str, Any], result: ValidationResult) -> None:
        """Fix the model deviations observed in real runs (never fabricates data)."""
        # Top-level agency_warnings belongs under reasoning.
        if "agency_warnings" in output:
            reasoning = output.get("reasoning")
            if isinstance(reasoning, dict) and not reasoning.get("agency_warnings"):
                reasoning["agency_warnings"] = output.pop("agency_warnings")
                result.repaired_keys.append("reasoning.agency_warnings")

        # Truncated evidence key: "verbi" -> "verbiage".
        for entry in output.get("evidence") or []:
            if isinstance(entry, dict) and "verbi" in entry and "verbiage" not in entry:
                entry["verbiage"] = entry.pop("verbi")
                result.repaired_keys.append("evidence[].verbiage")

    def _envelope_default(self, key: str) -> Any:
        return {
            "schema_version": "1.0",
            "parameter_id": "",
            "client_id": "DEFAULT",
            "evaluated_at": "",
            "status": "",
            "confidence": 0.0,
            "result": {},
            "evidence": [],
            "rules_applied": {"cms": [], "client": []},
            "reasoning": {"status": "", "summary": "", "evidence_refs": [], "missing": None, "agency_warnings": []},
            "encounter_index": 0,
        }.get(key)

    def _check_evidence_completeness(
        self, output: dict[str, Any], spec: AgentSchemaSpec, result: ValidationResult
    ) -> None:
        """Warn (not critical) when an evidence entry lacks required keys."""
        evidence = output.get("evidence")
        if not isinstance(evidence, list):
            return
        for position, entry in enumerate(evidence):
            if not isinstance(entry, dict):
                result.warnings.append(f"evidence[{position}] is not an object.")
                continue
            missing = [key for key in spec.evidence_item_keys if key not in entry]
            if missing:
                result.warnings.append(
                    f"evidence[{position}] (id={entry.get('evidence_id')}) missing {missing}."
                )

    def _check_dangling_refs(self, output: dict[str, Any], result: ValidationResult) -> None:
        """Critical: every referenced evidence_id must exist in ``evidence[]``."""
        evidence = output.get("evidence") or []
        known = {
            entry.get("evidence_id")
            for entry in evidence
            if isinstance(entry, dict) and entry.get("evidence_id")
        }
        used = _collect_evidence_refs(output)
        dangling = sorted({ref for ref in used if ref not in known})
        if dangling:
            result.dangling_refs = dangling
            result.critical = True

    # --- Classification -----------------------------------------------------

    def _validate_classification(
        self, output: dict[str, Any], spec: AgentSchemaSpec, result: ValidationResult
    ) -> None:
        encounters = output.get("encounters")
        if not isinstance(encounters, list):
            output["encounters"] = [] if encounters is None else encounters
            result.critical = True
            result.warnings.append("`encounters` missing or not a list.")
            encounters = output.get("encounters") if isinstance(output.get("encounters"), list) else []

        # total_encounters is derivable; fill/repair from the actual list length.
        if output.get("total_encounters") != len(encounters):
            if "total_encounters" not in output:
                result.missing_keys.append("total_encounters")
            output["total_encounters"] = len(encounters)
            result.repaired_keys.append("total_encounters")

        for position, encounter in enumerate(encounters):
            if not isinstance(encounter, dict):
                result.warnings.append(f"encounters[{position}] is not an object.")
                continue
            self._fill_missing(
                encounter,
                list(spec.encounter_item_keys),
                self._classification_default,
                AgentName.CLASSIFICATION,
                result,
                prefix=f"encounters[{position}].",
            )

    # --- Encounter selection (transaction-level) ----------------------------

    def _validate_selection(self, output: dict[str, Any], result: ValidationResult) -> None:
        """Light validation for the transaction-level selection output.

        Checks only what downstream routes on — a top-level ``status``, a ``result``
        object, a present ``best_encounter_index``, and a valid ``decision`` — without
        imposing the envelope ``result`` keys on the selection-specific shape.
        """
        if not output.get("status"):
            result.critical = True
            result.warnings.append("`status` missing.")

        selection_result = output.get("result")
        if not isinstance(selection_result, dict):
            output["result"] = {} if selection_result is None else selection_result
            result.critical = True
            result.warnings.append("`result` missing or not an object.")
            return

        # ``best_encounter_index`` may be null only for NO_ELIGIBLE_ENCOUNTER, but the
        # key must exist so downstream can read it uniformly.
        if "best_encounter_index" not in selection_result:
            selection_result["best_encounter_index"] = None
            result.missing_keys.append("result.best_encounter_index")
            result.repaired_keys.append("result.best_encounter_index")

        decision = selection_result.get("decision")
        if not decision:
            result.critical = True
            result.warnings.append("`result.decision` missing.")
        elif decision not in _SELECTION_DECISIONS:
            result.warnings.append(
                f"`result.decision` '{decision}' is not one of {sorted(_SELECTION_DECISIONS)}."
            )

    @staticmethod
    def _reorder_envelope_header(output: dict[str, Any]) -> dict[str, Any]:
        """Return ``output`` with the header fields first, in canonical order.

        Only reorders keys; values are untouched. Header fields that are absent
        (e.g. ``encounter_index`` for document-level poc extraction) are skipped,
        and all non-header keys keep their existing relative order.
        """
        ordered = {key: output[key] for key in _ENVELOPE_HEADER_ORDER if key in output}
        for key, value in output.items():
            if key not in ordered:
                ordered[key] = value
        return ordered

    @staticmethod
    def _classification_default(key: str) -> Any:
        return {
            "encounter_index": 0,
            "encounter_category": "",
            "encounter_subcategory": "",
            "encounter_label": "",
            "pages": [],
            "page_start": 1,
            "page_end": 1,
            "provider_name": None,
            "encounter_date": None,
            "classification_confidence": 0.0,
            "classification_notes": "",
        }.get(key)

    # --- Shared helpers -----------------------------------------------------

    @staticmethod
    def _fill_missing(
        target: dict[str, Any],
        expected_keys: list[str],
        default_for: Any,
        agent_name: AgentName,
        result: ValidationResult,
        *,
        prefix: str = "",
    ) -> None:
        """Fill any missing keys with typed defaults, recording each one."""
        for key in expected_keys:
            if key not in target:
                target[key] = default_for(key)
                result.missing_keys.append(f"{prefix}{key}")
                result.repaired_keys.append(f"{prefix}{key}")


def _collect_evidence_refs(node: Any) -> list[str]:
    """Recursively collect every evidence id referenced anywhere in ``node``.

    Covers ``result.*.evidence_refs``, ``rules_applied.*[].evidence_refs``,
    ``reasoning.evidence_refs`` (F2F), and ``reasoning.sources[].evidence_id``
    (poc) — so integrity is checked regardless of which linkage style the agent
    uses.
    """
    refs: list[str] = []
    if isinstance(node, dict):
        for key, value in node.items():
            if key.endswith("evidence_refs") and isinstance(value, list):
                refs.extend(str(ref) for ref in value)
            elif key == "sources" and isinstance(value, list):
                for source in value:
                    if isinstance(source, dict) and source.get("evidence_id"):
                        refs.append(str(source["evidence_id"]))
            else:
                refs.extend(_collect_evidence_refs(value))
    elif isinstance(node, list):
        for item in node:
            refs.extend(_collect_evidence_refs(item))
    return refs
