# 🐄 AskFlash Modular - Complete Project Context for ChatGPT

## 🎯 Project Overview

**AskFlash Modular** is a production-ready enterprise AI assistant platform that has been **migrated from a legacy monolithic architecture to modern microservices**. The system provides intelligent document search, conversation management, and AI-powered assistance for enterprise teams.

### Key Facts
- **Status**: 67% Complete (5/9 containers implemented and working)
- **Architecture**: Microservices with shared PostgreSQL database
- **Purpose**: Enterprise RAG (Retrieval-Augmented Generation) system
- **Branding**: 🐄 Flash AI with #7ed321 green theme
- **Recent Changes**: API restructured (removed `/api/v1/` prefix), company-mode only

## 🏗️ Current Architecture

### Container Services (9 Total)

| Container | Status | Port | Purpose | Tables Owned |
|-----------|--------|------|---------|--------------|
| **frontend.container** | ✅ Working | 3000 | React UI with streaming chat | _(stateless)_ |
| **conversation.container** | ✅ Working | 8001 | Chat sessions & messaging | `conversation_histories`, `conversation_messages` |
| **embedding.container** | ✅ Working | 8002 | Vector search & document indexing | `wikis`, `wiki_page_indexes` |
| **ai-orchestrator.container** | ✅ Working | 8003 | AI routing & quality analysis | `rulesets`, `integrations` |
| **gateway.container** | ✅ Working | 8000 | API gateway & routing | _(stateless)_ |
| **project-manager.container** | 🟡 Scaffolded | 8004 | External integrations (JIRA/Teams) | _(reads only)_ |
| **adaptive-engine.container** | 🟡 Scaffolded | 8005 | User learning & behavior analysis | `user_habits`, `learning_insights` |
| **local-llm.container** | 🟡 Scaffolded | 8006 | Local model hosting | _(stateless)_ |
| **analytics.container** | 🟡 Scaffolded | 8007 | Logging & metrics | _(external storage)_ |

### Infrastructure Services
- **PostgreSQL** (5432) - Shared database with logical table ownership
- **Redis** (6379) - Event messaging and caching  
- **Qdrant** (6333) - Vector database for embeddings
- **Adminer** (8080) - Database management UI

## 🚀 Implementation Status

### ✅ WORKING CONTAINERS (Production Ready)

#### Frontend Container (`frontend.container/`)
- **Technology**: React 18 + TypeScript + Vite
- **Features**: 
  - 🐄 Flash AI branding with #7ed321 theme
  - **Company-mode only** (general mode removed)
  - Streaming chat with Claude-style thinking indicators
  - Dark/light theme support
  - Responsive design
  - **Clean API calls** (no `/api/v1/` prefix)
- **Status**: Fully functional with updated API structure

#### Conversation Container (`conversation.container/`)
- **Key Services**:
  - `ConversationManager` - Complete conversation lifecycle
  - `StreamingAIService` - Step-by-step AI reasoning with streaming
- **Database Models**: 
  - `conversation_histories` table with UUIDs
  - `conversation_messages` table with metadata support
  - **Fixed**: Renamed `metadata` → `conv_metadata`/`msg_metadata` (SQLAlchemy reserved word issue)
- **API Endpoints**:
  - `GET /conversations/active` - Get/create active conversation
  - `POST /conversations/new` - Create new conversation  
  - `POST /chat/stream` - Streaming chat with thinking steps
- **Status**: All routes working, database models aligned with PostgreSQL schema

#### AI Orchestrator Container (`ai-orchestrator.container/`)
- **Production Systems**:
  - **Information Quality Enhancement** - Conflict detection, authority scoring
  - **Intent AI System** - GPT-3.5 conversation analysis
- **Core Capabilities**:
  - AI provider routing and load balancing
  - Quality analysis with confidence scoring
  - Search strategy generation
- **Status**: Core AI routing functionality operational

#### Embedding Container (`embedding.container/`)
- **Features**: 
  - Document indexing and vector generation
  - Semantic search with Qdrant integration
  - Alias discovery system
  - Enhanced search capabilities
- **Status**: Vector operations and document processing working

#### Gateway Container (`gateway.container/`)
- **Critical Fix Applied**: Removed `/api/v1/` prefix from all routes
- **Current Routes**:
  - `/conversations/active` → conversation container
  - `/conversations/new` → conversation container
  - `/chat/stream` → conversation container
- **Status**: Properly routing requests to conversation container

### 🟡 SCAFFOLDED CONTAINERS (Ready for Implementation)

The remaining 4 containers have basic structure and READMEs but need full implementation:
- `project-manager.container` - JIRA/Teams integrations
- `adaptive-engine.container` - User learning analytics  
- `local-llm.container` - Local model hosting
- `analytics.container` - System monitoring

## 🔧 Recent Critical Fixes

### API Structure Overhaul
**Problem**: Frontend getting 404 errors on all API calls
**Root Cause**: Multiple issues layered together
**Solution**: Complete API restructuring

1. **Removed `/api/v1/` prefix** from all endpoints for cleaner naming
2. **SQLAlchemy Reserved Word Fix**: 
   - Renamed `metadata` columns to `conv_metadata`/`msg_metadata`
   - This was preventing route registration entirely
3. **Database Model Alignment**: Updated to match actual PostgreSQL UUID schema
4. **Container Rebuilds**: Multiple `--no-cache` rebuilds required
5. **Company-Mode Only**: Removed general/company toggle throughout system

### Working API Structure (Current)
```
Frontend (localhost:3000) 
    ↓ 
Gateway (localhost:8000)
    ↓ [Clean Routes - No /api/v1/]
    ├── /conversations/active → Conversation Container (8001)
    ├── /conversations/new → Conversation Container (8001)  
    └── /chat/stream → Conversation Container (8001)
```

## 📊 Database Schema

### PostgreSQL Tables (Current)
```sql
-- CONVERSATION CONTAINER OWNERSHIP
conversation_histories (
    id UUID PRIMARY KEY,
    user_id VARCHAR,
    mode VARCHAR DEFAULT 'company',
    conv_metadata JSONB,  -- FIXED: was 'metadata'
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

conversation_messages (
    id UUID PRIMARY KEY,
    conversation_id UUID REFERENCES conversation_histories(id),
    role VARCHAR,
    content TEXT,
    msg_metadata JSONB,  -- FIXED: was 'metadata'  
    thinking_steps JSONB,
    sources JSONB,
    confidence FLOAT,
    created_at TIMESTAMP
);

-- EMBEDDING CONTAINER OWNERSHIP  
wikis (...);
wiki_page_indexes (...);

-- AI ORCHESTRATOR OWNERSHIP
rulesets (...);
integrations (...);
```

## 🔄 Communication Patterns

### Primary Data Flow
```
User Input → Frontend → Gateway → Conversation Container
                                      ↓
                              AI Orchestrator (quality analysis)
                                      ↓  
                              Embedding Container (document search)
                                      ↓
                              Streaming Response → Frontend
```

### Event-Driven (Redis)
- All containers emit analytics events
- Real-time notifications  
- Background processing triggers

## 🛠️ Development Setup

### Quick Start (Current Working)
```bash
# 1. Start infrastructure
docker-compose up postgres redis qdrant -d

# 2. Build working containers (may need --no-cache)
docker-compose build --no-cache gateway conversation frontend

# 3. Start working services
docker-compose up gateway conversation frontend -d

# 4. Test endpoints
curl http://localhost:8000/conversations/active  # Should work
curl http://localhost:8001/conversations/active  # Direct container access
```

### Verified Working URLs
- **Frontend**: http://localhost:3000 (React app loads)
- **Gateway Health**: http://localhost:8000/health
- **Conversation Direct**: http://localhost:8001/conversations/active
- **Gateway Routed**: http://localhost:8000/conversations/active

## 🎨 Design System

### Flash AI Branding
- **Primary Color**: #7ed321 (Flash Green)
- **Emoji**: 🐄 (Cow - Flash mascot)
- **Tagline**: "Making enterprise knowledge easier"
- **Theme**: Dark/light mode support
- **Typography**: System fonts with good readability

### UI/UX Patterns
- **Streaming Chat**: Claude-style thinking indicators
- **Company Mode Only**: Removed general/company toggle
- **Responsive Design**: Mobile-first approach
- **Accessibility**: WCAG compliant color contrast

## 🚧 Known Issues & Limitations

### Currently Working
- ✅ Frontend React app loads and renders correctly
- ✅ Gateway routes properly register and forward requests
- ✅ Conversation container API endpoints respond
- ✅ Database connections and models working
- ✅ Clean API structure (no `/api/v1/` prefix)

### Needs Implementation
- 🟡 Full chat streaming integration (frontend + backend)
- 🟡 Document search integration (embedding container)
- 🟡 Complete AI orchestration pipeline
- 🟡 Authentication/authorization system
- 🟡 Production deployment configuration

### Architecture Decisions Needed
- Local LLM vs Cloud AI provider strategy
- User authentication approach (JWT, OAuth, etc.)
- Real-time features implementation (WebSocket vs SSE)
- Monitoring and alerting strategy
- Backup and disaster recovery

## 📋 Development Standards

### Code Organization
- Each container follows FastAPI + async patterns
- Shared database with logical ownership
- Environment-based configuration
- Docker Compose for development
- Kubernetes-ready for production

### API Design
- RESTful endpoints where appropriate
- Streaming endpoints for real-time features  
- Consistent error handling and responses
- OpenAPI documentation auto-generated

### Database Patterns
- UUID primary keys throughout
- JSONB for flexible metadata storage
- Timestamp tracking for audit trails
- Foreign key constraints for data integrity

## 🎯 Next Steps for ChatGPT

This project is at a critical juncture with the **core infrastructure working** but needing strategic decisions about:

1. **Authentication Architecture** - How to implement user management
2. **AI Provider Strategy** - Balance between local LLMs and cloud APIs
3. **Real-time Features** - WebSocket vs Server-Sent Events for streaming
4. **Document Management** - How to handle large-scale document ingestion
5. **Production Deployment** - Kubernetes vs Docker Swarm vs managed services

The foundation is solid with working containers, clean APIs, and proper database schema. Ready for architectural guidance and feature implementation planning. 