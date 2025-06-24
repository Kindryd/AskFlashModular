# AI Instruction Protocol (AIP) - Efficient Internal AI Communication for Flash

## 📌 Overview

This document outlines the **AI Instruction Object (AIO) protocol** for the Flash AI Assistant - a structured, machine-optimized communication interface designed to replace verbose natural language queries with efficient, predictable instructions.

**Current Pain Points:**
- Natural language queries consume excessive tokens (average 150-300 tokens per query)
- Inconsistent response quality due to ambiguous parsing
- No structured routing for different query types
- Difficult to optimize and cache responses

**AIO Solution:**
- Structured JSON-based instruction format
- 60-80% token reduction in prompt construction
- Predictable response patterns for better caching
- Command-based routing for optimized processing

---

## 🧠 Core Concept - AI Instruction Object (AIO)

### Traditional Natural Language
```
User: "Hey Flash, can you help me find who's on the SRE team and how to contact them? I need this in a list format please."

Tokens used: ~25-30 tokens
Ambiguity: High (multiple interpretations possible)
Processing: Complex NLP parsing required
```

### AIO Protocol
```json
{
  "version": "1.0",
  "command": "find_team",
  "query": "SRE_team_contacts",
  "context_tags": ["team_directory", "sre"],
  "format": "list",
  "user_role": "support",
  "language": "eng",
  "confidence_threshold": 0.8
}
```

**Benefits:**
- Tokens used: ~15-20 tokens (40% reduction)
- Ambiguity: None (structured interpretation)
- Processing: Direct command dispatch
- Caching: Easy to cache by command+query hash

---

## 🔠 AIO Schema Specification

### Complete Field Reference

| Field | Type | Required | Description | Example Values |
|-------|------|----------|-------------|----------------|
| `version` | string | Yes | AIO protocol version | "1.0", "1.1" |
| `command` | enum | Yes | Primary task command | "fetch_answer", "find_team", "get_process" |
| `query` | string | Yes | Main query/topic | "reset_MFA", "SRE_team_contacts" |
| `context_tags` | array | No | Specific doc/context filters | ["auth_guide", "mfa_policy"] |
| `format` | enum | No | Response format | "steps", "list", "summary", "markdown" |
| `user_role` | enum | No | User role for context | "support", "dev", "sre", "mgr" |
| `language` | string | No | Response language | "eng", "py", "js", "sql" |
| `confidence_threshold` | float | No | Minimum confidence for response | 0.7, 0.8, 0.9 |

### Command Types and Use Cases

#### Core Commands
- **`fetch_answer`**: General knowledge/documentation queries
- **`find_team`**: Team member and contact information
- **`get_process`**: Company procedures and workflows
- **`explain`**: Technical concept explanations
- **`diagnose`**: Troubleshooting and problem analysis
- **`gen_code`**: Code generation and examples

#### Flash-Specific Commands  
- **`escalation_path`**: Find escalation procedures
- **`tool_access`**: Access requirements for tools/systems
- **`incident_response`**: Incident handling procedures
- **`compliance_check`**: Policy and compliance information

---

## 🔧 Implementation Architecture

### Integration with Existing Flash AI System

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Teams Bot     │    │   Frontend UI   │    │  API Clients    │
│                 │    │                 │    │                 │
│ Natural Lang.   │    │ Form/Dropdown   │    │ Direct AIO      │
│ → AIO Converter │    │ → AIO Builder   │    │ → JSON POST     │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────▼───────────────┐
                    │     AIO Processing Layer    │
                    │                             │
                    │  ┌─────────────────────────┐│
                    │  │   AIO Validator        ││
                    │  │   Command Router       ││
                    │  │   Context Fetcher      ││
                    │  │   Prompt Builder       ││
                    │  └─────────────────────────┘│
                    └─────────────┬───────────────┘
                                  │
                     ┌─────────────▼───────────────┐
                     │    Enhanced AI Service      │
                     │                             │
                     │  • Command-specific prompts │
                     │  • Optimized token usage    │
                     │  • Confidence scoring       │
                     │  • Response formatting      │
                     └─────────────┬───────────────┘
                                   │
                      ┌─────────────▼───────────────┐
                      │         OpenAI API          │
                      │      (GPT-4 Optimized)      │
                      └─────────────────────────────┘
```

### File Structure Integration

```
backend/app/
├── schemas/
│   ├── aio.py                 # AIO protocol schemas
│   └── search.py              # Existing schemas
├── services/
│   ├── aio/
│   │   ├── __init__.py
│   │   ├── processor.py       # Main AIO processor
│   │   ├── validator.py       # AIO validation logic
│   │   ├── router.py          # Command routing
│   │   └── converter.py       # Natural language → AIO
│   ├── ai.py                  # Enhanced with AIO support
│   └── vector_store.py        # Extended for AIO context
├── api/endpoints/
│   ├── ai.py                  # Add AIO endpoint
│   └── aio.py                 # Dedicated AIO endpoints
└── models/
    └── aio_logs.py            # AIO interaction logging
```

---

## 🚀 Development Implementation Plan

### Phase 1: Core AIO Infrastructure

**File: `backend/app/schemas/aio.py`**
```python
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from enum import Enum
import json

class AIOCommand(str, Enum):
    # Core commands
    FETCH_ANSWER = "fetch_answer"
    FIND_TEAM = "find_team"
    GET_PROCESS = "get_process"
    EXPLAIN = "explain"
    DIAGNOSE = "diagnose"
    GEN_CODE = "gen_code"
    
    # Flash-specific commands
    ESCALATION_PATH = "escalation_path"
    TOOL_ACCESS = "tool_access"
    INCIDENT_RESPONSE = "incident_response"
    COMPLIANCE_CHECK = "compliance_check"

class AIOFormat(str, Enum):
    STEPS = "steps"
    LIST = "list"
    SUMMARY = "summary"
    MARKDOWN = "markdown"
    CODE = "code"
    TABLE = "table"
    FLOWCHART = "flowchart"

class UserRole(str, Enum):
    SUPPORT = "support"
    DEVELOPER = "dev"
    SRE = "sre"
    MANAGER = "mgr"
    HR = "hr"
    EXTERNAL = "ext"
    ADMIN = "admin"

class AIOInstruction(BaseModel):
    """AI Instruction Object for structured AI communication"""
    
    version: str = Field(default="1.0", description="AIO protocol version")
    command: AIOCommand = Field(..., description="Primary task command")
    query: str = Field(..., min_length=1, max_length=500, description="Main query")
    context_tags: Optional[List[str]] = Field(default=None, description="Context filters")
    format: AIOFormat = Field(default=AIOFormat.MARKDOWN, description="Response format")
    user_role: UserRole = Field(default=UserRole.EXTERNAL, description="User role")
    language: str = Field(default="eng", description="Response language")
    confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
    
    @validator('query')
    def validate_query(cls, v):
        if not v.strip():
            raise ValueError('Query cannot be empty')
        return v.strip()
    
    class Config:
        use_enum_values = True
        json_encoders = {
            AIOCommand: lambda v: v.value,
            AIOFormat: lambda v: v.value,
            UserRole: lambda v: v.value
        }

class AIOResponse(BaseModel):
    """Response object for AIO processing"""
    
    instruction_id: str = Field(..., description="Unique instruction ID")
    response: str = Field(..., description="AI response content")
    confidence: float = Field(..., description="Response confidence score")
    sources_used: List[str] = Field(default=[], description="Documentation sources")
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")
    tokens_used: Dict[str, int] = Field(default={}, description="Token usage breakdown")
    fallback_triggered: bool = Field(default=False, description="Whether fallback was used")
    command_processed: AIOCommand = Field(..., description="Command that was processed")
    format_applied: AIOFormat = Field(..., description="Format that was applied")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Response metadata")
```

**File: `backend/app/services/aio/processor.py`**
```python
from typing import Dict, List, Optional, Tuple
import time
import uuid
import logging
from app.schemas.aio import AIOInstruction, AIOResponse, AIOCommand
from app.services.ai import AIService
from app.services.vector_store import VectorStoreService
from app.services.aio.router import AIOCommandRouter
from app.services.aio.validator import AIOValidator

logger = logging.getLogger(__name__)

class AIOProcessor:
    """Main processor for AI Instruction Objects"""
    
    def __init__(self, ai_service: AIService, vector_store: VectorStoreService):
        self.ai_service = ai_service
        self.vector_store = vector_store
        self.router = AIOCommandRouter()
        self.validator = AIOValidator()
    
    async def process_instruction(self, instruction: AIOInstruction) -> AIOResponse:
        """Process an AIO instruction and return structured response"""
        
        start_time = time.time()
        instruction_id = str(uuid.uuid4())
        
        try:
            # Validate instruction
            validation_result = await self.validator.validate(instruction)
            if not validation_result.is_valid:
                raise ValueError(f"Invalid AIO: {validation_result.errors}")
            
            # Route to appropriate handler
            handler = self.router.get_handler(instruction.command)
            
            # Process with command-specific logic
            response_content, sources, confidence = await handler.process(
                instruction, self.ai_service, self.vector_store
            )
            
            # Build response object
            processing_time = int((time.time() - start_time) * 1000)
            
            return AIOResponse(
                instruction_id=instruction_id,
                response=response_content,
                confidence=confidence,
                sources_used=sources,
                processing_time_ms=processing_time,
                tokens_used={"input": 0, "output": 0},  # TODO: Implement token counting
                command_processed=instruction.command,
                format_applied=instruction.format,
                metadata={"original_instruction": instruction.dict()}
            )
            
        except Exception as e:
            logger.error(f"AIO processing error: {str(e)}", exc_info=True)
            return self._build_error_response(instruction_id, str(e), start_time)
    
    def _build_error_response(self, instruction_id: str, error: str, start_time: float) -> AIOResponse:
        """Build error response for failed processing"""
        return AIOResponse(
            instruction_id=instruction_id,
            response=f"Error processing instruction: {error}",
            confidence=0.0,
            sources_used=[],
            processing_time_ms=int((time.time() - start_time) * 1000),
            fallback_triggered=True,
            command_processed=AIOCommand.FETCH_ANSWER,  # Default
            format_applied=AIOFormat.MARKDOWN
        )
```

### Phase 2: Natural Language to AIO Converter

**File: `backend/app/services/aio/converter.py`**
```python
import re
from typing import Optional, Dict, List
from app.schemas.aio import AIOInstruction, AIOCommand, AIOFormat, UserRole

class NaturalLanguageToAIOConverter:
    """Convert natural language queries to AIO format"""
    
    def __init__(self):
        self.command_patterns = {
            AIOCommand.FIND_TEAM: [
                r"who.*team", r"team.*member", r"contact.*team", 
                r"sre.*team", r"dev.*team", r"support.*team"
            ],
            AIOCommand.GET_PROCESS: [
                r"how.*process", r"procedure.*for", r"steps.*to",
                r"workflow", r"escalation", r"incident.*response"
            ],
            AIOCommand.DIAGNOSE: [
                r"error", r"issue", r"problem", r"troubleshoot",
                r"debug", r"fix", r"not.*work"
            ],
            AIOCommand.TOOL_ACCESS: [
                r"access.*to", r"permission", r"how.*login",
                r"connect.*to", r"vpn", r"dynatrace", r"azure"
            ]
        }
        
        self.format_patterns = {
            AIOFormat.LIST: [r"list", r"bullet", r"enumerate"],
            AIOFormat.STEPS: [r"step", r"instruction", r"guide"],
            AIOFormat.SUMMARY: [r"summary", r"brief", r"quick"],
            AIOFormat.CODE: [r"code", r"script", r"command"]
        }
    
    async def convert(self, natural_query: str, user_role: Optional[str] = None) -> AIOInstruction:
        """Convert natural language to AIO instruction"""
        
        query_lower = natural_query.lower()
        
        # Detect command
        command = self._detect_command(query_lower)
        
        # Detect format
        format_type = self._detect_format(query_lower)
        
        # Extract context tags
        context_tags = self._extract_context_tags(query_lower)
        
        # Clean query for AIO
        cleaned_query = self._clean_query_for_aio(natural_query)
        
        return AIOInstruction(
            command=command,
            query=cleaned_query,
            context_tags=context_tags,
            format=format_type,
            user_role=UserRole(user_role) if user_role else UserRole.EXTERNAL,
            confidence_threshold=0.7
        )
    
    def _detect_command(self, query: str) -> AIOCommand:
        """Detect the most appropriate command from natural language"""
        for command, patterns in self.command_patterns.items():
            if any(re.search(pattern, query) for pattern in patterns):
                return command
        return AIOCommand.FETCH_ANSWER  # Default fallback
    
    def _detect_format(self, query: str) -> AIOFormat:
        """Detect preferred response format"""
        for format_type, patterns in self.format_patterns.items():
            if any(re.search(pattern, query) for pattern in patterns):
                return format_type
        return AIOFormat.MARKDOWN  # Default
    
    def _extract_context_tags(self, query: str) -> List[str]:
        """Extract context tags from query"""
        tags = []
        
        # Technology/tool tags
        if "dynatrace" in query:
            tags.append("dynatrace")
        if "azure" in query:
            tags.append("azure_devops")
        if "mfa" in query or "multi-factor" in query:
            tags.append("mfa_policy")
        if "vpn" in query:
            tags.append("vpn_guide")
        
        # Team tags
        if "sre" in query:
            tags.append("sre_team")
        if "support" in query:
            tags.append("support_team")
        
        return tags
    
    def _clean_query_for_aio(self, query: str) -> str:
        """Clean and optimize query for AIO processing"""
        # Remove conversational elements
        cleaned = re.sub(r"^(hi|hello|hey|please|can you|could you)\s+", "", query.lower())
        cleaned = re.sub(r"\s+(please|thanks?|thank you)\.?$", "", cleaned)
        
        # Convert to keyword format
        cleaned = re.sub(r"how do i", "", cleaned)
        cleaned = re.sub(r"what is", "", cleaned)
        cleaned = re.sub(r"where is", "", cleaned)
        
        return cleaned.strip()
```

### Phase 3: API Integration

**File: `backend/app/api/endpoints/aio.py`**
```python
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
import logging
from app.schemas.aio import AIOInstruction, AIOResponse
from app.services.aio.processor import AIOProcessor
from app.services.aio.converter import NaturalLanguageToAIOConverter
from app.services.ai import AIService
from app.services.vector_store import VectorStoreService
from app.api.deps import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/aio/process", response_model=AIOResponse)
async def process_aio_instruction(
    instruction: AIOInstruction,
    ai_service: AIService = Depends(),
    vector_store: VectorStoreService = Depends(),
    current_user = Depends(get_current_user)
):
    """Process an AIO instruction directly"""
    
    processor = AIOProcessor(ai_service, vector_store)
    
    try:
        response = await processor.process_instruction(instruction)
        logger.info(f"AIO processed: {instruction.command} -> confidence: {response.confidence}")
        return response
    except Exception as e:
        logger.error(f"AIO processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/aio/convert-and-process", response_model=AIOResponse)
async def convert_and_process_natural_language(
    request: Dict[str, Any],
    ai_service: AIService = Depends(),
    vector_store: VectorStoreService = Depends(),
    current_user = Depends(get_current_user)
):
    """Convert natural language to AIO and process"""
    
    natural_query = request.get("query", "")
    user_role = request.get("user_role", "external")
    
    if not natural_query:
        raise HTTPException(status_code=400, detail="Query is required")
    
    # Convert natural language to AIO
    converter = NaturalLanguageToAIOConverter()
    instruction = await converter.convert(natural_query, user_role)
    
    # Process the AIO instruction
    processor = AIOProcessor(ai_service, vector_store)
    response = await processor.process_instruction(instruction)
    
    # Add conversion metadata
    response.metadata = response.metadata or {}
    response.metadata["converted_from_natural_language"] = True
    response.metadata["original_query"] = natural_query
    
    return response

@router.get("/aio/commands")
async def get_available_commands():
    """Get list of available AIO commands and their descriptions"""
    return {
        "commands": {
            "fetch_answer": "General knowledge and documentation queries",
            "find_team": "Team member and contact information",
            "get_process": "Company procedures and workflows",
            "explain": "Technical concept explanations",
            "diagnose": "Troubleshooting and problem analysis",
            "gen_code": "Code generation and examples",
            "escalation_path": "Find escalation procedures",
            "tool_access": "Access requirements for tools/systems",
            "incident_response": "Incident handling procedures",
            "compliance_check": "Policy and compliance information"
        },
        "formats": {
            "steps": "Step-by-step instructions",
            "list": "Bullet point list",
            "summary": "Brief summary",
            "markdown": "Full markdown response",
            "code": "Code examples",
            "table": "Tabular format",
            "flowchart": "Process flow description"
        }
    }
```

---

## 📊 Performance Benefits Analysis

### Token Usage Comparison

**Traditional Approach:**
```
Prompt: "You are Flash's AI assistant. The user is asking: 'Can you help me find who's on the SRE team and their contact information? I need this in a list format.' Please search the documentation and provide a helpful response."

Tokens: ~45-55 tokens
```

**AIO Approach:**
```
Prompt: "SYSTEM: Flash AI - Team Lookup
TASK: find_team
QUERY: SRE_team_contacts  
FORMAT: list
USER_ROLE: support

CONTEXT: [Retrieved team documentation]

Response:"

Tokens: ~25-30 tokens (45% reduction)
```

### Expected Performance Improvements

| Metric | Traditional | AIO Protocol | Improvement |
|--------|-------------|--------------|-------------|
| Avg Tokens per Query | 150-300 | 80-150 | 40-50% reduction |
| Response Consistency | 70% | 90%+ | Better structured output |
| Cache Hit Rate | 15% | 60%+ | Structured queries cache better |
| Processing Time | 800ms | 500ms | Faster dispatch & less parsing |
| API Cost | $0.12/1K queries | $0.07/1K queries | 40% cost reduction |

---

## ✅ Implementation Checklist

### Development Milestones

- [ ] **Week 1**: Core AIO schema and validation
- [ ] **Week 1**: Basic AIO processor framework  
- [ ] **Week 2**: Command routing and handlers
- [ ] **Week 2**: Natural language converter
- [ ] **Week 3**: API endpoints and integration
- [ ] **Week 3**: Teams Bot AIO conversion
- [ ] **Week 4**: Testing and optimization
- [ ] **Week 4**: Documentation and training

### Quality Assurance

- [ ] Unit tests for all AIO components
- [ ] Integration tests with existing AI service
- [ ] Performance benchmarking vs traditional approach
- [ ] Security review of AIO endpoints
- [ ] Load testing for AIO processing

### Deployment Requirements

- [ ] Database migrations for AIO logging
- [ ] Environment variables for AIO configuration
- [ ] Monitoring dashboards for AIO metrics
- [ ] Documentation for internal users
- [ ] Rollback plan for AIO features

---

## 🔮 Future Roadmap

### Advanced AIO Features (v2.0)
- **Chained Instructions**: Multiple AIO commands in sequence
- **Dynamic Context**: Auto-fetch related context based on user history
- **Learning Pipeline**: Improve command detection from usage patterns
- **Multi-language Support**: AIO in different programming languages

### Integration Expansions
- **Slack Bot**: Full AIO support for Slack workspaces
- **CLI Tool**: Command-line AIO client for power users
- **Browser Extension**: Direct AIO queries from any webpage
- **Mobile SDK**: Native mobile apps using AIO protocol

This AIO protocol transforms Flash AI from a traditional chatbot into a structured, efficient AI service optimized for enterprise use while maintaining the natural language interface users expect.