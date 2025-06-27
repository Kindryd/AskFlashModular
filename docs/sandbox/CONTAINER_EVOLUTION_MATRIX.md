# 📦 Container Evolution Matrix - Current → MCP Architecture

This document provides a detailed mapping of how existing containers evolve and which new containers need to be created for the MCP multi-agent architecture.

---

## 🔄 Container Transformation Map

### **Current Working Containers → MCP Evolution**

| Current Container | New Role | Port | Evolution Type | MCP Integration |
|-------------------|----------|------|----------------|-----------------|
| `frontend.container` | **Enhanced Frontend** | 3000 | 🔄 **EVOLVE** | Add MCP task visualization, agent activity monitoring |
| `conversation.container` | **Conversation Manager** | 8001 | 🔄 **EVOLVE** | Integrate with MCP for task-based streaming |
| `embedding.container` | **Embedding Agent** | 8002 | 🔄 **EVOLVE** | Become MCP task consumer via RabbitMQ |
| `ai-orchestrator.container` | **MCP Master Control** | 8003 | 🔄 **TRANSFORM** | Full transformation into task DAG coordinator |
| `gateway.container` | **Enhanced Gateway** | 8000 | 🔄 **EVOLVE** | Add MCP routing, WebSocket proxy, agent load balancing |

### **Scaffolded Containers → MCP Completion**

| Scaffolded Container | New Role | Port | Implementation Type | MCP Integration |
|---------------------|----------|------|---------------------|-----------------|
| `project-manager.container` | **Integration Manager** | 8004 | ✅ **COMPLETE** | MCP event-driven JIRA/Teams integration |
| `adaptive-engine.container` | **Learning Engine** | 8005 | ✅ **COMPLETE** | MCP task pattern analysis and optimization |
| `local-llm.container` | **Local AI Provider** | 8006 | ✅ **COMPLETE** | MCP-compatible local LLM hosting |
| `analytics.container` | **System Monitor** | 8007 | ✅ **COMPLETE** | MCP task analytics and performance tracking |

### **New Agent Containers → MCP Agents**

| New Container | Role | Port | Creation Type | MCP Integration |
|---------------|------|------|---------------|-----------------|
| `preprocessor.container` | **Intent Strategist** | 8009 | 🆕 **CREATE** | RabbitMQ `intent.task` consumer |
| `executor.container` | **Research Specialist** | 8010 | 🆕 **CREATE** | RabbitMQ `executor.task` consumer |
| `moderator.container` | **Quality Assurance** | 8011 | 🆕 **CREATE** | RabbitMQ `moderator.task` consumer |
| `web-search.container` | **External Augmentation** | 8012 | 🆕 **CREATE** | RabbitMQ `websearch.task` consumer |

---

## 📊 Detailed Evolution Plans

### **🔄 EVOLVE: frontend.container**
```typescript
// Current State: Basic React streaming chat
// Target State: MCP-aware UI with agent visualization

NEW FEATURES TO ADD:
├── TaskProgressTracker.tsx - Real-time DAG stage visualization
├── AgentActivityPanel.tsx - Show active agents and their status
├── ReasoningStepsDisplay.tsx - Enhanced thinking steps with agent context
├── TaskHistoryViewer.tsx - Browse past MCP executions
├── AdvancedSettingsPanel.tsx - User DAG preferences
└── WebSocketManager.ts - Real-time MCP event handling

INTEGRATION POINTS:
- WebSocket connection to MCP progress streams
- Agent status monitoring via Redis pub/sub
- Task DAG visualization with D3.js or similar
- Real-time progress updates for each DAG stage
```

### **🔄 EVOLVE: conversation.container**
```python
# Current State: StreamingAIService with direct AI calls
# Target State: MCP-integrated task-based streaming

SERVICES TO MODIFY:
├── streaming_ai.py → mcp_streaming_service.py
│   ├── emit_task_to_mcp()
│   ├── poll_task_progress()
│   ├── stream_agent_updates()
│   └── maintain_legacy_compatibility()
├── conversation_manager.py (enhance)
│   ├── track_mcp_task_ids()
│   ├── link_conversations_to_tasks()
│   └── provide_task_history()

API ENDPOINTS TO ADD:
- POST /conversations/{id}/mcp-task - Create MCP task for conversation
- GET /conversations/{id}/task-status - Get current task progress
- GET /conversations/{id}/agent-activity - Show active agents
```

### **🔄 EVOLVE: embedding.container**
```python
# Current State: Direct API endpoints for vector operations
# Target State: RabbitMQ consumer + API endpoints

SERVICES TO ADD:
├── mcp_task_consumer.py
│   ├── consume_embedding_tasks()
│   ├── process_vector_search()
│   ├── emit_completion_events()
│   └── handle_task_retries()
├── enhanced_search.py (upgrade)
│   ├── task_aware_search()
│   ├── context_enhanced_results()
│   └── semantic_expansion()

INTEGRATION POINTS:
- RabbitMQ consumer for 'embedding.task' queue
- Redis pub/sub for completion events
- Maintain existing API endpoints for direct calls
```

### **🔄 TRANSFORM: ai-orchestrator.container → mcp.container**
```python
# Current State: Basic AI routing and quality analysis
# Target State: Full Master Control Program with DAG coordination

COMPLETE RESTRUCTURE:
├── services/
│   ├── task_coordinator.py - Core DAG execution engine
│   ├── message_broker.py - RabbitMQ/Redis integration
│   ├── state_manager.py - Task state and context management
│   ├── agent_monitor.py - Agent health and performance tracking
│   └── dag_optimizer.py - Dynamic DAG optimization
├── models/
│   ├── task_dag.py - Task DAG data models
│   ├── agent_status.py - Agent monitoring models
│   └── task_history.py - Execution history models
├── api/
│   ├── task_routes.py - Task management endpoints
│   ├── agent_routes.py - Agent monitoring endpoints
│   └── analytics_routes.py - Performance analytics

PRESERVE FROM CURRENT:
- Information Quality Enhancement (quality_analyzer.py)
- Intent AI System (intent_ai.py)
- Database connection patterns
- Flash AI branding and configuration
```

---

## 🆕 New Container Specifications

### **preprocessor.container (Port 8009)**
```python
CONTAINER STRUCTURE:
├── services/
│   ├── intent_analyzer.py - GPT-3.5 query analysis
│   ├── query_expander.py - Sub-question generation
│   ├── strategy_planner.py - DAG modification logic
│   └── complexity_classifier.py - Query complexity assessment
├── models/
│   ├── intent_analysis.py - Analysis result models
│   └── planning_strategy.py - Planning data models
├── core/
│   ├── rabbitmq_consumer.py - 'intent.task' queue consumer
│   ├── redis_publisher.py - Progress event emission
│   └── config.py - GPT-3.5 and service configuration

INTEGRATION:
- Consumes: RabbitMQ 'intent.task' queue
- Emits: Redis 'ai:plan:ready' events
- Updates: Task DAG in Redis with refined plan
```

### **executor.container (Port 8010)**
```python
CONTAINER STRUCTURE:
├── services/
│   ├── reasoning_engine.py - GPT-4o powered reasoning
│   ├── document_synthesizer.py - Context-aware analysis
│   ├── evidence_evaluator.py - Source credibility assessment
│   └── response_generator.py - Final response creation
├── models/
│   ├── reasoning_context.py - Context management models
│   └── execution_result.py - Response and metadata models
├── core/
│   ├── rabbitmq_consumer.py - 'executor.task' queue consumer
│   ├── redis_publisher.py - Execution progress events
│   └── config.py - GPT-4o and reasoning configuration

INTEGRATION:
- Consumes: RabbitMQ 'executor.task' queue
- Emits: Redis 'ai:execution:complete' events
- Can request: Web search via 'websearch.task' queue
```

### **moderator.container (Port 8011)**
```python
CONTAINER STRUCTURE:
├── services/
│   ├── response_moderator.py - Quality assessment
│   ├── confidence_scorer.py - Response confidence analysis
│   ├── tone_analyzer.py - Appropriate tone validation
│   └── improvement_suggester.py - Response enhancement
├── models/
│   ├── moderation_result.py - Assessment result models
│   └── confidence_metrics.py - Scoring data models
├── core/
│   ├── rabbitmq_consumer.py - 'moderator.task' queue consumer
│   ├── redis_publisher.py - Moderation result events
│   └── config.py - Moderation criteria configuration

INTEGRATION:
- Consumes: RabbitMQ 'moderator.task' queue
- Emits: Redis 'ai:moderation:pass' or 'ai:moderation:retry' events
- Can trigger: Re-execution if confidence too low
```

### **web-search.container (Port 8012)**
```python
CONTAINER STRUCTURE:
├── services/
│   ├── web_searcher.py - DuckDuckGo/SerpAPI integration
│   ├── content_analyzer.py - LLM-powered content analysis
│   ├── fact_verifier.py - Information verification
│   └── context_synthesizer.py - Web context creation
├── models/
│   ├── search_result.py - Search result models
│   └── verification_result.py - Fact-check models
├── core/
│   ├── rabbitmq_consumer.py - 'websearch.task' queue consumer
│   ├── redis_publisher.py - Search completion events
│   └── config.py - Search API and LLM configuration

INTEGRATION:
- Consumes: RabbitMQ 'websearch.task' queue
- Emits: Redis 'ai:websearch:complete' events
- Updates: Task context with verified web information
```

---

## 🔗 Communication Flow Evolution

### **Current State: Direct API Calls**
```
Frontend → Gateway → Conversation → AI-Orchestrator → Embedding
```

### **Target State: MCP Task Coordination**
```
Frontend → Gateway → Conversation → MCP
                                    ↓
                        [Creates Task DAG]
                                    ↓
                    RabbitMQ Task Distribution
                    ↓         ↓         ↓         ↓
            Preprocessor  Embedding  Executor  Moderator
                    ↓         ↓         ↓         ↓
                Redis Progress Events (Real-time to Frontend)
                                    ↓
                        MCP Orchestrates Next Stage
                                    ↓
                        Final Response Assembly
```

This evolution matrix ensures a clear understanding of how each container transforms while maintaining backward compatibility and adding powerful MCP capabilities. 