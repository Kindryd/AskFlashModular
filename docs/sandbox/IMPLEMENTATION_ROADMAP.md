# 🚀 AskFlash Modular → MCP Architecture Implementation Roadmap

This document provides a comprehensive, step-by-step plan to evolve the current AskFlash Modular project (67% complete) into the proposed MCP (Master Control Program) multi-agent architecture while preserving all working functionality.

---

## 📊 Current State Analysis

### ✅ **Working Foundation (67% Complete)**
- **frontend.container** - React UI with streaming chat (Port 3000)
- **conversation.container** - Chat sessions & messaging (Port 8001) 
- **embedding.container** - Vector search & document indexing (Port 8002)
- **ai-orchestrator.container** - AI routing & quality analysis (Port 8003)
- **gateway.container** - API gateway & routing (Port 8000)
- **Infrastructure** - PostgreSQL, Redis, Qdrant, Adminer all working
- **Clean API** - No `/api/v1/` prefix, company-mode only

### 🟡 **Scaffolded Containers (Need Implementation)**
- `project-manager.container` (Port 8004)
- `adaptive-engine.container` (Port 8005) 
- `local-llm.container` (Port 8006)
- `analytics.container` (Port 8007)

### 🎯 **Target MCP Architecture**
- Transform `ai-orchestrator` → `mcp.container` (Master Control Program)
- Add new agent containers: `preprocessor`, `executor`, `moderator`, `web-search`
- Implement task DAG coordination with Redis + RabbitMQ
- Multi-stage AI reasoning with real-time progress tracking

---

## 🏗️ Implementation Plan

## **Phase 1: Infrastructure Enhancement (Week 1)**
*Extend current working infrastructure to support MCP architecture*

### **Step 1.1: Add RabbitMQ to Infrastructure** ⏱️ 2 hours
**Goal**: Add RabbitMQ messaging broker to support task dispatch

```bash
# Update docker-compose.yml
```
- Add RabbitMQ service with management plugin
- Configure exchanges and queues per messaging schema
- Add RabbitMQ to health checks
- Update environment variables

**Deliverables**:
- ✅ RabbitMQ running on port 5672 (management: 15672)
- ✅ Predefined queues: `intent.task`, `embedding.task`, `executor.task`, `moderator.task`, `websearch.task`
- ✅ Health check integration

### **Step 1.2: Enhanced Redis Configuration** ⏱️ 1 hour
**Goal**: Configure Redis for advanced messaging patterns

- Enable Redis streams and pub/sub
- Configure Redis key naming conventions
- Set up TTL policies for task data
- Add Redis monitoring/debugging tools

**Deliverables**:
- ✅ Redis configured for streams, pub/sub, and KV storage
- ✅ Key naming conventions implemented
- ✅ TTL policies for task cleanup

### **Step 1.3: Database Schema Evolution** ⏱️ 3 hours
**Goal**: Extend PostgreSQL schema for MCP task management

```sql
-- New tables for MCP
CREATE TABLE task_histories (
    id UUID PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    query TEXT NOT NULL,
    plan JSONB NOT NULL,
    status VARCHAR NOT NULL,
    current_stage VARCHAR,
    completed_stages JSONB,
    context TEXT,
    response JSONB,
    error TEXT,
    started_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE task_dag_templates (
    id UUID PRIMARY KEY,
    name VARCHAR NOT NULL,
    description TEXT,
    stages JSONB NOT NULL,
    conditions JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Deliverables**:
- ✅ MCP task tracking tables
- ✅ DAG template system
- ✅ Migration scripts and rollback procedures

---

## **Phase 2: MCP Core Implementation (Week 2)**
*Transform ai-orchestrator into the Master Control Program*

### **Step 2.1: Transform ai-orchestrator → mcp.container** ⏱️ 6 hours
**Goal**: Evolve existing orchestrator into full MCP with task DAG coordination

**Core Services to Implement**:
```python
# services/task_coordinator.py
class TaskCoordinator:
    - create_task_dag()
    - execute_dag_stage()
    - handle_stage_completion()
    - emit_progress_events()
    - manage_retries_and_failures()

# services/message_broker.py  
class MessageBroker:
    - publish_to_rabbitmq()
    - listen_redis_events()
    - route_task_messages()
    - handle_agent_responses()

# services/state_manager.py
class StateManager:
    - store_task_state_redis()
    - update_task_progress()
    - manage_context_buffer()
    - cleanup_expired_tasks()
```

**API Endpoints to Add**:
- `POST /tasks/create` - Create new task DAG
- `GET /tasks/{task_id}/status` - Get task progress
- `POST /tasks/{task_id}/abort` - Cancel task
- `GET /tasks/{task_id}/logs` - Get task execution logs

**Deliverables**:
- ✅ Full MCP container with DAG coordination
- ✅ Redis task state management
- ✅ RabbitMQ task dispatch system
- ✅ Real-time progress tracking
- ✅ Legacy compatibility maintained

### **Step 2.2: Update conversation.container Integration** ⏱️ 2 hours
**Goal**: Modify conversation container to use MCP for AI processing

- Update StreamingAIService to emit tasks to MCP
- Implement task-based streaming response handling
- Maintain existing conversation APIs for frontend compatibility
- Add task progress polling for real-time updates

**Deliverables**:
- ✅ Conversation container integrated with MCP
- ✅ Backward compatibility with existing frontend
- ✅ Enhanced streaming with task progress

---

## **Phase 3: Agent Container Implementation (Week 3)**
*Create specialized AI agent containers*

### **Step 3.1: preprocessor.container (Intent Strategist)** ⏱️ 4 hours
**Goal**: Create intelligent query analysis and planning agent

**Core Functionality**:
```python
# services/intent_analyzer.py
class IntentAnalyzer:
    - analyze_query_intent()
    - generate_sub_questions()
    - determine_search_strategy()
    - classify_complexity()
    - suggest_dag_modifications()
```

**Features**:
- GPT-3.5 powered intent analysis
- Query expansion and clarification
- Dynamic DAG planning based on query complexity
- RabbitMQ consumer for `intent.task` queue

**Deliverables**:
- ✅ Full preprocessor container (Port 8009)
- ✅ Intent analysis with GPT-3.5
- ✅ Dynamic DAG generation
- ✅ RabbitMQ integration

### **Step 3.2: executor.container (Research Specialist)** ⏱️ 5 hours
**Goal**: Create powerful reasoning agent with GPT-4o

**Core Functionality**:
```python
# services/reasoning_engine.py
class ReasoningEngine:
    - context_aware_reasoning()
    - document_synthesis()
    - evidence_evaluation()
    - response_generation()
    - request_additional_search()
```

**Features**:
- GPT-4o for complex reasoning
- Context-aware document analysis
- Evidence-based response generation
- ReAct reasoning pattern implementation
- Ability to request web search augmentation

**Deliverables**:
- ✅ Full executor container (Port 8010)
- ✅ GPT-4o integration
- ✅ Advanced reasoning capabilities
- ✅ Document synthesis and analysis

### **Step 3.3: moderator.container (Quality Assurance)** ⏱️ 3 hours
**Goal**: Create response validation and improvement agent

**Core Functionality**:
```python
# services/response_moderator.py
class ResponseModerator:
    - validate_response_quality()
    - check_factual_accuracy()
    - assess_tone_appropriateness()
    - suggest_improvements()
    - calculate_confidence_score()
```

**Features**:
- GPT-3.5/4o for quality assessment
- Confidence scoring algorithm
- Response improvement suggestions
- Escalation logic for low-confidence responses

**Deliverables**:
- ✅ Full moderator container (Port 8011)
- ✅ Quality assessment pipeline
- ✅ Confidence scoring system
- ✅ Response improvement logic

### **Step 3.4: web-search.container (External Augmentation)** ⏱️ 4 hours
**Goal**: Create web search and fact-checking agent

**Core Functionality**:
```python
# services/web_searcher.py
class WebSearcher:
    - perform_web_search()
    - extract_relevant_facts()
    - verify_information()
    - synthesize_web_context()
    - detect_outdated_info()
```

**Features**:
- DuckDuckGo/SerpAPI integration
- LLM-powered content analysis
- Fact verification against known sources
- Real-time information augmentation

**Deliverables**:
- ✅ Full web-search container (Port 8012)
- ✅ Web search API integration
- ✅ Content analysis and verification
- ✅ MCP integration for conditional search

---

## **Phase 4: Legacy Container Completion (Week 4)**
*Complete the original 4 scaffolded containers with MCP integration*

### **Step 4.1: Complete project-manager.container** ⏱️ 5 hours
**Goal**: Implement external integrations with MCP event listening

**Enhanced Features**:
- Listen to MCP task completion events
- Trigger JIRA ticket creation based on AI insights
- Send Teams notifications for important discoveries
- Integration with task DAG for automated workflows

**Deliverables**:
- ✅ Full project-manager implementation
- ✅ JIRA/Teams integration
- ✅ MCP event-driven triggers
- ✅ Automated workflow capabilities

### **Step 4.2: Complete adaptive-engine.container** ⏱️ 4 hours
**Goal**: Implement user learning with MCP task analytics

**Enhanced Features**:
- Analyze MCP task patterns for user behavior
- Learn from DAG execution success/failure rates
- Personalize task planning based on user history
- Generate learning insights from multi-agent interactions

**Deliverables**:
- ✅ Full adaptive-engine implementation
- ✅ MCP task pattern analysis
- ✅ Personalized DAG optimization
- ✅ User behavior learning

### **Step 4.3: Complete local-llm.container** ⏱️ 6 hours
**Goal**: Implement local LLM hosting with MCP integration

**Features**:
- Host Mistral/Llama models locally
- Provide OpenAI-compatible API
- Act as fallback for cloud AI failures
- Process sensitive queries locally

**Deliverables**:
- ✅ Local LLM hosting (Ollama/vLLM)
- ✅ OpenAI-compatible endpoints
- ✅ GPU acceleration support
- ✅ MCP integration for local processing

### **Step 4.4: Complete analytics.container** ⏱️ 3 hours
**Goal**: Implement comprehensive system monitoring

**Enhanced Features**:
- Monitor MCP task execution metrics
- Track agent performance across the DAG
- Generate system health reports
- Real-time alerting for system issues

**Deliverables**:
- ✅ Full analytics implementation
- ✅ MCP task monitoring
- ✅ Agent performance tracking
- ✅ Real-time system alerts

---

## **Phase 5: Frontend Enhancement & Integration (Week 5)**
*Enhance frontend to fully utilize MCP capabilities*

### **Step 5.1: MCP-Aware Frontend Features** ⏱️ 6 hours
**Goal**: Enhance React frontend to display MCP task progress

**New Features**:
```typescript
// Enhanced UI Components
- TaskProgressTracker: Real-time DAG stage visualization
- AgentActivityPanel: Show which agents are working
- ReasoningStepsDisplay: Claude-style thinking with agent context
- TaskHistoryViewer: Browse past MCP task executions
- AdvancedSettingsPanel: Configure DAG preferences
```

**Real-time Features**:
- WebSocket connection to MCP progress streams
- Agent activity indicators
- Task DAG visualization
- Performance metrics display

**Deliverables**:
- ✅ Enhanced React UI with MCP integration
- ✅ Real-time task progress visualization
- ✅ Agent activity monitoring
- ✅ Advanced user controls

### **Step 5.2: Gateway Enhancement** ⏱️ 2 hours
**Goal**: Update gateway for MCP routing and load balancing

- Add routes for MCP task management
- Implement intelligent load balancing across agents
- Add WebSocket proxy for real-time updates
- Enhanced health checking for agent containers

**Deliverables**:
- ✅ MCP-aware gateway routing
- ✅ Agent load balancing
- ✅ WebSocket proxy implementation
- ✅ Enhanced health monitoring

---

## **Phase 6: Testing, Optimization & Production Readiness (Week 6)**
*Comprehensive testing and performance optimization*

### **Step 6.1: Integration Testing** ⏱️ 8 hours
**Goal**: Comprehensive end-to-end testing of MCP architecture

**Test Scenarios**:
- Complete task DAG execution flows
- Agent failure and recovery scenarios
- High concurrency task processing
- Frontend real-time update accuracy
- Database consistency under load

### **Step 6.2: Performance Optimization** ⏱️ 6 hours
**Goal**: Optimize system performance for production workloads

- Redis connection pooling and optimization
- RabbitMQ queue tuning and partitioning
- Agent container resource optimization
- Database query optimization
- Caching strategy implementation

### **Step 6.3: Production Deployment Preparation** ⏱️ 4 hours
**Goal**: Prepare for production deployment

- Kubernetes deployment manifests
- Environment configuration management
- Monitoring and alerting setup
- Backup and disaster recovery procedures
- Security hardening and audit

---

## 📊 Success Metrics

### **Technical Metrics**
- ✅ All 12+ containers operational and communicating
- ✅ Sub-2 second task initialization time
- ✅ 99.5% task completion success rate
- ✅ Real-time frontend updates within 100ms
- ✅ Zero data loss during agent failures

### **Functional Metrics**
- ✅ Multi-agent collaboration producing higher quality responses
- ✅ User queries handled with visible reasoning steps
- ✅ System can handle 100+ concurrent tasks
- ✅ Intelligent task routing based on complexity
- ✅ Automated external integrations working

### **User Experience Metrics**
- ✅ Sub-3 second initial response time
- ✅ Real-time progress visibility
- ✅ Improved response quality vs single-agent system
- ✅ Seamless fallback for system failures
- ✅ Mobile-responsive performance maintained

---

## 🎯 Risk Mitigation

### **Technical Risks**
- **Message Broker Failures**: Implement Redis fallback for critical operations
- **Agent Container Crashes**: Automatic restart policies and task reassignment
- **Database Performance**: Connection pooling and read replicas
- **Network Partitions**: Circuit breaker patterns and graceful degradation

### **Integration Risks**
- **Legacy API Compatibility**: Maintain facade endpoints during transition
- **Data Migration**: Incremental migration with rollback procedures
- **Third-party Dependencies**: Fallback providers and offline capabilities

---

## 🚀 Post-Implementation Roadmap

### **Phase 7: Advanced Features (Future)**
- Multi-tenant architecture support
- Advanced ML-based task optimization
- Custom agent creation framework
- Enterprise SSO integration
- Advanced analytics and business intelligence

This roadmap provides a clear path from the current 67% complete system to a fully operational MCP multi-agent architecture while preserving all working functionality and ensuring production readiness. 