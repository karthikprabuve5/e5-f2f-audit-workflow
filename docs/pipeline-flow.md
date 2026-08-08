# F2F Audit Workflow — Code-Level Flow

End-to-end flow of the current codebase: how data enters, how agents process it,
how raw is converted to processed `*-results.json`, and how the consolidated
`merge_encounters` is assembled. Class and method names match the source.

## 1. Class-level call flow

```mermaid
flowchart TD
    subgraph BOOT["bootstrap.py (wiring — reads env)"]
        B1["build_poc_pipeline() -> PocPipeline"]
        B2["build_f2f_pipeline() -> F2fPipeline"]
        B3["build_result_store() -> ResultStore(persist_to_disk)"]
        B4["build_document_source() -> LocalDirectoryDocumentSource"]
        B5["build_agent_factory() -> AgentFactory"]
        B6["build_merge_source() -> DiskMergeSource"]
    end

    subgraph POC["PocPipeline.run(...) -> AnchorSet"]
        P1["_run_agent(AgentName.CLASSIFICATION)"]
        P2["_select_poc_encounter() ⇒ raise POCClassificationError if none"]
        P3["_run_agent(AgentName.POC_485_EXTRACTION)"]
        P4["ResultStore.store_classification('poc', ...)"]
        P5["ResultStore.store_poc_extraction(...)"]
        P6["AnchorSet.from_poc_extraction() -> AnchorSet"]
        P1 --> P4 --> P2 --> P3 --> P5 --> P6
    end

    subgraph F2F["F2fPipeline.run(...) -> dict (result_store.results)"]
        F1["_run_agent(AgentName.CLASSIFICATION)"]
        F2["EncounterNormalizer.normalize()"]
        F3["ResultStore.store_classification('f2f', ...)"]
        F4["EncounterSplitter.split() -> chunks"]
        F5["asyncio.gather( _run_encounter() per encounter )"]
        F6["_run_encounter(): EncounterAgentSelector.select()<br/>+ asyncio.gather(_run_agent per agent)"]
        F7["_record_agent_results() -> ResultStore.store_encounter_agent()<br/>(+ _persist_raw_on_failure on error)"]
        F8["_build_summary() -> ResultStore.store_summary()"]
        F1 --> F2 --> F3 --> F4 --> F5 --> F6 --> F7 --> F8
    end

    subgraph BASE["BasePipeline._run_agent (shared engine)"]
        E1["_await_launch_slot() (stagger)"]
        E2["asyncio.Semaphore (concurrency cap)"]
        E3["LangfuseTracer.agent_span()"]
        E4["_invoke_with_retries() -> _is_retryable / _backoff_delay"]
        E5["AgentFactory.run(...)"]
        E1 --> E2 --> E3 --> E4 --> E5
    end

    subgraph FACTORY["AgentFactory.run(...) -> AgentOutput"]
        G1["PromptRenderer.render(spec.prompt_filename, replacements)"]
        G2["_build_agent(): create_deep_agent(CompositeBackend{State, Filesystem})"]
        G3["agent.ainvoke({messages, files}) -> Bedrock (ModelProvider.active())"]
        G4["_extract_output(): read state file -> json.loads = raw"]
        G5["SchemaValidator.validate(agent, raw) -> (processed, ValidationResult)"]
        G6["AgentOutput{raw, processed, validation}"]
        G1 --> G2 --> G3 --> G4 --> G5 --> G6
    end

    subgraph STORE["ResultStore"]
        S1["_results dict (property .results): processed + raw + errors"]
        S2["_write() -> outputs/&lt;txn&gt;/.../*-results.json"]
        S3["_write_raw() -> *-raw.json (disk mirror when persisting)"]
    end

    subgraph MERGE["Merge encounters (pure)"]
        D0["build_merge_encounters_payload(poc_results, f2f_results)  (in-memory path)"]
        D1["DiskMergeSource.load() OR TransactionOutputs.from_mapping()"]
        D2["TransactionOutputs{poc_extraction, classification_f2f, agents}"]
        D0 --> D1
        D3["MergeEncountersEngine.build(outputs, generated_at)"]
        D4["for b in BUILDERS: b.build(outputs, EvidenceResolver)"]
        D5["_collect_data_quality() -> EncounterAgentSelector.select()"]
        D6["merge_encounters dict -> ResultStore.store_merge_encounters()"]
        D1 --> D2 --> D3 --> D4 --> D5 --> D6
    end

    B4 --> P1
    P6 -.anchors.-> F5
    F6 --> BASE
    E5 --> FACTORY
    G6 -->|processed + raw| S1
    G6 -->|processed| S2
    G6 -->|raw| S3
    S1 --> D1
    S2 --> D1
```

## 2. Sequence (who calls whom)

```mermaid
sequenceDiagram
    participant Caller as run_poc / run_f2f / your package
    participant BS as bootstrap
    participant POC as PocPipeline
    participant F2F as F2fPipeline
    participant Base as BasePipeline
    participant AF as AgentFactory
    participant SV as SchemaValidator
    participant RS as ResultStore
    participant AE as MergeEncountersEngine

    Caller->>BS: build_*_pipeline(), build_result_store()
    Caller->>POC: run(poc_content, client_name, result_store)
    POC->>Base: _run_agent(CLASSIFICATION / POC_485_EXTRACTION)
    Base->>AF: run(agent, document_content, replacements, config)
    AF->>SV: validate(agent, raw) -> processed
    AF-->>Base: AgentOutput{raw, processed, validation}
    POC->>RS: store_classification / store_poc_extraction
    POC-->>Caller: AnchorSet

    Caller->>F2F: run(f2f_content, anchors, result_store)
    F2F->>Base: _run_agent(CLASSIFICATION)
    F2F->>F2F: EncounterNormalizer.normalize / EncounterSplitter.split
    par per encounter, per agent (asyncio.gather)
        F2F->>Base: _run_encounter -> _run_agent(...)
        Base->>AF: run(...)
        AF->>SV: validate -> processed
    end
    F2F->>RS: store_encounter_agent(...) / store_summary(...)
    F2F-->>Caller: result_store.results (dict)

    Caller->>AE: build(TransactionOutputs.from_mapping(payload), generated_at)
    AE->>AE: BUILDERS[*].build() + EvidenceResolver + _collect_data_quality
    AE-->>Caller: merge_encounters dict
    Caller->>RS: store_merge_encounters(...)  (optional)
```

## 3. Key classes and their one job

| Class | File | Responsibility |
|---|---|---|
| `bootstrap` (module) | `bootstrap.py` | Reads env, constructs everything (the only env reader) |
| `PocPipeline` | `pipelines/poc_pipeline.py` | classify POC -> gate -> extract -> `AnchorSet` |
| `F2fPipeline` | `pipelines/f2f_pipeline.py` | classify F2F -> normalize -> split -> parallel agents -> summary |
| `BasePipeline` | `pipelines/base_pipeline.py` | `_run_agent`: semaphore cap, launch stagger, retry/backoff, tracing |
| `AgentFactory` | `agents/agent_factory.py` | build+invoke deep agent, `json.loads`=raw, validate=processed -> `AgentOutput` |
| `SchemaValidator` | `core/output_validator.py` | raw -> normalized/repaired processed + `ValidationResult` |
| `EncounterAgentSelector` | `core/detection.py` | pick which agents run for an encounter |
| `EncounterNormalizer` / `EncounterSplitter` | `core/` | repair page lines / cut per-encounter chunks |
| `AnchorSet` | `core/anchors.py` | the 5 POC placeholders injected into F2F prompts |
| `ResultStore` | `core/result_store.py` | in-memory `_results` (processed) + disk `*-results.json` / `*-raw.json` |
| `TransactionOutputs` | `merge_encounters/transaction_outputs.py` | normalize outputs — `from_disk` or `from_mapping` |
| `MergeEncountersEngine` | `merge_encounters/merge_engine.py` | pure: `BUILDERS` + `EvidenceResolver` + `data_quality` -> `merge_encounters` |
| `DiskMergeSource` | `merge_encounters/merge_source.py` | batch loader wrapping `TransactionOutputs.from_disk` |

## 4. The two conversions

| Conversion | Where | Result |
|---|---|---|
| raw -> results.json | `AgentFactory._extract_output` (`SchemaValidator.validate`) | `raw` (verbatim) + `processed` (normalized `-results.json`) |
| results.json -> merge_encounters | `MergeEncountersEngine.build` via `TransactionOutputs` | consolidated `merge-encounters/results.json` (topics + inline evidence + data_quality) |

Note: `AgentOutput` holds both `raw` and `processed`. After `ResultStore.store_*`
runs, `result_store.results` keeps **processed + raw + errors** in memory (raw is
also mirrored to `*-raw.json` on disk when persisting). The merge engine consumes
the processed outputs only.
