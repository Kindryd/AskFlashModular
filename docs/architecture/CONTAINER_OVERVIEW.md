# 🏗️ AskFlash Modular - Container Architecture Overview

## 📋 Architecture Summary

AskFlash Modular implements a **microservices architecture** using containerized services with a **shared PostgreSQL database**. This design provides clear separation of concerns while maintaining data consistency and avoiding the complexity of distributed transactions.

## 🎯 Design Principles

### 1. **Shared Database with Logical Ownership**
- Single PostgreSQL instance for all containers
- Each container owns specific tables (write access)
- Cross-service data access via APIs or read-only access
- Maintains ACID properties without distributed transactions

### 2. **Event-Driven Communication**
- **Synchronous**: HTTP APIs for real-time operations
- **Asynchronous**: Redis events for background processing
- **Decoupled**: Services communicate via well-defined contracts

### 3. **Container Responsibilities**
- Each container has a single, well-defined purpose
- Clear API boundaries for external communication
- Independent scaling and deployment capabilities

## 📦 Container Breakdown

### Frontend Service

#### `frontend.container` (Port 3000)
**Purpose**: Modern React-based user interface

**Responsibilities**:
- Single-page React application with Flash branding
- Real-time streaming chat interface with "thinking steps"
- Dark/light theme support and responsive design
- Company/General mode switching
- WebSocket connections for real-time updates
- Local storage for user preferences

**Technology Stack**:
- React 18 with modern hooks
- CSS custom properties for theming
- Fetch API with ReadableStream for streaming
- Markdown rendering with syntax highlighting
- TypeScript for type safety

**Legacy Features Preserved**:
- 🐄 Flash branding with #7ed321 green theme
- Claude-style thinking indicators during AI reasoning
- Dual mode support (Company/General)
- Persistent conversation history
- Source citations and confidence indicators

### Core Services

#### `conversation.container` (Port 8001)
**Purpose**: Chat session management and user interactions

**Responsibilities**:
- WebSocket connections for real-time chat
- Conversation persistence and history
- User query tracking and analytics
- Coordination with AI services

**Database Tables**:
- `conversation_histories` - Chat sessions
- `conversation_messages` - Individual messages  
- `frequent_queries` - User query patterns

#### `embedding.container` (Port 8002)
**Purpose**: Vector generation and semantic search

**Responsibilities**:
- Document indexing and embedding generation
- Semantic search across knowledge base
- Qdrant vector database management
- Content processing and chunking

**Database Tables**:
- `wikis` - Document sources and metadata
- `wiki_page_indexes` - Page-level indexing status

#### `ai-orchestrator.container` (Port 8003)
**Purpose**: AI provider management and routing

**Responsibilities**:
- AI provider selection and load balancing
- Request routing (OpenAI vs Local LLM)
- Response quality control and filtering
- AI model configuration management

**Database Tables**:
- `rulesets` - AI routing rules and configs
- `integrations` - AI provider configurations

### Supporting Services

#### `project-manager.container` (Port 8004)
**Purpose**: External integrations and notifications

**Responsibilities**:
- JIRA ticket creation
- Teams/Slack notifications
- External workflow triggers
- Integration status monitoring

**Database Access**: Read-only (via APIs)

#### `adaptive-engine.container` (Port 8005)
**Purpose**: User learning and behavior analysis

**Responsibilities**:
- User behavior pattern detection
- Conversation effectiveness analysis
- Personalization recommendations
- Learning insights generation

**Database Tables**:
- `user_habits` - User behavior patterns
- `learning_insights` - Generated recommendations

#### `local-llm.container` (Port 8006)
**Purpose**: Local model hosting

**Responsibilities**:
- Host local LLM models (Mistral, Llama)
- OpenAI-compatible API endpoints
- GPU-accelerated inference
- Privacy-focused AI processing

**Database Access**: None (stateless)

#### `analytics.container` (Port 8007)
**Purpose**: System monitoring and reporting

**Responsibilities**:
- Event collection from all services
- Performance metrics aggregation
- Usage reporting and insights
- System health monitoring

**Database Access**: Read-only + External storage (S3)

#### `gateway.container` (Port 8000)
**Purpose**: API gateway and routing

**Responsibilities**:
- Request routing to appropriate services
- Authentication and authorization
- Rate limiting and CORS handling
- Load balancing and failover

**Database Access**: None (stateless)

## 🔄 Communication Patterns

### Synchronous Communication (HTTP)

```
Frontend (3000) 
    ↓ 
Gateway Container (8000)
    ↓
┌─────────────────────────────────────┐
│  Conversation (8001) ←→ AI-Orch (8003)  │
│       ↓                    ↓         │
│  Embedding (8002) ←→ Local-LLM (8006) │
└─────────────────────────────────────┘
```

### Frontend-Backend Communication

```
React Frontend (3000)
    ↓ (HTTP + WebSocket)
Gateway (8000)
    ↓
Conversation Service (8001) ← Real-time chat
    ↓
AI Orchestrator (8003) ← AI processing
    ↓
Embedding Service (8002) ← Document search
```

### Asynchronous Communication (Redis Events)

```
All Containers → Redis Events → Analytics Container
     ↓
Adaptive Engine (listens to user behavior events)
     ↓  
Project Manager (listens to action triggers)
```

## 🗄️ Database Architecture

### Table Ownership Model

```sql
-- CONVERSATION.CONTAINER
conversation_histories, conversation_messages, frequent_queries

-- EMBEDDING.CONTAINER  
wikis, wiki_page_indexes

-- AI-ORCHESTRATOR.CONTAINER
rulesets, integrations

-- ADAPTIVE-ENGINE.CONTAINER
user_habits, learning_insights

-- SHARED (Read-only for most)
users
```

### Cross-Service Data Access

1. **Primary Pattern**: API calls between services
2. **Secondary Pattern**: Read-only database access with proper indexing
3. **Event Pattern**: Redis notifications for async updates

## 🚀 Deployment Architecture

### Development
```bash
docker-compose up -d
```

### Production Considerations
- **Kubernetes** deployment with pod scaling
- **External PostgreSQL** cluster with read replicas  
- **Redis Cluster** for high availability
- **Load balancers** for stateless services
- **Monitoring** with Prometheus/Grafana

## 📈 Scaling Strategy

### Horizontal Scaling
```bash
# Scale conversation handlers
docker-compose up --scale conversation=3

# Scale AI processing
docker-compose up --scale ai-orchestrator=2

# Scale embedding generation  
docker-compose up --scale embedding=2
```

### Vertical Scaling
- **Database**: Increase PostgreSQL resources
- **Vector Store**: Scale Qdrant cluster
- **AI Processing**: Add GPU resources to local-llm

## 🔧 Migration from Legacy

This architecture preserves key features from the legacy system:

**✅ Preserved**:
- Real-time streaming chat experience
- Vector-powered semantic search capabilities  
- Microsoft Teams and external integrations
- Multi-provider AI support with fallbacks
- Sophisticated conversation management

**🔄 Modernized**:
- Monolithic → Microservices architecture
- Single container → Independent scaling
- Hardcoded config → Database-driven rules
- Simple logging → Comprehensive analytics

**❌ Removed**:
- ALTO Protocol (failed optimization attempt)
- Overly complex prompt management
- Rigid pattern matching systems

## 🛠️ Development Workflow

1. **Individual Development**: Work on single containers
2. **Integration Testing**: Use docker-compose for full system testing
3. **Database Migration**: Use Alembic migrations per container
4. **API Versioning**: Independent versioning per service
5. **Documentation**: Maintain per-container README files

This architecture provides a solid foundation for long-term scalability while maintaining the sophisticated AI capabilities that made the legacy system valuable. 