# Operational Architecture - Practical Implementation Details

## Error Handling & Resilience

### Retry Mechanisms and Backoff Strategies

**Exponential Backoff with Jitter**
- Initial retry delay: 1 second
- Maximum retry delay: 60 seconds
- Backoff multiplier: 2x
- Jitter: ±25% random variation to prevent thundering herd
- Max retries: 5 attempts per operation

**Retry Configuration per Agent Type**

| Agent Type | Transient Errors | Configuration Errors | Quality Errors | Logic Errors |
|------------|------------------|---------------------|----------------|--------------|
| Extraction | Retry with backoff | Alert user | Recheck with adjusted params | Escalate to human |
| EDA | Retry with backoff | Alert user | Recheck with adjusted params | Escalate to human |
| Quality | Retry with backoff | Alert user | Recheck with adjusted params | Escalate to human |
| RCA | Retry with backoff | Alert user | Recheck with adjusted params | Escalate to human |
| Optimization | Retry with backoff | Alert user | Recheck with adjusted params | Escalate to human |
| Validation | Retry with backoff | Alert user | Recheck with adjusted params | Escalate to human |
| Observability | Retry with backoff | Alert user | Recheck with adjusted params | Escalate to human |

### Circuit Breakers for Failing Agents

**Circuit Breaker States**
- **Closed**: Normal operation, requests pass through
- **Open**: Requests fail immediately, no retries
- **Half-Open**: Limited requests allowed to test recovery

**Circuit Breaker Configuration**
- Failure threshold: 5 consecutive failures
- Success threshold: 3 consecutive successes to close
- Timeout: 60 seconds before attempting half-open
- Half-open max requests: 3 requests

**Implementation per Agent**
```python
# Pseudo-code for circuit breaker
class AgentCircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.state = "CLOSED"
        self.last_failure_time = None
    
    def call_agent(self, agent_func, *args, **kwargs):
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "HALF_OPEN"
            else:
                raise CircuitBreakerOpenError()
        
        try:
            result = agent_func(*args, **kwargs)
            if self.state == "HALF_OPEN":
                self.success_count += 1
                if self.success_count >= 3:
                    self.state = "CLOSED"
                    self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
            raise
```

### Dead Letter Queues for Failed Tasks

**DLQ Configuration**
- Queue: RabbitMQ or Kafka dead letter queue
- Retention: 7 days
- Max size: 10 GB per queue
- Automatic replay: Manual trigger only

**DLQ Message Schema**
```json
{
  "task_id": "uuid",
  "agent_type": "extraction|eda|quality|rca|optimization|validation|observability",
  "original_payload": {...},
  "error_type": "transient|configuration|quality|logic",
  "error_message": "...",
  "retry_count": 3,
  "timestamp": "2026-06-08T10:00:00Z",
  "stack_trace": "..."
}
```

**DLQ Monitoring**
- Alert when DLQ size > 100 messages
- Daily DLQ review by operations team
- Automatic classification of error patterns

### Fallback Paths When Agents Fail

**Fallback Hierarchy**
1. **Retry with adjusted parameters** - Automatic
2. **Switch to alternative agent** - If available
3. **Use cached/stale data** - For non-critical operations
4. **Graceful degradation** - Reduce functionality
5. **Manual intervention** - Last resort

**Fallback Examples**
- **Extraction Agent fails**: Switch to cached extraction from previous run
- **EDA Agent fails**: Use basic statistics instead of full profiling
- **Quality Agent fails**: Skip quality checks, proceed with warning
- **RCA Agent fails**: Return basic error without investigation
- **Optimization Agent fails**: Use default transformation rules
- **Validation Agent fails**: Log validation failure, proceed to delivery
- **Observability Agent fails**: Use basic metrics instead of advanced analytics

## Security & Governance

### Authentication/Authorization Flow

**Authentication Mechanisms**
- **Internal Users**: Dell SSO (SAML 2.0 / OIDC)
- **Service Accounts**: OAuth 2.0 client credentials
- **API Keys**: For external integrations (rotated every 90 days)

**Authorization Model (RBAC)**
| Role | Permissions |
|------|-------------|
| **Admin** | Full access to all agents, configurations, and user management |
| **Data Engineer** | Execute agents, view results, modify configurations |
| **Data Analyst** | View EDA results, run quality checks, read-only access |
| **Business User** | View dashboards, receive alerts, no agent execution |
| **Auditor** | Read-only access to audit logs and compliance reports |

**Auth Flow**
```
User → SSO Login → JWT Token → API Gateway → Validate Token → Agent Execution
```

### Data Encryption

**Encryption at Rest**
- **Databases**: AES-256 encryption (PostgreSQL TDE)
- **File Storage**: AES-256 encryption (Dell internal storage)
- **Backups**: AES-256 encryption with separate key management

**Encryption in Transit**
- **API Calls**: TLS 1.3
- **Database Connections**: SSL/TLS
- **Message Queue**: TLS 1.3
- **Internal Service Communication**: mTLS (mutual TLS)

**Key Management**
- **KMS**: Dell Key Management Service
- **Key Rotation**: Every 90 days
- **Key Access**: Role-based, audit logged

### Compliance Logging

**GDPR Compliance**
- Data access logging (who accessed what data and when)
- Data retention policies (auto-delete after X days)
- Right to be forgotten (data purge capability)
- Data breach notification (within 72 hours)

**SOC2 Compliance**
- Change management logging (all configuration changes)
- Access control logging (all authentication/authorization events)
- Incident response logging (all security incidents)
- Regular penetration testing (quarterly)

**Audit Log Schema**
```json
{
  "event_id": "uuid",
  "timestamp": "2026-06-08T10:00:00Z",
  "user_id": "user@domain.com",
  "action": "agent_execute|config_change|data_access",
  "resource": "agent_id|table_name|config_key",
  "result": "success|failure",
  "ip_address": "10.0.0.1",
  "user_agent": "Mozilla/5.0...",
  "additional_context": {...}
}
```

**Log Retention**
- Audit logs: 7 years
- Application logs: 1 year
- Security logs: 7 years
- Performance logs: 90 days

## State Management Details

### State Persistence Strategy

**Redis (Hot State)**
- **Purpose**: Fast access to current agent states
- **Data**: Active workflow states, agent execution status, session data
- **TTL**: 24 hours (auto-expire)
- **Persistence**: RDB snapshots every 5 minutes
- **Replication**: Master-slave with automatic failover

**PostgreSQL (Cold State)**
- **Purpose**: Long-term state storage and audit trail
- **Data**: Workflow history, agent results, configuration changes
- **Retention**: 7 years
- **Backups**: Daily full backups, hourly incremental
- **Replication**: Streaming replication with read replicas

**State Partitioning**
```
Redis:
- workflow:{workflow_id} → Current workflow state
- agent:{agent_id} → Current agent state
- session:{session_id} → User session data

PostgreSQL:
- workflows → Workflow history
- agent_states → Agent execution history
- audit_logs → Audit trail
- configurations → Configuration history
```

### State Consistency Guarantees

**Consistency Levels**
- **Strong Consistency**: Critical state (workflow status, agent decisions)
- **Eventual Consistency**: Non-critical state (metrics, statistics)
- **Best Effort**: Temporary state (session data, cache)

**Consistency Mechanisms**
- **Distributed Locks**: Redis RedLock for critical operations
- **Optimistic Concurrency**: Version numbers for state updates
- **Transaction Boundaries**: ACID transactions for PostgreSQL writes
- **Idempotency**: All state updates are idempotent

### Checkpoint/Resume Mechanisms

**Checkpoint Strategy**
- **Frequency**: After each agent completes
- **Scope**: Agent output, validation results, user feedback
- **Storage**: PostgreSQL (persistent) + Redis (cache)

**Checkpoint Schema**
```json
{
  "checkpoint_id": "uuid",
  "workflow_id": "workflow_123",
  "agent_id": "eda_agent_001",
  "timestamp": "2026-06-08T10:00:00Z",
  "state": {
    "agent_output": {...},
    "validation_results": {...},
    "user_feedback": {...}
  },
  "next_agent": "quality_agent"
}
```

**Resume Logic**
```
1. User requests resume
2. Load latest checkpoint for workflow
3. Restore agent state from checkpoint
4. Resume from next_agent in sequence
5. Skip completed agents
6. Re-run only failed/pending agents
```

### State Recovery After Failures

**Recovery Scenarios**
- **Agent Crash**: Restore from last checkpoint, re-run agent
- **Workflow Engine Crash**: Restore from PostgreSQL, resume workflow
- **Redis Failure**: Failover to slave, rebuild from PostgreSQL
- **PostgreSQL Failure**: Failover to replica, minimal data loss (< 5 min)

**Recovery Procedures**
1. **Detection**: Health checks detect failure
2. **Isolation**: Failing component is isolated
3. **Recovery**: Automatic failover or manual intervention
4. **Verification**: Health checks verify recovery
5. **Resumption**: Workflow resumes from last checkpoint

**RTO/RPO Targets**
- **RTO (Recovery Time Objective)**: 15 minutes
- **RPO (Recovery Point Objective)**: 5 minutes

## Data Flow Specifics

### Data Formats Between Agents

**Internal Data Format**
- **Primary**: Apache Parquet (columnar, efficient for analytics)
- **Fallback**: JSON (for small datasets, debugging)
- **Streaming**: Apache Avro (for real-time data)

**Data Format Schema**
```json
{
  "metadata": {
    "source_agent": "extraction_agent",
    "target_agent": "eda_agent",
    "timestamp": "2026-06-08T10:00:00Z",
    "data_format": "parquet",
    "schema_version": "1.0"
  },
  "data": "...",
  "schema": {
    "columns": [...],
    "types": [...],
    "constraints": {...}
  }
}
```

**Format Conversion**
- **Extraction → EDA**: Database → Parquet
- **EDA → Quality**: Parquet → Parquet (with quality metadata)
- **Quality → RCA**: Parquet → Parquet (with RCA annotations)
- **RCA → Optimization**: Parquet → Parquet (with optimization suggestions)
- **Optimization → Validation**: Parquet → Parquet (transformed)
- **Validation → Observability**: Parquet → Parquet (with metrics)

### Data Volume Handling

**Batch Processing**
- **Small datasets** (< 1GB): In-memory processing (Pandas)
- **Medium datasets** (1GB - 100GB): Distributed processing (PySpark)
- **Large datasets** (> 100GB): Distributed processing with partitioning (PySpark)

**Streaming Processing**
- **Real-time**: Apache Kafka + PySpark Structured Streaming
- **Windowing**: Tumbling windows (5 min, 15 min, 1 hour)
- **Backpressure**: Automatic rate limiting

**Volume Estimation per Agent**
| Agent | Typical Volume | Max Volume | Processing Time |
|-------|----------------|------------|-----------------|
| Extraction | 1GB - 10GB | 100GB | 5 - 30 min |
| EDA | 1GB - 10GB | 100GB | 10 - 60 min |
| Quality | 1GB - 10GB | 100GB | 5 - 30 min |
| RCA | 100MB - 5GB | 50GB | 5 - 45 min |
| Optimization | 1GB - 10GB | 100GB | 10 - 60 min |
| Validation | 1GB - 10GB | 100GB | 5 - 30 min |
| Observability | 100MB - 1GB | 10GB | 1 - 10 min |

### Latency Expectations per Stage

**End-to-End Latency Targets**
- **Small dataset** (< 1GB): < 15 minutes
- **Medium dataset** (1GB - 10GB): < 1 hour
- **Large dataset** (> 10GB): < 4 hours

**Per-Agent Latency Targets**
| Agent | P50 | P95 | P99 |
|-------|-----|-----|-----|
| Extraction | 5 min | 15 min | 30 min |
| EDA | 10 min | 30 min | 60 min |
| Quality | 5 min | 15 min | 30 min |
| RCA | 10 min | 30 min | 45 min |
| Optimization | 10 min | 30 min | 60 min |
| Validation | 5 min | 15 min | 30 min |
| Observability | 2 min | 5 min | 10 min |

**Latency Monitoring**
- Real-time latency tracking per agent
- SLO alerts when P95 exceeds target
- Latency trend analysis for capacity planning

### Data Transformation Points

**Transformation Locations**
1. **Extraction Agent**: Source format → Parquet
2. **EDA Agent**: Add profiling metadata
3. **Quality Agent**: Add quality scores and flags
4. **RCA Agent**: Add RCA annotations
5. **Optimization Agent**: Apply transformations (type conversion, normalization)
6. **Validation Agent**: Add validation results
7. **Observability Agent**: Add metrics and trends

**Transformation Pipeline**
```
Raw Data → Extraction → Parquet → EDA → Parquet + Metadata → Quality → 
Parquet + Quality Flags → RCA → Parquet + RCA Annotations → 
Optimization → Transformed Parquet → Validation → Validated Parquet → 
Observability → Parquet + Metrics
```

**Transformation Validation**
- Schema validation at each transformation point
- Data integrity checks (row count, checksum)
- Transformation audit trail (what changed, when, why)
