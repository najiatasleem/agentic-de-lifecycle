# Agentic DE Lifecycle - Architecture Diagram

## Multi-Agent Agentic Flow

```mermaid
graph TB
    subgraph "PRESENTATION LAYER"
        direction TB
        UI[User Interface]
        AUTH[Authentication]
        RBAC[Authorization]
    end
    
    subgraph "ORCHESTRATION LAYER"
        direction TB
        ORCH[Orchestrator Agent]
        CB[Circuit Breaker]
        RETRY[Retry Logic]
        DLQ[Dead Letter Queue]
    end
    
    subgraph "AGENT LAYER"
        direction TB
        INGEST[Extraction Agent]
        EDA[EDA Agent]
        DQ[Quality Agent]
        RCA[RCA Agent]
        OPT[Optimization Agent]
        VAL[Validation Agent]
        OBS[Observability Agent]
    end
    
    subgraph "DATA LAYER"
        direction TB
        REDIS[(Redis)]
        PG[(PostgreSQL)]
        KNOW[Knowledge Layer]
        PARQUET[Parquet]
        KAFKA[Kafka]
    end
    
    subgraph "INFRASTRUCTURE LAYER"
        direction TB
        ENC[Encryption]
        AUDIT[Audit Log]
        CHECK[Checkpoint]
    end
    
    subgraph "EXTERNAL LAYER"
        direction TB
        DB[(Database)]
        API[(API)]
        FILES[(Files)]
        TARGET[(Target System)]
    end
    
    UI --> AUTH
    AUTH --> RBAC
    RBAC --> ORCH
    
    ORCH --> CB
    CB --> RETRY
    RETRY --> INGEST
    RETRY --> DLQ
    DLQ --> ORCH
    
    INGEST --> DB
    INGEST --> API
    INGEST --> FILES
    
    INGEST --> PARQUET
    PARQUET --> EDA
    EDA --> PARQUET
    PARQUET --> DQ
    DQ --> PARQUET
    PARQUET --> RCA
    RCA --> PARQUET
    PARQUET --> OPT
    OPT --> PARQUET
    PARQUET --> VAL
    VAL --> PARQUET
    PARQUET --> OBS
    OBS --> KAFKA
    KAFKA --> TARGET
    
    INGEST --> REDIS
    EDA --> REDIS
    DQ --> REDIS
    RCA --> REDIS
    OPT --> REDIS
    VAL --> REDIS
    OBS --> REDIS
    
    REDIS --> CHECK
    CHECK --> PG
    
    EDA --> KNOW
    DQ --> KNOW
    RCA --> KNOW
    OPT --> KNOW
    VAL --> KNOW
    OBS --> KNOW
    
    KNOW --> ORCH
    PG --> ORCH
    
    PARQUET --> ENC
    ENC --> TARGET
    ORCH --> AUDIT
    AUDIT --> PG
    
    style UI fill:#1e3a8a,stroke:#1e40af,stroke-width:3px,color:#ffffff
    style AUTH fill:#1e3a8a,stroke:#1e40af,stroke-width:3px,color:#ffffff
    style RBAC fill:#1e3a8a,stroke:#1e40af,stroke-width:3px,color:#ffffff
    style ORCH fill:#b45309,stroke:#92400e,stroke-width:3px,color:#ffffff
    style CB fill:#b45309,stroke:#92400e,stroke-width:3px,color:#ffffff
    style RETRY fill:#b45309,stroke:#92400e,stroke-width:3px,color:#ffffff
    style DLQ fill:#b45309,stroke:#92400e,stroke-width:3px,color:#ffffff
    style INGEST fill:#166534,stroke:#14532d,stroke-width:3px,color:#ffffff
    style EDA fill:#166534,stroke:#14532d,stroke-width:3px,color:#ffffff
    style DQ fill:#166534,stroke:#14532d,stroke-width:3px,color:#ffffff
    style RCA fill:#991b1b,stroke:#7f1d1d,stroke-width:3px,color:#ffffff
    style OPT fill:#166534,stroke:#14532d,stroke-width:3px,color:#ffffff
    style VAL fill:#166534,stroke:#14532d,stroke-width:3px,color:#ffffff
    style OBS fill:#166534,stroke:#14532d,stroke-width:3px,color:#ffffff
    style REDIS fill:#0369a1,stroke:#075985,stroke-width:3px,color:#ffffff
    style PG fill:#0369a1,stroke:#075985,stroke-width:3px,color:#ffffff
    style KNOW fill:#7c3aed,stroke:#5b21b6,stroke-width:3px,color:#ffffff
    style PARQUET fill:#c2410c,stroke:#9a3412,stroke-width:3px,color:#ffffff
    style KAFKA fill:#c2410c,stroke:#9a3412,stroke-width:3px,color:#ffffff
    style ENC fill:#7c3aed,stroke:#5b21b6,stroke-width:3px,color:#ffffff
    style AUDIT fill:#7c3aed,stroke:#5b21b6,stroke-width:3px,color:#ffffff
    style CHECK fill:#7c3aed,stroke:#5b21b6,stroke-width:3px,color:#ffffff
    style DB fill:#0369a1,stroke:#075985,stroke-width:3px,color:#ffffff
    style API fill:#0369a1,stroke:#075985,stroke-width:3px,color:#ffffff
    style FILES fill:#0369a1,stroke:#075985,stroke-width:3px,color:#ffffff
    style TARGET fill:#0369a1,stroke:#075985,stroke-width:3px,color:#ffffff
```
