# Encounter Selection — Flow Diagram

```mermaid
flowchart TD
    A["Load merge_encounters, soc_date,<br/>POC anchors (i_certify / undersigned)"] --> B{soc_date valid?}
    B -- No --> Bx["flag SOC_MISSING<br/>timing = UNKNOWN for all"]:::warn
    B -- Yes --> C["Step 1: Compute window<br/>[SOC-90 ... SOC+30]"]
    Bx --> C

    C --> D["Filter encounters by window<br/>(in-window kept; others reported, excluded)"]
    D --> E{Any encounter<br/>in-window?}
    E -- No --> Z1["NO_ELIGIBLE_ENCOUNTER<br/>best_encounter_index = null"]:::stop

    E -- Yes --> F["Step 2: Date alignment vs POC<br/>date_aligned = exact match to<br/>i_certify OR undersigned"]
    F --> G["Step 3: Parameter alignment per encounter<br/>Gates: in-window + provider allowed + signed note<br/>Clinical: primary dx / homebound / skilled<br/>Scored: signature strength, criteria_count (0-6)<br/>Compute weighted score 0-100 (PrimaryDx30/HB20/<br/>Skilled20/Time10/Provider10/Signature10)"]
    G --> H["Step 4: Emit date_aligned_encounter<br/>{present, encounter_index, matched_anchor}<br/>NO early exit"]

    H --> I["Step 5: Rank ALL eligible encounters"]
    I --> I1["1) Hard gates -> drop NOT_ELIGIBLE"]
    I1 --> I2["2) Primary Dx alignment (threshold)"]
    I2 --> Jq{Any encounter<br/>aligned on Primary Dx?}
    Jq -- No --> Z2["PRIMARY_DX_UNALIGNED<br/>NEEDS_HUMAN_REVIEW<br/>(recommend least-weak)"]:::warn
    Jq -- Yes --> I3["3) Clinical-pillar coverage<br/>more of {Homebound, Skilled} wins (2>1>0)"]
    I3 --> I4["4) Full criteria coverage (of 6)"]
    I4 --> I5["5) Tie-breakers: weighted score (advisory) -><br/>certified-date -> signature strength -><br/>closest-to-SOC -> defensibility"]
    I5 --> K["Best encounter determined"]

    K --> L{Best == date-aligned<br/>encounter?}
    L -- "No date-aligned exists" --> M1["selection_method = clinical_only_no_anchor<br/>flag NO_ANCHOR_DATE"]
    L -- "Yes (best is date-aligned)" --> N{Best aligned on all<br/>clinical pillars?<br/>(primary+homebound+skilled)}
    L -- "No (other out-ranks it)" --> O["DATE_MATCH_OVERRIDDEN_BY_CLINICAL<br/>NEEDS_HUMAN_REVIEW<br/>recommend best + both summaries"]:::warn

    M1 --> N
    N -- "Yes (warnings only, e.g. weak sig)" --> S["SELECTED<br/>best_is_date_aligned per case"]:::ok
    N -- "No (residual pillar gap)" --> R["DECISIVE_DATA_GAP<br/>NEEDS_HUMAN_REVIEW"]:::warn

    S --> OUT["Step 6: Output<br/>date_aligned_encounter + best_encounter_index<br/>+ best_is_date_aligned + best_encounter_score + final_statement<br/>+ per-encounter alignment + score(0-100) + breakdown<br/>+ comparison + flags"]
    R --> OUT
    O --> OUT
    Z2 --> OUT

    classDef ok fill:#1b5e20,color:#fff,stroke:#2e7d32;
    classDef warn fill:#7f5300,color:#fff,stroke:#a97400;
    classDef stop fill:#7f1d1d,color:#fff,stroke:#b91c1c;
```
