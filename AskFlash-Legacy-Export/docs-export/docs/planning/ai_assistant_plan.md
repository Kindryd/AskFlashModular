# AI Assistant Integration Plan for Internal Application

This document outlines the steps to implement a company-aware assistant using open-source tools within our existing FastAPI backend that uses PostgreSQL, SQLAlchemy, and Python.

## 1. Vector Storage Setup
- Use Qdrant as the vector database
- Deploy via Docker container
- Configure collections for each data source:
  - Phase 1: Documentation (Azure DevOps Wiki)
  - Phase 2: Codebase (via tree-sitter)
  - Phase 3: Dynatrace logs

## 2. Embedding Strategy
- Use `sentence-transformers` for generating embeddings (e.g., `all-MiniLM-L6-v2` or `bge-base-en`)
- Process wiki content on-demand using existing `AzureDevOpsClient` and `DocumentationService`
- Chunk content appropriately for wiki documentation
- Embed text and upsert into Qdrant with metadata linking back to `WikiIndex` and `WikiPage` models

## 3. Data Ingestion
### Phase 1: Wiki Integration
- Leverage existing `AzureDevOpsClient` for content fetching
- Use current `DocumentationService` for content processing
- Process and chunk wiki content on-demand
- Store embeddings with metadata in Qdrant
- Maintain existing `WikiIndex` and `WikiPage` models for structure

### Future Phases
- **Codebase**: Extract meaningful snippets using `tree-sitter` or AST tools
- **Dynatrace Logs**: Connect via Dynatrace API and preprocess logs/errors

## 4. Retrieval-Augmented Generation (RAG)
- Extend existing `AIService` to use vector search
- Use LangChain or LlamaIndex for semantic search over Qdrant
- Integrate with current `SearchService` and `Ruleset` system
- Format and forward results to GPT-4 (via OpenAI API)
- Maintain existing response guidelines and context rules

## 5. Backend API Integration
- Extend current FastAPI service to:
  - Add vector store management endpoints
  - Enhance existing search endpoint with vector search
  - Maintain current authentication and authorization
  - Support embedding management
- Update `Ruleset` model to include:
  - Vector store configuration
  - Embedding model settings
  - Collection management settings

## 6. Implementation Phases

### Phase 1: Wiki Integration
1. Set up Qdrant container
2. Implement `VectorStoreService`
3. Modify `DocumentationService` for on-demand content processing
4. Update `SearchService` to use vector search
5. Extend `AIService` for RAG
6. Update `Ruleset` model

### Phase 2: Infrastructure
1. Add embedding pipeline
2. Implement collection management
3. Add embedding refresh mechanisms
4. Update documentation and architecture

### Phase 3: Future Integrations
1. Codebase integration
2. Dynatrace integration
3. Additional data sources

## 7. Deployment
- Dockerize components:
  - Vector DB (Qdrant)
  - Embedding pipeline
  - Existing FastAPI service
- Use Docker Compose for local development
- Document deployment process

## 8. Optional Enhancements
- Add user memory with Redis
- Implement document auto-refresh pipelines
- Add caching layer for frequently accessed content
- Enhance frontend with real-time search capabilities

## Summary
This architecture extends our existing system to provide a ChatGPT4-level assistant with real-time, context-aware company knowledge, using fully open-source infrastructure where possible. The phased approach ensures we can deliver value quickly while maintaining extensibility for future features.

## Integration with Existing Architecture
- Maintains current layered architecture pattern
- Extends existing services without breaking changes
- Preserves current authentication and authorization
- Supports future integration with codebase and Dynatrace
- Follows established naming conventions and code organization

## Documentation Updates
- Update `ARCHITECTURE.md` with vector store integration
- Update `askflash-codebase.mdc` with new components
- Document API changes and new endpoints
- Maintain clear separation of concerns