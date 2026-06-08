# Agentic DE Lifecycle - Architecture Diagram

## Multi-Agent Agentic Flow

```mermaid
graph TB
    subgraph "User Interface"
        UI[User Interface]
        AUTH[Auth/SSO]
    end
    
    subgraph "Orchestration"
        ORCH[Orchestrator Agent]
        CB[Circuit Breaker]
        RETRY[Retry Logic]
    end
    
    subgraph "Data Sources"
        DB[(Database)]
        API[(API)]
        FILES[(Files)]
    end
    
    subgraph "Agent Pipeline"
        INGEST[Extraction Agent]
        EDA[EDA Agent]
        DQ[Quality Agent]
        RCA[RCA Agent]
        OPT[Optimization Agent]
        VAL[Validation Agent]
        OBS[Observability Agent]
    end
    
    subgraph "Error Handling"
        DLQ[Dead Letter Queue]
        FALLBACK[Fallback Paths]
    end
    
    subgraph "State Management"
        REDIS[(Redis)]
        PG[(PostgreSQL)]
        CHECK[Checkpoint]
    end
    
    subgraph "Knowledge Layer"
        KNOW[Knowledge Layer]
    end
    
    subgraph "Security"
        ENC[Encryption]
        RBAC[RBAC]
        AUDIT[Audit Log]
    end
    
    subgraph "Data Flow"
        PARQUET[Parquet]
        JSON[JSON]
        KAFKA[Kafka Stream]
    end
    
    subgraph "Output"
        TARGET[(Target System)]
    end
    
    UI --> AUTH
    AUTH --> ORCH
    ORCH --> CB
    CB --> RETRY
    RETRY --> INGEST
    
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
    
    RETRY --> DLQ
    DLQ --> FALLBACK
    FALLBACK --> ORCH
    
    INGEST --> REDIS
    EDA --> REDIS
    DQ --> REDIS
    RCA --> REDIS
    OPT --> REDIS
    VAL --> REDIS
    OBS --> REDIS
    
    REDIS --> CHECK
    CHECK --> PG
    
    PG --> ORCH
    
    EDA --> KNOW
    DQ --> KNOW
    RCA --> KNOW
    OPT --> KNOW
    VAL --> KNOW
    OBS --> KNOW
    
    KNOW --> ORCH
    
    UI --> RBAC
    RBAC --> ORCH
    PARQUET --> ENC
    ENC --> TARGET
    ORCH --> AUDIT
    AUDIT --> PG
    
    style UI fill:#e1f5ff,stroke:#01579b,stroke-width:2px
    style AUTH fill:#e1f5ff,stroke:#01579b,stroke-width:2px
    style ORCH fill:#fff4e1,stroke:#f57f17,stroke-width:2px
    style CB fill:#fff4e1,stroke:#f57f17,stroke-width:2px
    style RETRY fill:#fff4e1,stroke:#f57f17,stroke-width:2px
    style INGEST fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    style EDA fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    style DQ fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    style RCA fill:#fce4ec,stroke:#c62828,stroke-width:2px
    style OPT fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    style VAL fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    style OBS fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    style DLQ fill:#ffebee,stroke:#c62828,stroke-width:2px
    style FALLBACK fill:#ffebee,stroke:#c62828,stroke-width:2px
    style REDIS fill:#e3f2fd,stroke:#0277bd,stroke-width:2px
    style PG fill:#e3f2fd,stroke:#0277bd,stroke-width:2px
    style CHECK fill:#e3f2fd,stroke:#0277bd,stroke-width:2px
    style KNOW fill:#f3e5f5,stroke:#6a1b9a,stroke-width:2px
    style ENC fill:#f3e5f5,stroke:#6a1b9a,stroke-width:2px
    style RBAC fill:#f3e5f5,stroke:#6a1b9a,stroke-width:2px
    style AUDIT fill:#f3e5f5,stroke:#6a1b9a,stroke-width:2px
    style PARQUET fill:#fff3e0,stroke:#e65100,stroke-width:2px
    style JSON fill:#fff3e0,stroke:#e65100,stroke-width:2px
    style KAFKA fill:#fff3e0,stroke:#e65100,stroke-width:2px
    style DB fill:#e3f2fd,stroke:#0277bd,stroke-width:2px
    style API fill:#e3f2fd,stroke:#0277bd,stroke-width:2px
    style FILES fill:#e3f2fd,stroke:#0277bd,stroke-width:2px
    style TARGET fill:#e3f2fd,stroke:#0277bd,stroke-width:2px
```
