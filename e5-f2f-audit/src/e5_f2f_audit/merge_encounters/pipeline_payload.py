"""Adapt live pipeline result dicts into the merge engine's ``from_mapping`` payload.

The POC and F2F pipelines accumulate their outputs in a :class:`ResultStore`, whose
``results`` dict is shaped for streaming/persistence — not for the merge engine.
:func:`build_merge_encounters_payload` performs the small, pure reshape that bridges
the two, so an in-process orchestrator can go pipeline → merge without touching disk:

    payload = build_merge_encounters_payload(poc_store.results, f2f_store.results,
                                             transaction_id=txn, client_id=client)
    merged = MergeEncountersEngine().build(TransactionOutputs.from_mapping(payload), generated_at=now)

It reads only plain data and returns a new dict; it makes no verdicts and performs
no I/O. The two source dicts are never mutated.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def build_merge_encounters_payload(
    poc_results: Mapping[str, Any],
    f2f_results: Mapping[str, Any],
    *,
    transaction_id: str | None = None,
    client_id: str | None = None,
) -> dict[str, Any]:
    """Reshape POC + F2F ``ResultStore.results`` into a ``from_mapping`` payload.

    Args:
        poc_results: A POC run's ``ResultStore.results`` (supplies ``poc_extraction``).
        f2f_results: An F2F run's ``ResultStore.results`` (supplies ``classification_f2f``
            and the per-encounter ``agents`` map). May be the same object as
            ``poc_results`` when a single shared store was used for both runs.
        transaction_id: Overrides the id; falls back to whichever source carries one.
        client_id: Optional; when omitted, ``TransactionOutputs.from_mapping`` derives
            it from the outputs.

    Returns:
        A dict with keys ``transaction_id``, ``poc_extraction``, ``classification_f2f``,
        ``agents`` (and ``client_id`` when provided), ready for
        ``TransactionOutputs.from_mapping``.
    """
    payload: dict[str, Any] = {
        "transaction_id": (
            transaction_id
            or f2f_results.get("transaction_id")
            or poc_results.get("transaction_id")
        ),
        "poc_extraction": poc_results.get("poc_485_extraction"),
        "classification_f2f": (f2f_results.get("classification") or {}).get("f2f"),
        "agents": _transpose_encounters(f2f_results.get("encounters") or {}),
    }
    if client_id:
        payload["client_id"] = client_id
    return payload


def _transpose_encounters(
    encounters: Mapping[Any, Mapping[str, Any]],
) -> dict[str, dict[int, dict[str, Any]]]:
    """Transpose ``{encounter_index: {agent: processed}}`` to ``{agent: {index: processed}}``.

    The merge engine keys per-encounter agent outputs by agent first; the store keys
    them by encounter first. Encounter indices are coerced to ``int`` to match the
    engine's expectations.
    """
    agents: dict[str, dict[int, dict[str, Any]]] = {}
    for encounter_index, agent_map in encounters.items():
        for agent_name, processed in (agent_map or {}).items():
            agents.setdefault(agent_name, {})[int(encounter_index)] = processed
    return agents
