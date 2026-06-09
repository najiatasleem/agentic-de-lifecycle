# Agentic Data Intelligence System - Executive Architecture Diagram

## Executive Summary View

```mermaid
graph TB
    subgraph "1. TRIGGER LAYER"
        TRIG[User/Query/Event/Scheduled]
    end
    
    subgraph "2. ORCHESTRATION LAYER"
        ORCH[Orchestrator + Decision Engine]
    end
    
    subgraph "3. AGENT LAYER"
        EDA[EDA Agent]
        DQ[Quality Agent]
        RCA[RCA Agent]
        UP[Upstream Validation]
        META[Metadata Agent]
    end
    
    subgraph "4. DECISION LAYER"
        DEC[Decision Points]
        MULTI[Multi-Path Execution]
    end
    
    subgraph "5. INTELLIGENCE LAYER"
        KNOW[Knowledge Layer]
        VDB[Vector Database]
    end
    
    subgraph "6. EXTERNAL LAYER"
        ALATION[Alation]
        DDL[DDL-TD Mapping]
    end
    
    subgraph "7. OUTPUT LAYER"
        REC[Recommendations]
        ALERT[Alerts]
        REPORT[Reports]
    end
    
    TRIG --> ORCH
    ORCH --> EDA
    EDA --> DEC
    DEC --> MULTI
    MULTI --> DQ
    MULTI --> RCA
    MULTI --> UP
    MULTI --> META
    
    DQ --> KNOW
    RCA --> KNOW
    UP --> KNOW
    META --> KNOW
    KNOW --> VDB
    VDB --> ORCH
    
    UP --> DDL
    META --> ALATION
    
    ORCH --> REC
    ORCH --> ALERT
    ORCH --> REPORT
    
    style TRIG fill:#1e3a8a,stroke:#1e40af,stroke-width:3px,color:#ffffff
    style ORCH fill:#b45309,stroke:#92400e,stroke-width:3px,color:#ffffff
    style EDA fill:#166534,stroke:#14532d,stroke-width:3px,color:#ffffff
    style DQ fill:#166534,stroke:#14532d,stroke-width:3px,color:#ffffff
    style RCA fill:#991b1b,stroke:#7f1d1d,stroke-width:3px,color:#ffffff
    style UP fill:#166534,stroke:#14532d,stroke-width:3px,color:#ffffff
    style META fill:#166534,stroke:#14532d,stroke-width:3px,color:#ffffff
    style DEC fill:#7c3aed,stroke:#5b21b6,stroke-width:3px,color:#ffffff
    style MULTI fill:#c2410c,stroke:#9a3412,stroke-width:3px,color:#ffffff
    style KNOW fill:#7c3aed,stroke:#5b21b6,stroke-width:3px,color:#ffffff
    style VDB fill:#7c3aed,stroke:#5b21b6,stroke-width:3px,color:#ffffff
    style ALATION fill:#c2410c,stroke:#9a3412,stroke-width:3px,color:#ffffff
    style DDL fill:#c2410c,stroke:#9a3412,stroke-width:3px,color:#ffffff
    style REC fill:#166534,stroke:#14532d,stroke-width:3px,color:#ffffff
    style ALERT fill:#991b1b,stroke:#7f1d1d,stroke-width:3px,color:#ffffff
    style REPORT fill:#166534,stroke:#14532d,stroke-width:3px,color:#ffffff
```

## Architecture Narrative

**1. Trigger Layer** - User, query, event, or scheduled triggers initiate analysis
**2. Orchestration Layer** - Orchestrator with decision engine manages agentic workflows
**3. Agent Layer** - Specialized agents (EDA, Quality, RCA, Upstream, Metadata) execute analysis
**4. Decision Layer** - Decision points route to appropriate agents; multi-path execution for complex issues
**5. Intelligence Layer** - Knowledge layer learns patterns; vector database enables contextual decisions
**6. External Layer** - Alation for metadata; DDL-TD mapping for upstream validation
**7. Output Layer** - Recommendations, alerts, and reports guide next steps
