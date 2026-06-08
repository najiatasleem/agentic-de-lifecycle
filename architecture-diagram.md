# Agentic DE Lifecycle - Architecture Diagram

## Multi-Agent Agentic Flow

```mermaid
graph TB
    subgraph "User Layer"
        USER[User / UI]
    end
    
    subgraph "Orchestration"
        ORCH[Orchestrator Agent]
    end
    
    subgraph "Specialized Agents"
        INGEST[Extraction Agent]
        EDA[EDA Agent]
        DQ[DQ Agent]
        RCA[RCA Agent]
        OPT[Optimization Agent]
        VAL[Validation Agent]
        OBS[Observability Agent]
    end
    
    subgraph "Knowledge Layer"
        KNOW[Knowledge Layer]
    end
    
    subgraph "Data Sources"
        DB[(Database)]
        API[(API)]
        FILES[(Files)]
    end
    
    subgraph "Output"
        TARGET[(Target System)]
    end
    
    USER --> ORCH
    ORCH --> INGEST
    ORCH --> EDA
    ORCH --> DQ
    ORCH --> RCA
    ORCH --> OPT
    ORCH --> VAL
    ORCH --> OBS
    
    INGEST --> DB
    INGEST --> API
    INGEST --> FILES
    
    EDA --> KNOW
    DQ --> KNOW
    RCA --> KNOW
    OPT --> KNOW
    VAL --> KNOW
    OBS --> KNOW
    
    KNOW --> ORCH
    
    VAL --> TARGET
    
    style USER fill:#e1f5ff
    style ORCH fill:#fff4e1
    style INGEST fill:#e8f5e9
    style EDA fill:#e8f5e9
    style DQ fill:#e8f5e9
    style RCA fill:#fce4ec
    style OPT fill:#e8f5e9
    style VAL fill:#e8f5e9
    style OBS fill:#e8f5e9
    style KNOW fill:#f3e5f5
```
