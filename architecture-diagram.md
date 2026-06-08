# Agentic DE Lifecycle - Architecture Diagram

## Multi-Agent Agentic Flow

```mermaid
graph TB
    subgraph "User Layer"
        USER[User Input/Feedback]
        DASH[Dashboard]
    end
    
    subgraph "Orchestration"
        COORD[Agent Coordinator]
        WORKFLOW[Workflow Engine]
        STATE[State Manager]
    end
    
    subgraph "Data Sources"
        DB[(Database)]
        API[(API)]
        FILES[(Files)]
    end
    
    subgraph "Agent Pipeline"
        EXTRACT[Data Extraction Agent]
        VALIDATE1[Validator]
        RECHECK1[Recheck Controller]
        
        QUALITY[Data Quality Agent]
        VALIDATE2[Validator]
        RECHECK2[Recheck Controller]
        
        TRANSFORM[Transformation Agent]
        VALIDATE3[Validator]
        RECHECK3[Recheck Controller]
    end
    
    subgraph "Storage"
        REDIS[(Redis)]
        PG[(PostgreSQL)]
    end
    
    subgraph "Output"
        TARGET[(Target System)]
    end
    
    USER --> DASH
    DASH --> COORD
    COORD --> WORKFLOW
    WORKFLOW --> STATE
    
    WORKFLOW --> EXTRACT
    EXTRACT --> DB
    EXTRACT --> API
    EXTRACT --> FILES
    
    EXTRACT --> VALIDATE1
    VALIDATE1 -->|Pass| QUALITY
    VALIDATE1 -->|Fail| RECHECK1
    RECHECK1 -->|Adjust Params| EXTRACT
    RECHECK1 -->|Max Retries| DASH
    
    QUALITY --> VALIDATE2
    VALIDATE2 -->|Pass| TRANSFORM
    VALIDATE2 -->|Fail| RECHECK2
    RECHECK2 -->|Adjust Params| QUALITY
    RECHECK2 -->|Max Retries| DASH
    
    TRANSFORM --> VALIDATE3
    VALIDATE3 -->|Pass| TARGET
    VALIDATE3 -->|Fail| RECHECK3
    RECHECK3 -->|Adjust Params| TRANSFORM
    RECHECK3 -->|Max Retries| DASH
    
    DASH -->|Feedback| WORKFLOW
    STATE --> REDIS
    STATE --> PG
    
    WORKFLOW --> STATE
    EXTRACT --> STATE
    QUALITY --> STATE
    TRANSFORM --> STATE
    
    style USER fill:#e1f5ff
    style COORD fill:#fff4e1
    style EXTRACT fill:#e8f5e9
    style QUALITY fill:#e8f5e9
    style TRANSFORM fill:#e8f5e9
    style VALIDATE1 fill:#fce4ec
    style VALIDATE2 fill:#fce4ec
    style VALIDATE3 fill:#fce4ec
    style RECHECK1 fill:#fff4e1
    style RECHECK2 fill:#fff4e1
    style RECHECK3 fill:#fff4e1
```
