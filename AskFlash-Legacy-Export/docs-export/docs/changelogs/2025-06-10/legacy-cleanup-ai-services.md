# Legacy Cleanup: AI Services and Dependencies
**Date:** 2025-06-10  
**Type:** Architecture Cleanup  
**Impact:** Low Risk - Removes unused/confusing legacy components

## Overview
Comprehensive cleanup of legacy AI services and unused dependencies to eliminate confusion and streamline the codebase. This cleanup was motivated by the legacy `ai.py` service causing confusion during development and the presence of unused external integrations.

## What Was Removed

### 🗑️ Legacy AI Service (`backend/app/services/ai.py`)
- **Reason**: Fully replaced by `StreamingAIService` and direct OpenAI integration
- **Usage Before**: Only used in Teams bot general mode and search endpoint
- **Replacement**: Teams bot now uses placeholder, search endpoint uses placeholder

### 🗑️ ALTO System (`backend/app/alto/`)
- **Reason**: Needs redesign, was causing confusion
- **Files Removed**: 
  - `alto_runner.py`, `enhanced_alto_runner.py`
  - `prompt_template.py`, `alto_codec.py`
  - `context_manager.py`, `schemas.py`
  - `intent_parser.py`, `vector_integration.py`
  - `legacy_comparison.py`, `alto_cache.py`
- **Note**: Will be reimplemented with cleaner design

### 🗑️ Legacy v1 API (`backend/app/api/v1/`)
- **Reason**: Deprecated, only used old AIService
- **Files Removed**: Entire `v1` directory structure
- **Replacement**: All functionality moved to `api_v1` endpoints

### 🗑️ Notion Integration Dependencies
- **Reason**: Not currently being used
- **Changes**:
  - Removed `notion-client==2.2.1` from all requirements files
  - Made import optional in `documentation.py`
  - Updated default ruleset to mark as disabled
  - Kept model fields for future reactivation

### 🗑️ Dynatrace Integration Dependencies  
- **Reason**: Not currently being used
- **Changes**:
  - Commented out `dynatrace-api-client` from requirements
  - Updated monitoring service placeholders to be clearer
  - Updated default ruleset to mark as disabled

## What Was Updated

### ✅ StreamingAIService Made Standalone
- **Before**: `class StreamingAIService(AIService)`
- **After**: `class StreamingAIService:` (standalone)
- **Changes**:
  - Removed inheritance from `AIService`
  - Updated constructor to initialize OpenAI client directly
  - All functionality preserved, just cleaner architecture

### ✅ Teams Bot Updated
- **Before**: Used `AIService` for general mode
- **After**: Uses placeholder message for general mode
- **Placeholder**: `"🌐 Teams general mode is currently under development..."`
- **Company Mode**: Still works via `StreamingAIService`

### ✅ Search Endpoint Updated  
- **Before**: Used `AIService` for response generation
- **After**: Uses placeholder response
- **Placeholder**: `"🔍 Search endpoint is under development..."`
- **Documentation Search**: Still works, just no AI response

### ✅ External Dependencies Made Optional
- **Azure DevOps**: Made import optional with fallbacks
- **GitHub**: Made import optional with fallbacks  
- **Notion**: Made import optional with fallbacks
- **Benefit**: Reduced dependency installation requirements

## Current AI Service Architecture

### **Active Services:**
1. **StreamingAIService** (`streaming_ai.py`)
   - **Usage**: Company mode (main chat endpoint + streaming)
   - **Features**: Dual-AI architecture, enhanced reasoning, quality analysis
   - **Status**: ✅ Fully functional, standalone

2. **Direct OpenAI Client** (`chat.py/_process_general_mode_pure`)
   - **Usage**: General mode (main chat endpoint)
   - **Features**: Pure ChatGPT-like experience
   - **Status**: ✅ Fully functional

3. **DocumentationService** (`documentation.py`)
   - **Usage**: Base class for `EnhancedDocumentationService`
   - **Status**: ✅ Still needed (inheritance relationship)

### **Placeholder Services:**
1. **Teams Bot General Mode**: Shows development message
2. **Search Endpoint AI Response**: Shows development message  
3. **Monitoring Service**: Placeholder for Dynatrace integration

## Benefits Achieved

### 🎯 Reduced Confusion
- Eliminated legacy `AIService` that was causing development confusion
- Clear separation between active and placeholder components
- Removed unused ALTO system causing complexity

### 🚀 Simplified Dependencies
- Reduced required external packages
- Optional imports prevent installation failures
- Cleaner requirements files

### 🏗️ Cleaner Architecture
- `StreamingAIService` no longer has unnecessary inheritance
- Removed dead code and legacy APIs
- Clear service boundaries

### 📈 Maintainability
- Less code to maintain
- Clear documentation of what's active vs placeholder
- Easier to understand current state

## Files Modified

### Services Updated:
- `app/services/streaming_ai.py` - Removed AIService inheritance
- `app/services/teams_bot.py` - Added placeholder for general mode
- `app/services/documentation.py` - Made external imports optional
- `app/services/monitoring.py` - Updated placeholder messages

### API Endpoints Updated:
- `app/api/api_v1/endpoints/chat.py` - Removed AIService import
- `app/api/api_v1/endpoints/search.py` - Added placeholder AI response

### Configuration Updated:
- `requirements-base.txt` - Commented out unused dependencies, fixed pydantic-settings version compatibility  
- `requirements-features.txt` - Teams bot specific dependencies
- `pyproject.toml` - Commented out unused dependencies, fixed pydantic-settings version compatibility
- `scripts/insert_default_ruleset.py` - Marked integrations as disabled

### Files Removed:
- `requirements.txt` - Only used by standalone Dockerfile (not docker-compose split approach)
- `requirements-complete.txt` - Not referenced anywhere, redundant content

## Testing Impact
- Core functionality unchanged for company mode
- General mode still works via direct OpenAI integration
- Teams bot company mode still works
- Search endpoint documentation search still works
- Only placeholders affected: Teams general mode, Search AI responses

## Migration Notes
- No breaking changes for end users
- All active AI functionality preserved
- Teams bot may show different message for general mode
- Search endpoint shows placeholder instead of AI-generated responses

## Issues Fixed

### ✅ Pydantic-Settings Version Compatibility
- **Problem**: `pydantic-settings==2.2.1` was incompatible with `pydantic==2.6.3`
- **Error**: `cannot import name 'Secret' from 'pydantic'`
- **Solution**: Updated to `pydantic-settings>=2.6.0,<3.0.0` for compatibility
- **Impact**: Resolves import errors and ensures stable dependency management

## Future Work
- ALTO system will be redesigned and reimplemented
- Notion integration can be reactivated when needed
- Dynatrace integration can be implemented when required
- Teams bot general mode needs proper implementation
- Search endpoint AI responses need proper implementation

---
**Technical Debt Reduced**: Removed ~2,000+ lines of unused/legacy code  
**Dependency Complexity**: Reduced from required to optional external integrations  
**Architecture Clarity**: Clear separation between active and placeholder components  
**Compatibility Issues**: Fixed pydantic-settings version mismatch 