"""Unit tests for the AGENT_SPECS derivation and instruction coverage."""

from __future__ import annotations

from f2f_orchestration.agents.agent_factory import AGENT_INSTRUCTIONS, AGENT_SPECS
from f2f_orchestration.core.detection import AgentName


def test_every_agent_has_a_spec_and_an_instruction() -> None:
    assert set(AGENT_SPECS) == set(AgentName)
    assert set(AGENT_INSTRUCTIONS) == set(AgentName)


def test_specs_derive_prompt_skill_and_output_from_the_name() -> None:
    for name, spec in AGENT_SPECS.items():
        assert spec.prompt_filename == f"{name}-system-prompt.md"
        assert spec.skill_dir == f"/skills/{name}/"
        assert spec.state_output_path.startswith(f"/workspace/documents/outputs/{name}/")
        assert spec.instruction == AGENT_INSTRUCTIONS[name]


def test_poc_extraction_writes_anchors_others_write_results() -> None:
    poc_spec = AGENT_SPECS[AgentName.POC_485_EXTRACTION]
    assert poc_spec.state_output_path.endswith("/anchors.json")

    for name, spec in AGENT_SPECS.items():
        if name is not AgentName.POC_485_EXTRACTION:
            assert spec.state_output_path.endswith("/results.json")


def test_document_paths_match_the_source_document() -> None:
    assert AGENT_SPECS[AgentName.POC_485_EXTRACTION].input_document_path.endswith("/POC.md")
    assert AGENT_SPECS[AgentName.CLASSIFICATION].input_document_path.endswith("/F2F.md")
    assert AGENT_SPECS[AgentName.HOMEBOUND].input_document_path.endswith("/F2F.md")
