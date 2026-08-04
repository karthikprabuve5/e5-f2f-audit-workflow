"""All deep agents in one place.

``AgentFactory`` builds and runs every agent in the system. Each agent is
described once in ``AGENT_SPECS``. Because an agent's name (``AgentName``) equals
its skill folder, most fields are derived by convention:

    skill_dir           = ``/skills/<name>/`` (source dir; the skill lives in ``/skills/<name>/<name>/``)
    prompt_filename     = ``<name>-system-prompt.md``
    state_output_path   = ``/workspace/documents/outputs/<name>/results.json``

Every field is derived from the name; the only override is ``poc-485-extraction``
writing ``anchors.json`` instead of ``results.json``.

A fresh deep agent is created per run so its filesystem state is isolated. The
factory renders the prompt (with anchor placeholders), injects the document
content, invokes the agent with the caller-supplied config (Langfuse callbacks),
parses the JSON the agent wrote to its state file, and runs it through the
post-processing :class:`SchemaValidator`. It returns an :class:`AgentOutput`
bundling the raw output, the normalized output, and the validation result.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, FilesystemBackend, StateBackend
from deepagents.backends.utils import create_file_data

from ..core.detection import AgentName
from ..core.logging_setup import get_logger
from ..core.models import ModelProvider
from ..core.output_validator import SchemaValidator, ValidationResult
from ..core.prompts import PromptRenderer

logger = get_logger(__name__)

F2F_DOCUMENT_PATH = "/workspace/documents/F2F.md"
POC_DOCUMENT_PATH = "/workspace/documents/POC.md"
SKILLS_ROUTE = "/skills/"

_OUTPUT_ROOT = "/workspace/documents/outputs"
_PROMPT_SUFFIX = "-system-prompt.md"
_DEFAULT_OUTPUT_FILENAME = "results.json"


class AgentOutputError(RuntimeError):
    """Raised when an agent did not produce parseable JSON at its output path.

    When the failure is unparseable content (not a missing file), ``raw_content``
    carries the exact string the agent wrote, so callers can still persist it for
    traceability before marking the run failed.
    """

    def __init__(self, message: str, *, raw_content: str | None = None) -> None:
        super().__init__(message)
        self.raw_content = raw_content


@dataclass(frozen=True)
class AgentOutput:
    """The result of one agent run: raw output, normalized output, and validation.

    ``raw`` is exactly what the agent emitted (post-JSON-parse, pre-normalization);
    ``processed`` is the normalized copy the pipelines use and store as the
    canonical result; ``validation`` is the quality signal also embedded inside
    ``processed`` under its ``validation`` key.
    """

    agent: str
    raw: dict[str, Any]
    processed: dict[str, Any]
    validation: ValidationResult


# The human trigger message handed to each agent, all in one place. The system
# prompt drives the real behavior; this is just the invocation nudge.
AGENT_INSTRUCTIONS: dict[AgentName, str] = {
    AgentName.CLASSIFICATION: "Classify and split the encounters.",
    AgentName.POC_485_EXTRACTION: "Extract the five POC/485 anchors.",
    AgentName.ENCOUNTER_IDENTITY: "Extract the encounter identity.",
    AgentName.PRIMARY_DIAGNOSIS: "Extract and validate the primary diagnosis.",
    AgentName.SKILLED_SERVICES: "Extract and validate the skilled services.",
    AgentName.HOMEBOUND: "Extract the homebound information from the encounter.",
    AgentName.INPATIENT_DETECTION: "Detect inpatient and observation setting context.",
    AgentName.TELEHEALTH_IDENTITY: "Extract the telehealth identity parameters.",
    AgentName.SURGICAL_NOTE: "Validate the surgical note for F2F adequacy.",
}


@dataclass(frozen=True)
class AgentSpec:
    """Everything needed to build, run, and read one agent."""

    prompt_filename: str
    skill_dir: str
    input_document_path: str
    state_output_path: str
    instruction: str


def _spec(
    agent: AgentName,
    *,
    document_path: str,
    output_filename: str = _DEFAULT_OUTPUT_FILENAME,
) -> AgentSpec:
    """Build a spec, deriving skill/prompt/output paths and instruction from the name.

    ``output_filename`` is overridable for ``poc-485-extraction``, the only agent
    that does not write ``results.json``.
    """
    return AgentSpec(
        prompt_filename=f"{agent}{_PROMPT_SUFFIX}",
        skill_dir=f"/skills/{agent}/",
        input_document_path=document_path,
        state_output_path=f"{_OUTPUT_ROOT}/{agent}/{output_filename}",
        instruction=AGENT_INSTRUCTIONS[agent],
    )


AGENT_SPECS: dict[AgentName, AgentSpec] = {
    AgentName.CLASSIFICATION: _spec(AgentName.CLASSIFICATION, document_path=F2F_DOCUMENT_PATH),
    AgentName.POC_485_EXTRACTION: _spec(
        AgentName.POC_485_EXTRACTION,
        document_path=POC_DOCUMENT_PATH,
        output_filename="anchors.json",
    ),
    AgentName.ENCOUNTER_IDENTITY: _spec(
        AgentName.ENCOUNTER_IDENTITY, document_path=F2F_DOCUMENT_PATH
    ),
    AgentName.PRIMARY_DIAGNOSIS: _spec(
        AgentName.PRIMARY_DIAGNOSIS, document_path=F2F_DOCUMENT_PATH
    ),
    AgentName.SKILLED_SERVICES: _spec(
        AgentName.SKILLED_SERVICES, document_path=F2F_DOCUMENT_PATH
    ),
    AgentName.HOMEBOUND: _spec(AgentName.HOMEBOUND, document_path=F2F_DOCUMENT_PATH),
    AgentName.INPATIENT_DETECTION: _spec(
        AgentName.INPATIENT_DETECTION, document_path=F2F_DOCUMENT_PATH
    ),
    AgentName.TELEHEALTH_IDENTITY: _spec(
        AgentName.TELEHEALTH_IDENTITY, document_path=F2F_DOCUMENT_PATH
    ),
    AgentName.SURGICAL_NOTE: _spec(AgentName.SURGICAL_NOTE, document_path=F2F_DOCUMENT_PATH),
}


class AgentFactory:
    """Builds and runs deep agents from the ``AGENT_SPECS`` registry."""

    def __init__(
        self,
        *,
        model_provider: ModelProvider,
        prompt_renderer: PromptRenderer,
        skills_root: Path,
        schema_validator: SchemaValidator | None = None,
    ) -> None:
        self._model_provider = model_provider
        self._prompt_renderer = prompt_renderer
        self._skills_root = skills_root
        # Stateless post-processing collaborator; injectable for tests.
        self._validator = schema_validator or SchemaValidator()

    async def run(
        self,
        agent_name: AgentName,
        *,
        document_content: str,
        replacements: Mapping[str, str] | None = None,
        config: Mapping[str, Any] | None = None,
    ) -> AgentOutput:
        """Render, build, invoke, validate, and return the agent's output bundle."""
        spec = self._spec_for(agent_name)
        system_prompt = self._prompt_renderer.render(spec.prompt_filename, replacements)
        agent = self._build_agent(spec, system_prompt)

        logger.debug("Invoking agent", extra={"agent": str(agent_name)})
        result = await agent.ainvoke(
            {
                "messages": [{"role": "user", "content": spec.instruction}],
                "files": {spec.input_document_path: create_file_data(document_content)},
            },
            config=dict(config or {}),
        )
        return self._extract_output(agent_name, spec, result)

    def _build_agent(self, spec: AgentSpec, system_prompt: str):
        backend = CompositeBackend(
            default=StateBackend(),
            routes={
                SKILLS_ROUTE: FilesystemBackend(root_dir=str(self._skills_root), virtual_mode=True)
            },
        )
        return create_deep_agent(
            model=self._model_provider.active(),
            system_prompt=system_prompt,
            backend=backend,
            skills=[spec.skill_dir],
        )

    @staticmethod
    def _spec_for(agent_name: AgentName) -> AgentSpec:
        spec = AGENT_SPECS.get(agent_name)
        if spec is None:
            raise KeyError(
                f"Unknown agent '{agent_name}'. Known agents: {', '.join(map(str, AGENT_SPECS))}."
            )
        return spec

    def _extract_output(
        self, agent_name: AgentName, spec: AgentSpec, result: Mapping[str, Any]
    ) -> AgentOutput:
        """Read the agent's state file, parse it, then normalize + validate it.

        On unparseable content the raw string is attached to the raised error so
        the pipeline can still persist it for traceability.
        """
        files = result.get("files") or {}
        entry = files.get(spec.state_output_path)
        if entry is None:
            raise AgentOutputError(
                f"Agent '{agent_name}' did not write output at {spec.state_output_path}."
            )

        content = entry.get("content") if isinstance(entry, Mapping) else entry
        try:
            raw_output = json.loads(content)
        except (TypeError, json.JSONDecodeError) as exc:
            raw_text = content if isinstance(content, str) else None
            raise AgentOutputError(
                f"Agent '{agent_name}' output at {spec.state_output_path} is not valid JSON.",
                raw_content=raw_text,
            ) from exc

        if not isinstance(raw_output, dict):
            raise AgentOutputError(
                f"Agent '{agent_name}' output at {spec.state_output_path} is not a JSON object.",
                raw_content=content if isinstance(content, str) else None,
            )

        processed, validation = self._validator.validate(agent_name, raw_output)
        return AgentOutput(
            agent=str(agent_name),
            raw=raw_output,
            processed=processed,
            validation=validation,
        )
