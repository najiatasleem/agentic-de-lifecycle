# Agentic DE Lifecycle - Architecture Diagram

## High-Level Architecture

```mermaid
graph TB
    subgraph "User Interface Layer"
        UI[Agent Dashboard]
        CONFIG[Configuration Manager]
        ALERT[Alert System]
    end
    
    subgraph "Orchestration Layer"
        COORD[Agent Coordinator]
        WORKFLOW[Workflow Engine]
        STATE[State Manager]
    end
    
    subgraph "Agent Layer"
        EXTRACT[Data Extraction Agent]
        QUALITY[Data Quality Agent]
        TRANSFORM[Transformation Agent]
    end
    
    subgraph "Validation Layer"
        VALIDATOR[Output Validator]
        RECHECK[Recheck Controller]
        FEEDBACK[Feedback Integrator]
    end
    
    subgraph "Data Sources"
        DB[(Database)]
        API[(API)]
        FILES[(Files)]
    end
    
    subgraph "Storage"
        REDIS[(Redis/State)]
        PG[(PostgreSQL)]
    end
    
    UI --> COORD
    CONFIG --> COORD
    ALERT --> COORD
    
    COORD --> WORKFLOW
    COORD --> STATE
    WORKFLOW --> STATE
    
    WORKFLOW --> EXTRACT
    WORKFLOW --> QUALITY
    WORKFLOW --> TRANSFORM
    
    EXTRACT --> VALIDATOR
    QUALITY --> VALIDATOR
    TRANSFORM --> VALIDATOR
    
    VALIDATOR --> RECHECK
    RECHECK --> EXTRACT
    RECHECK --> QUALITY
    RECHECK --> TRANSFORM
    
    VALIDATOR --> FEEDBACK
    FEEDBACK --> UI
    
    EXTRACT --> DB
    EXTRACT --> API
    EXTRACT --> FILES
    
    STATE --> REDIS
    STATE --> PG
    
    style UI fill:#e1f5ff
    style COORD fill:#fff4e1
    style EXTRACT fill:#e8f5e9
    style QUALITY fill:#e8f5e9
    style TRANSFORM fill:#e8f5e9
    style VALIDATOR fill:#fce4ec
    style RECHECK fill:#fce4ec
    style FEEDBACK fill:#fce4ec
```

## Detailed Agent Flow with Recheck Loops

```mermaid
sequenceDiagram
    participant User
    participant Dashboard
    participant Coordinator
    participant Workflow
    participant ExtractAgent
    participant QualityAgent
    participant TransformAgent
    participant Validator
    participant RecheckController
    participant FeedbackIntegrator
    
    User->>Dashboard: Initiate Pipeline
    Dashboard->>Coordinator: Create Workflow
    Coordinator->>Workflow: Initialize
    
    Workflow->>ExtractAgent: Execute Extraction
    ExtractAgent->>ExtractAgent: Connect to Source
    ExtractAgent->>ExtractAgent: Extract Data
    ExtractAgent->>Validator: Validate Output
    
    alt Validation Passes
        Validator-->>Workflow: Success
        Workflow->>QualityAgent: Execute Quality Check
    else Validation Fails
        Validator->>RecheckController: Trigger Recheck
        RecheckController->>RecheckController: Adjust Parameters
        RecheckController->>ExtractAgent: Retry
        ExtractAgent->>Validator: Validate Output
        
        alt Max Retries Exceeded
            RecheckController->>Dashboard: Escalate to User
            Dashboard->>User: Request Approval
            User->>Dashboard: Provide Feedback
            Dashboard->>FeedbackIntegrator: Integrate Feedback
            FeedbackIntegrator->>ExtractAgent: Update Parameters
        end
    end
    
    QualityAgent->>QualityAgent: Run Quality Checks
    QualityAgent->>Validator: Validate Output
    
    alt Validation Passes
        Validator-->>Workflow: Success
        Workflow->>TransformAgent: Execute Transformation
    else Validation Fails
        Validator->>RecheckController: Trigger Recheck
        RecheckController->>QualityAgent: Retry
    end
    
    TransformAgent->>TransformAgent: Apply Transformations
    TransformAgent->>Validator: Validate Output
    
    alt Validation Passes
        Validator-->>Workflow: Success
        Workflow->>Coordinator: Pipeline Complete
        Coordinator->>Dashboard: Notify User
    else Validation Fails
        Validator->>RecheckController: Trigger Recheck
        RecheckController->>TransformAgent: Retry
    end
```

## Recheck Loop Logic

```mermaid
graph TD
    START[Agent Execution] --> OUTPUT[Generate Output]
    OUTPUT --> VALIDATE[Validate Output]
    
    VALIDATE --> PASS{Validation Pass?}
    
    PASS -->|Yes| NEXT[Proceed to Next Agent]
    PASS -->|No| ANALYZE[Analyze Failure]
    
    ANALYZE --> CLASSIFY{Error Type}
    
    CLASSIFY -->|Transient| RETRY1[Retry with Backoff]
    CLASSIFY -->|Configuration| ALERT1[Alert User]
    CLASSIFY -->|Quality| ADJUST[Adjust Parameters]
    CLASSIFY -->|Logic| ESCALATE[Escalate to Human]
    
    RETRY1 --> OUTPUT
    ADJUST --> OUTPUT
    
    ALERT1 --> USER_INPUT[User Input]
    USER_INPUT --> OUTPUT
    
    ESCALATE --> USER_APPROVAL{User Approval}
    
    USER_APPROVAL -->|Approve| CONTINUE[Continue Execution]
    USER_APPROVAL -->|Reject| MODIFY[Modify Workflow]
    
    MODIFY --> OUTPUT
    CONTINUE --> NEXT
    
    style START fill:#e1f5ff
    style VALIDATE fill:#fff4e1
    style PASS fill:#e8f5e9
    style NEXT fill:#e8f5e9
    style ESCALATE fill:#fce4ec
    style USER_APPROVAL fill:#fce4ec
```

## State Management Flow

```mermaid
graph LR
    subgraph "Agent Execution"
        A1[Agent 1] -->|State Update| SM[State Manager]
        A2[Agent 2] -->|State Update| SM
        A3[Agent 3] -->|State Update| SM
    end
    
    subgraph "Storage"
        SM -->|Persist| REDIS[(Redis)]
        SM -->|Audit Trail| PG[(PostgreSQL)]
    end
    
    subgraph "Query"
        DASH[Dashboard] -->|Query State| SM
        WORKFLOW[Workflow Engine] -->|Query State| SM
    end
    
    REDIS -->|Retrieve| SM
    PG -->|Retrieve| SM
    
    SM -->|Return State| DASH
    SM -->|Return State| WORKFLOW
    
    style SM fill:#fff4e1
    style REDIS fill:#e1f5ff
    style PG fill:#e1f5ff
```

## Human-in-the-Loop Checkpoints

```mermaid
graph TB
    subgraph "Agent Execution"
        EXTRACT[Extraction Agent]
        QUALITY[Quality Agent]
        TRANSFORM[Transformation Agent]
    end
    
    subgraph "Checkpoints"
        CP1[Schema Validation]
        CP2[Quality Threshold]
        CP3[Transformation Logic]
    end
    
    subgraph "User Actions"
        APPROVE[Approve]
        MODIFY[Modify Parameters]
        REJECT[Reject]
    end
    
    EXTRACT --> CP1
    QUALITY --> CP2
    TRANSFORM --> CP3
    
    CP1 -->|Requires Approval| APPROVE
    CP2 -->|Below Threshold| MODIFY
    CP3 -->|Logic Violation| REJECT
    
    APPROVE -->|Resume| QUALITY
    MODIFY -->|Retry| QUALITY
    REJECT -->|Stop| END[End Workflow]
    
    style CP1 fill:#fff4e1
    style CP2 fill:#fff4e1
    style CP3 fill:#fff4e1
    style APPROVE fill:#e8f5e9
    style MODIFY fill:#fff4e1
    style REJECT fill:#fce4ec
```

## Error Handling Strategy

```mermaid
graph TD
    ERROR[Error Occurred] --> CLASSIFY{Error Classification}
    
    CLASSIFY -->|Transient| TRANSIENT[Transient Error]
    CLASSIFY -->|Configuration| CONFIG[Configuration Error]
    CLASSIFY -->|Quality| QUALITY_ERR[Quality Error]
    CLASSIFY -->|Logic| LOGIC[Logic Error]
    
    TRANSIENT --> RETRY[Automatic Retry]
    RETRY -->|Exponential Backoff| EXECUTE[Re-execute]
    
    CONFIG --> ALERT[Alert User]
    ALERT --> USER_FIX[User Correction]
    USER_FIX --> EXECUTE
    
    QUALITY_ERR --> RECHECK[Recheck Loop]
    RECHECK --> PARAM_ADJUST[Parameter Adjustment]
    PARAM_ADJUST --> EXECUTE
    
    LOGIC --> ESCALATE[Escalate to Human]
    ESCALATE --> MANUAL[Manual Intervention]
    MANUAL --> WORKFLOW_MOD[Workflow Modification]
    WORKFLOW_MOD --> EXECUTE
    
    EXECUTE --> SUCCESS{Success?}
    SUCCESS -->|Yes| CONTINUE[Continue]
    SUCCESS -->|No| ERROR
    
    style TRANSIENT fill:#e8f5e9
    style CONFIG fill:#fff4e1
    style QUALITY_ERR fill:#fff4e1
    style LOGIC fill:#fce4ec
    style ESCALATE fill:#fce4ec
```

## Technology Stack

```mermaid
graph TB
    subgraph "Core Framework"
        AIRFLOW[Apache Airflow]
        PREFECT[Prefect]
    end
    
    subgraph "State Management"
        REDIS[Redis]
        POSTGRES[PostgreSQL]
    end
    
    subgraph "Message Queue"
        RABBIT[RabbitMQ]
        KAFKA[Apache Kafka]
    end
    
    subgraph "API Layer"
        FASTAPI[FastAPI]
        FLASK[Flask]
    end
    
    subgraph "Agent Implementation"
        PYTHON[Python]
        PANDAS[Pandas]
        PYSPARK[PySpark]
        SQLALCHEMY[SQLAlchemy]
        GREAT[Great Expectations]
    end
    
    subgraph "UI/Dashboard"
        STREAMLIT[Streamlit]
        REACT[React]
        PLOTLY[Plotly]
        WEBSOCKET[WebSocket]
    end
    
    subgraph "Infrastructure"
        DOCKER[Docker]
        K8S[Kubernetes]
        PROMETHEUS[Prometheus]
        GRAFANA[Grafana]
        ELK[ELK Stack]
    end
    
    style AIRFLOW fill:#e1f5ff
    style REDIS fill:#e1f5ff
    style RABBIT fill:#e1f5ff
    style FASTAPI fill:#e1f5ff
    style PYTHON fill:#e8f5e9
    style STREAMLIT fill:#e8f5e9
    style DOCKER fill:#fff4e1
```
