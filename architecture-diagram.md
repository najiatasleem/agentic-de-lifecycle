# Agentic DE Lifecycle - Architecture Diagram

## Multi-Agent Agentic Flow

```mermaid
graph LR
    subgraph "User Interface"
        USER[User]
        DASH[Dashboard]
    end
    
    subgraph "Orchestration"
        COORD[Coordinator]
        WORKFLOW[Workflow Engine]
        STATE[State Manager]
    end
    
    subgraph "Data Sources"
        DB[(Database)]
        API[(API)]
        FILES[(Files)]
    end
    
    subgraph "Extraction Stage"
        EXTRACT[Extraction Agent]
        V1[Validator]
        R1[Recheck]
    end
    
    subgraph "Quality Stage"
        QUALITY[Quality Agent]
        V2[Validator]
        R2[Recheck]
    end
    
    subgraph "Transformation Stage"
        TRANSFORM[Transform Agent]
        V3[Validator]
        R3[Recheck]
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
    
    EXTRACT --> V1
    V1 -->|Pass| QUALITY
    V1 -->|Fail| R1
    R1 --> EXTRACT
    R1 --> DASH
    
    QUALITY --> V2
    V2 -->|Pass| TRANSFORM
    V2 -->|Fail| R2
    R2 --> QUALITY
    R2 --> DASH
    
    TRANSFORM --> V3
    V3 -->|Pass| TARGET
    V3 -->|Fail| R3
    R3 --> TRANSFORM
    R3 --> DASH
    
    DASH --> WORKFLOW
    STATE --> REDIS
    STATE --> PG
    
    EXTRACT --> STATE
    QUALITY --> STATE
    TRANSFORM --> STATE
    
    style USER fill:#e1f5ff
    style COORD fill:#fff4e1
    style EXTRACT fill:#e8f5e9
    style QUALITY fill:#e8f5e9
    style TRANSFORM fill:#e8f5e9
    style V1 fill:#fce4ec
    style V2 fill:#fce4ec
    style V3 fill:#fce4ec
    style R1 fill:#fff4e1
    style R2 fill:#fff4e1
    style R3 fill:#fff4e1
```
