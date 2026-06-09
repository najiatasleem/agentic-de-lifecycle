# Agentic Data Intelligence System - Architecture

## Problem Statement

**Assist data engineers in identifying, prioritizing, and investigating data quality issues across tables — and recommend next steps.**

Unlike deterministic pipelines, this system dynamically routes between EDA, data quality, and root cause analysis agents based on the nature and severity of issues detected. Decision-making happens at key points where multiple investigative paths exist.

## Core Agentic Principle

**Agentic = Agent autonomously chooses from multiple options when ambiguity exists**

If flow is: `Step1 → Step2 → Step3` → This is NOT agentic  
If flow is: `Step1 → Decision → [Option A, Option B, Option C] → Next step based on decision` → This IS agentic

## Trigger Points

| Trigger Type | Example | Entry Point |
|-------------|---------|-------------|
| **User-triggered** | "Analyze this table" | Direct UI input |
| **Query-triggered** | "Check all tables in this query" | Query parsing |
| **Event-triggered** | "New data load complete" | Pipeline event |
| **Scheduled** | Daily monitoring | Cron/scheduler |

## Decision Points (Agentic Core)

### Decision Point 1: EDA Output Analysis

**Input:** Null % = 93%

**Agent Options:**
- **Option A:** Ignore (known non-critical column)
- **Option B:** Flag as risk
- **Option C:** Trigger RCA
- **Option D:** Check upstream tables

**Decision Logic:** Based on column criticality, historical patterns, and business impact

### Decision Point 2: Quality Issue Detection

**Input:** Duplicate rows detected

**Agent Options:**
- **Option A:** PK validation check
- **Option B:** Source data investigation
- **Option C:** Transformation logic review
- **Option D:** Report only

**Decision Logic:** Based on severity, data volume, and downstream impact

### Decision Point 3: Freshness Issue

**Input:** Data freshness delay > 4 hours

**Agent Options:**
- **Option A:** Ingestion pipeline check
- **Option B:** Upstream source validation
- **Option C:** SLA breach alert
- **Option D:** Historical trend analysis

**Decision Logic:** Based on SLA thresholds, historical patterns, and business criticality

## Agent Boundaries (What Agents Will/Won't Do)

### ✅ What Agents WILL Do
- Detect issues (nulls, duplicates, schema changes, freshness delays)
- Prioritize issues based on severity and business impact
- Trigger deeper analysis (RCA, upstream validation, metadata lookup)
- Suggest next steps and recommendations
- Learn from historical patterns to improve decision-making

### ❌ What Agents Will NOT Do
- Automatically fix data or modify pipelines
- Create tickets or work on fixes (for now)
- Make irreversible changes to production systems
- Access systems without proper authorization
- Override human decisions without explicit approval

**Why boundaries matter:** Builds trust and ensures agents operate within safe, predictable limits.

## Self-Routing Logic Between Agents

### Routing Decision Tree

```
EDA Agent Output →
   ├─ No issues → Stop
   ├─ Minor issue → Report only
   ├─ High null % →
   │   ├─ Known non-critical → Ignore
   │   ├─ Critical column → RCA Agent
   │   └─ Upstream dependency → Upstream Validation Agent
   ├─ Duplicates →
   │   ├─ PK issue → PK Validation Agent
   │   ├─ Source issue → Source Investigation Agent
   │   └─ Transformation issue → Transformation Review Agent
   └─ Freshness delay →
       ├─ SLA breach → Alert
       ├─ Ingestion issue → Ingestion Check Agent
       └─ Upstream issue → Upstream Validation Agent
```

### Multi-Path Execution

When ambiguity exists, agents execute multiple paths in parallel:

**Example: Critical data quality issue detected**
```
Path 1: RCA Agent (investigate root cause)
Path 2: Lineage Agent (check upstream dependencies)
Path 3: Metadata Agent (lookup column definitions in Alation)
Path 4: Historical Agent (analyze trends over time)

↓ Combine insights → Final recommendation
```

## Output Usage and Integration Workflows

### What Users Do with Output

**UI Provides:**
- Issue summary with severity scores
- Root cause analysis findings
- Recommended next steps
- Historical context and patterns

**User Actions:**
- Review and approve recommendations
- Trigger deeper investigation manually
- Compare with upstream tables
- Export insights to documentation
- Feed into pipeline monitoring systems

### Integration Points

- **Pipeline Monitoring:** Feed quality metrics into existing monitoring dashboards
- **Documentation:** Auto-generate data quality reports for Confluence
- **Alerting:** Integrate with PagerDuty/Slack for critical issues
- **Data Catalog:** Sync findings with Alation for metadata enrichment
- **CI/CD:** Validate data quality before pipeline deployments

## External System Integration

### Alation/Data Dictionary Integration

**Purpose:** Conversational table and column metadata lookup

**Use Cases:**
- "Explain this column" → Agent queries Alation → Returns metadata + context
- "What is the business definition of this table?" → Retrieves from data dictionary
- "Who owns this table?" → Returns stewardship information
- "What are the SLAs for this data?" → Retrieves SLA definitions

**Implementation:**
- Alation MCP (Model Context Protocol) for API access
- Caching layer for frequently accessed metadata
- Fallback to manual documentation if Alation unavailable

### DDL-TD Table Relationship Mapping

**Purpose:** Map table relationships for upstream validation

**Mapping Sources:**
- **KA (Knowledge Articles):** Documented table relationships
- **Confluence Pages:** Team documentation on data lineage
- **Data Vault (DV):** Structural metadata and dependencies
- **Database Foreign Keys:** Technical relationships
- **Query Analysis:** Inferred relationships from SQL queries

**Upstream Validation Flow:**
```
Issue detected in Table A →
   Query DDL-TD mapping →
   Identify upstream tables (B, C, D) →
   Validate upstream data availability →
   Correlate issues across lineage →
   Report root cause location
```

## Specialized Agents

### 1. EDA Agent (Profiling Stage) ✅ BUILT

**Role:**
- Schema detection
- Column classification
- Nulls / distribution / freshness

**Decision Logic:**
- Which columns need deeper analysis?
- Should trigger quality checks?
- Should trigger RCA based on findings?

### 2. Quality Agent (Quality Stage)

**Role:**
- Scoring and risk detection
- Severity classification
- Issue prioritization

**Decision Logic:**
- Is this issue critical or ignorable?
- Should trigger RCA or report only?
- Which investigative path to take?

### 3. RCA Agent (Root Cause Analysis) 🔥 KEY DIFFERENTIATOR

**Role:**
- Investigate issues
- Run follow-up queries
- Correlate signals across multiple paths

**Multi-Path Execution:**
- Path 1: Time trend analysis
- Path 2: Upstream validation
- Path 3: Metadata lookup
- Path 4: Historical pattern matching

**Decision Logic:**
- Which root cause hypothesis to prioritize?
- When to stop investigation?
- How confident is the conclusion?

### 4. Upstream Validation Agent

**Role:**
- Validate upstream data availability
- Check corresponding tables for issues
- Correlate issues across lineage

**Decision Logic:**
- Which upstream tables to check?
- Is issue local or propagated?
- Should alert upstream teams?

### 5. Metadata Agent

**Role:**
- Query Alation for table/column definitions
- Retrieve business context and ownership
- Lookup SLAs and documentation

**Decision Logic:**
- Which metadata source to query?
- How to interpret conflicting information?
- When to fallback to manual documentation?

### 6. Orchestrator Agent (THE BRAIN)

**Role:**
- Decide which agent to trigger based on decision points
- Manage multi-path execution and result combination
- Handle retries and fallbacks
- Enforce agent boundaries

**Flow Example:**
```
User trigger →
Orchestrator →
    runs EDA Agent →
    analyzes output →
    makes decision (4 options available) →
    routes to appropriate agent(s) →
    combines multi-path results →
    returns final recommendation
```

### 7. Knowledge Layer (Learning System)

**Stores:**
- Table behavior patterns
- Known issues and resolutions
- Historical trends and seasonality
- Decision outcomes and effectiveness

**Why this matters:**
```
"add_cntct_id is usually sparse (80-90% null)"
→ System does not overreact to 93% null
→ Decision: Flag as risk, don't trigger RCA
```

## Simplified Architecture

```
                User Trigger
                     ↓
           Orchestrator Agent
                     ↓
                EDA Agent
                     ↓
           Decision Point
        ┌──────┬──────┬──────┐
        ↓      ↓      ↓      ↓
    Stop   Report   RCA    Upstream
        └──────┴──────┴──────┘
                     ↓
         Multi-Path Execution
        ┌──────┬──────┬──────┐
        ↓      ↓      ↓      ↓
    RCA  Lineage  Metadata  Historical
        └──────┴──────┴──────┘
                     ↓
         Combine Insights
                     ↓
         Knowledge Layer
                     ↓
         Final Recommendation
```

## Implementation Phases

### Phase 1 (CURRENT - Built)
- EDA Agent ✅ (rule-based Python/Pandas, no LLM)
- Basic quality checks ✅ (rule-based thresholds)
- Streamlit UI ✅
- Database + File upload modes ✅

**Status:** Rule-based only, no decision engine, no LLM integration

### Phase 2 (NEXT - High Impact)
- Orchestrator Agent (LangGraph)
- Decision Engine (hybrid rule-based + LLM)
- RCA Agent
- Self-Routing Logic
- Human-in-the-Loop UI

**This delivers true agentic behavior**

### Phase 3
- Upstream Validation Agent
- Metadata Agent (Alation integration)
- DDL-TD Table Relationship Mapping
- Multi-Path Execution
- Knowledge Layer Enhancement

### Phase 4
- Advanced integration (Alerting, Documentation, CI/CD)
- Automated ticket creation
- Pipeline modification suggestions

## Business Impact

### Today:
- Manual EDA execution
- Ad-hoc quality checks
- Reactive issue resolution

### With Agentic System:
- **Autonomous issue detection and prioritization**
- **Dynamic routing to appropriate investigative paths**
- **Multi-path analysis for complex issues**
- **Contextual recommendations based on historical patterns**
- **Reduced manual debugging time**
- **Faster root cause identification**
- **Proactive issue detection before business impact**
- **Scalable across datasets without expert dependency**

## Why This vs Existing Tools

### vs Deterministic Pipelines (Airflow, dbt)
- **Agentic:** Chooses from multiple options based on context
- **Pipelines:** Fixed sequence of steps
- **Value:** Handles ambiguity and requires less human intervention

### vs AI Coding Assistants (Windsurf, Copilot)
- **Agentic:** Autonomous decision-making with multi-path execution
- **AI Assistants:** Suggest code but don't execute decisions
- **Value:** End-to-end investigation, not just code generation

### vs Traditional EDA Tools (pandas-profiling, Great Expectations)
- **Agentic:** Contextual analysis with routing and RCA
- **Traditional Tools:** Static profiling and rule-based checks
- **Value:** Investigates root causes, not just reports symptoms

## Decision Engine Implementation

### Approach: Hybrid (Rule-Based + LLM-Powered)

**Rationale:** Rules provide deterministic decisions for clear cases; LLM handles ambiguity and context-aware decisions.

### Decision Structure

```python
decision = {
    "trigger": "high_null",
    "options": ["ignore", "dq_only", "rca", "upstream_check"],
    "chosen": "rca",
    "confidence": 0.82,
    "reason": "high_null + high_usage_column + critical_business_impact",
    "timestamp": "2026-06-09T10:00:00Z",
    "agent": "decision_engine"
}
```

### Decision Thresholds

| Metric | Threshold | Action |
|--------|-----------|--------|
| Null % | > 90% | Ignore (known sparse) |
| Null % | 50-90% + critical column | RCA |
| Null % | 50-90% + non-critical | Report only |
| Duplicates | > 5% | PK validation |
| Freshness delay | > 4 hours | Ingestion check |
| Freshness delay | > SLA | Alert |

### Decision Logging

**What to log:**
- Trigger condition
- Available options
- Chosen option
- Confidence score
- Reasoning
- Timestamp
- Agent responsible

**Why:** Audit trail, explainability, learning for knowledge layer

### Confidence Scoring

**Rule-based decisions:** Confidence = 1.0 (deterministic)

**LLM-based decisions:** Confidence = 0.0-1.0 (based on:
- Pattern match strength
- Historical precedent
- Data quality signal clarity
- Business context availability)

**Low confidence (< 0.6):** Trigger human-in-the-loop

### Decision Engine Flow

```
Input (EDA output) →
   Check rules →
      If match → execute rule (confidence = 1.0)
      If no match → query LLM →
         LLM returns decision + confidence
         If confidence < 0.6 → escalate to human
         Else → execute decision
   Log decision →
   Feed into knowledge layer
```

## Flow + Boundaries

### Defined Flow

```
Trigger (User/Query/Event/Scheduled) →
   Orchestrator →
      EDA Agent →
         Decision Engine →
            Multi-Path Execution (RCA + Metadata + Lineage + Historical) →
               Combine Insights →
                  Knowledge Layer →
                     Final Recommendation →
                        User Action
```

### Agent Boundaries (WILL vs WON'T DO)

#### ✅ Agents WILL Do
- Detect issues (nulls, duplicates, schema changes, freshness delays)
- Prioritize issues based on severity and business impact
- Trigger deeper analysis (RCA, upstream validation, metadata lookup)
- Suggest next steps and recommendations
- Learn from historical patterns to improve decision-making
- Log all decisions with reasoning

#### ❌ Agents Will NOT Do
- Automatically fix data or modify pipelines
- Create tickets or work on fixes (Phase 1)
- Make irreversible changes to production systems
- Access systems without proper authorization
- Override human decisions without explicit approval
- Delete or drop data
- Modify schema definitions
- Execute DDL statements

### Boundary Enforcement

**Implementation:**
- Permission checks before any system modification
- Read-only database access for analysis
- Explicit approval required for write operations
- Sandbox environment for testing recommendations
- Audit trail for all actions

## Multi-Path Execution

### Parallel Execution Strategy

**When:** Ambiguity exists, high business impact, or confidence < 0.8

**Paths:**
1. **RCA Agent:** Investigate root cause (time trends, correlations)
2. **Lineage Agent:** Check upstream dependencies (DDL-TD mapping)
3. **Metadata Agent:** Lookup business context (Alation)
4. **Historical Agent:** Analyze patterns over time (knowledge layer)

### Execution Flow

```
Decision: "Critical issue detected, low confidence" →
   Trigger multi-path execution →
      Parallel execution:
         Path 1: RCA Agent (investigate)
         Path 2: Lineage Agent (upstream)
         Path 3: Metadata Agent (context)
         Path 4: Historical Agent (patterns)
      Wait for all paths (timeout: 5 min) →
      Combine insights (weighted by confidence) →
      Generate final recommendation
```

### Result Combination Logic

```python
combined_result = {
    "rca_insights": {...},
    "lineage_insights": {...},
    "metadata_insights": {...},
    "historical_insights": {...},
    "final_recommendation": "trigger_rca",
    "combined_confidence": 0.87,
    "conflicting_signals": [],
    "resolution_strategy": "weighted_average"
}
```

### Timeout Handling

- Individual path timeout: 2 minutes
- Overall execution timeout: 5 minutes
- Fallback: Proceed with available insights, flag missing paths

## Lightweight Knowledge Layer

### What to Store (Phase 1)

**Past Decisions:**
- Decision trigger
- Chosen option
- Outcome (user approved/rejected)
- Effectiveness score

**Common Patterns:**
- Known sparse columns (e.g., add_cntct_id: 80-90% null)
- Known seasonal patterns
- Known upstream dependencies

**Known Issues:**
- Recurring problems
- Resolution history
- Team ownership

### Storage Schema

```python
knowledge_entry = {
    "type": "column_pattern",
    "key": "table_name.column_name",
    "pattern": "high_null",
    "typical_range": [0.8, 0.9],
    "last_observed": "2026-06-09T10:00:00Z",
    "decision_override": "do_not_trigger_rca",
    "confidence": 0.95
}
```

### Retrieval and Usage

**Query:**
```python
pattern = knowledge_layer.lookup("table_name.column_name")
if pattern and pattern.typical_range.contains(current_null_pct):
    decision = "ignore"  # Known pattern
else:
    decision = "investigate"  # New pattern
```

### Learning Mechanism

**Explicit Learning:**
- User feedback on recommendations
- Manual overrides recorded
- Pattern updates based on new data

**Implicit Learning:**
- Decision outcome tracking
- Effectiveness scoring
- Pattern drift detection

## Human-in-the-Loop Integration

### Trigger Conditions

**Escalate to human when:**
- Decision confidence < 0.6
- Multiple conflicting paths
- High business impact (critical table)
- Unknown pattern detected
- User explicitly requests review

### UI Presentation

```
⚠️ Decision Ambiguity Detected

Issue: add_cntct_id has 93% null
Confidence: 0.45 (below threshold)

Available Options:
[ ] Ignore (known sparse column)
[ ] Report only (flag as risk)
[ ] Trigger RCA (investigate root cause)
[ ] Check upstream tables (validate dependencies)

Recommendation: Trigger RCA
Reason: High null % + critical column + unknown pattern

[Approve Recommendation]  [Select Option]  [Add Note]
```

### Feedback Loop

**User Action → System Learning:**
- User selects option → Record decision
- User adds note → Store as context
- User approves → Increase confidence threshold
- User rejects → Decrease confidence, trigger re-evaluation

### Escalation Paths

**Level 1: UI Decision**
- User chooses from options
- System executes immediately

**Level 2: Team Review**
- Critical issue, high ambiguity
- Route to data engineering team
- SLA: 4 hours response

**Level 3: Management Escalation**
- Production incident
- Business impact > threshold
- Route to management with full context

### Approval Workflow

```
Agent decision →
   If confidence >= 0.8 → Auto-approve
   If confidence < 0.8 → Human review →
      User approves → Execute
      User rejects → Re-evaluate with new context
      User modifies → Execute with modification
```

## Technology Stack

### Core Framework
- **Orchestration**: Apache Airflow or Prefect
- **State Management**: Redis or PostgreSQL
- **Message Queue**: RabbitMQ or Apache Kafka
- **API Layer**: FastAPI or Flask

### Agent Implementation
- **Language**: Python 3.10+
- **Data Processing**: Pandas, PySpark
- **Database**: SQLAlchemy, psycopg2
- **Validation**: Great Expectations or Pandera
- **LLM Integration**: OpenAI API, LangChain, or LlamaIndex
- **Decision Engine**: Rule-based + LLM-powered decision making

### UI/Dashboard
- **Frontend**: Streamlit or React
- **Visualization**: Plotly or Altair
- **Real-time Updates**: WebSocket or Server-Sent Events
- **Conversational Interface**: Chat UI for natural language queries

### Infrastructure
- **Containerization**: Docker
- **Orchestration**: Kubernetes
- **Monitoring**: Prometheus + Grafana
- **Logging**: ELK Stack or Loki

### Component-Specific Technologies

#### Orchestrator Agent
- **Workflow Engine**: LangGraph for agentic workflows
- **Task Scheduling**: Celery or Dask
- **Decision Engine**: Rule-based + LLM-powered
- **State Management**: LangChain State Management

#### EDA Agent (Built)
- **Profiling**: pandas-profiling, ydata-profiling
- **Statistics**: scipy, statsmodels
- **Visualization**: Plotly, Seaborn
- **Current Implementation**: Streamlit + Pandas

#### Quality Agent
- **Quality Rules**: Great Expectations, Soda
- **Anomaly Detection**: PyOD, isolation-forest
- **Scoring**: Custom metrics + ML models
- **Severity Classification**: Rule-based + LLM

#### RCA Agent
- **Query Engine**: SQL, pandas
- **Correlation Analysis**: scipy, networkx
- **Time Series Analysis**: statsmodels, Prophet
- **Pattern Recognition**: scikit-learn, TensorFlow
- **Multi-Path Orchestration**: LangGraph parallel execution

#### Upstream Validation Agent
- **Lineage Parsing**: SQLGlot, dbt lineage
- **DDL-TD Mapping**: Custom mapping engine
- **Dependency Graph**: networkx
- **Upstream Query**: SQLAlchemy, psycopg2

#### Metadata Agent
- **Alation Integration**: Alation MCP (Model Context Protocol)
- **API Client**: httpx, requests
- **Caching**: Redis with TTL
- **Fallback**: Manual documentation parsing

#### Knowledge Layer
- **Vector Database**: Pinecone, Weaviate, or pgvector
- **Embeddings**: OpenAI Embeddings or Sentence Transformers
- **Retrieval**: LangChain Vector Store
- **Storage**: PostgreSQL with pgvector extension
- **Decision History**: PostgreSQL for tracking decision outcomes
