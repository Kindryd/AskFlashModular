# ⚡ AskFlash: Advanced Streaming Chat with Multi-Step AI Reasoning

This guide explains how to implement **sophisticated, step-by-step AI responses** similar to Claude's reasoning process in Cursor. Unlike simple text streaming, this creates a true thinking AI that shows its reasoning process while performing actual operations.

---

## 🧠 How Claude Actually Works (In Cursor)

When Claude processes complex requests, it:

1. **Analyzes the request** - Understanding context and requirements
2. **Plans the approach** - Determining what tools/operations are needed  
3. **Executes step-by-step** - Performing searches, reading files, analysis
4. **Synthesizes results** - Combining findings into comprehensive responses
5. **Provides transparency** - Showing sources, confidence, and reasoning

This is **not just text streaming** - it's multi-step reasoning with real operations.

---

## ✅ Current AskFlash Architecture

Your system already has the foundation for sophisticated AI reasoning:

- **RAG Engine**: Vector search with Qdrant + documentation retrieval
- **Dual Mode System**: Company (Flash Team) vs General AI modes  
- **Service Layer**: AIService, DocumentationService, VectorStoreService
- **Conversation Management**: History tracking and context preservation
- **Confidence Scoring**: Based on documentation relevance

---

## 🚀 Implementation Strategy

### Phase 1: Enhanced AI Reasoning Service

Create `backend/app/services/streaming_ai.py`:

```python
from typing import AsyncGenerator, Dict, List, Any, Optional
from fastapi import Request
from fastapi.responses import StreamingResponse
import asyncio
import json
from datetime import datetime

from app.services.ai import AIService
from app.services.documentation import DocumentationService
from app.services.vector_store import VectorStoreService
from app.models.ruleset import Ruleset
from app.schemas.search import DocumentationSource

class StreamingAIService(AIService):
    """Enhanced AI service with step-by-step reasoning capabilities"""
    
    async def process_query_with_reasoning(
        self,
        query: str,
        ruleset: Ruleset,
        user_id: int,
        conversation_id: Optional[str] = None,
        mode: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Process query with transparent step-by-step reasoning.
        Yields intermediate thoughts and progress updates.
        """
        
        # Step 1: Analysis Phase
        yield self._format_step("🔍 Analyzing your request...")
        await asyncio.sleep(0.5)  # Realistic processing delay
        
        # Determine processing mode
        if not mode:
            yield self._format_step("🤔 Determining best approach...")
            mode = await self._detect_mode(query, ruleset)
            yield self._format_step(f"✅ Selected {mode} mode")
        
        # Step 2: Context Gathering
        history = []
        if conversation_id:
            yield self._format_step("📚 Retrieving conversation context...")
            history = await self._get_conversation_history(conversation_id)
            if history:
                yield self._format_step(f"✅ Found {len(history)} previous messages")
        
        # Step 3: Knowledge Retrieval (Company Mode)
        sources = []
        confidence = 0.8  # Default for general mode
        
        if mode == "company":
            yield self._format_step("🔎 Searching Flash documentation...")
            
            # Perform vector search
            docs = await self.documentation_service.search_documentation(
                query, ruleset.search_priority
            )
            
            if docs:
                yield self._format_step(f"📋 Found {len(docs)} relevant documents")
                sources = docs
                confidence = self._calculate_confidence(docs)
                
                # Show specific sources found
                for i, doc in enumerate(docs[:3], 1):
                    yield self._format_step(f"  {i}. {doc.title or 'Document'}")
            else:
                yield self._format_step("ℹ️ No specific documentation found, using general knowledge")
        
        # Step 4: Response Generation
        yield self._format_step("💭 Generating comprehensive response...")
        
        # Build enhanced system prompt with reasoning instructions
        system_prompt = self._build_reasoning_system_prompt(mode, ruleset)
        
        # Generate response using existing AI logic but with enhanced prompting
        if mode == "company":
            response, _, _ = await self._process_company_query(
                query, ruleset, system_prompt, history
            )
        else:
            response, _, _ = await self._process_general_query(
                query, ruleset, system_prompt, history
            )
        
        # Step 5: Quality Assessment
        yield self._format_step("🎯 Assessing response quality...")
        final_confidence = await self._analyze_response_quality(query, response, sources)
        
        # Step 6: Final Response
        yield self._format_step("✨ Response ready!")
        await asyncio.sleep(0.3)
        
        # Format and yield final response
        formatted_response = self._format_response(
            response, sources, final_confidence, mode, ruleset
        )
        
        # Store interaction
        await self._store_interaction(
            query, formatted_response, mode, sources, final_confidence,
            ruleset.id, user_id, conversation_id
        )
        
        # Yield final response as structured data
        yield self._format_final_response({
            "response": formatted_response,
            "mode": mode,
            "sources": [self._source_to_dict(s) for s in sources],
            "confidence": final_confidence,
            "conversation_id": conversation_id,
            "timestamp": datetime.now().isoformat()
        })
    
    def _format_step(self, message: str) -> str:
        """Format intermediate reasoning step"""
        return json.dumps({
            "type": "thinking",
            "message": message,
            "timestamp": datetime.now().isoformat()
        }) + "\n"
    
    def _format_final_response(self, data: Dict) -> str:
        """Format final response data"""
        return json.dumps({
            "type": "response",
            "data": data
        }) + "\n"
    
    def _build_reasoning_system_prompt(self, mode: str, ruleset: Ruleset) -> str:
        """Enhanced system prompt for reasoning mode"""
        base_prompt = self._build_system_prompt(mode, ruleset)
        
        reasoning_addition = """
        
IMPORTANT: When responding, provide clear, comprehensive answers that:
1. Directly address the user's question
2. Explain your reasoning when relevant
3. Acknowledge limitations or uncertainties
4. Provide actionable guidance when appropriate
5. Use the retrieved documentation effectively (in company mode)
"""
        
        return base_prompt + reasoning_addition
    
    async def _analyze_response_quality(
        self, 
        query: str, 
        response: str, 
        sources: List[DocumentationSource]
    ) -> float:
        """Analyze response quality and adjust confidence"""
        # This could use additional AI calls to assess response quality
        # For now, use existing confidence calculation
        if sources:
            return self._calculate_confidence(sources)
        
        # For general mode, estimate confidence based on response completeness
        if len(response) > 100 and "I don't know" not in response.lower():
            return 0.85
        return 0.65
    
    def _source_to_dict(self, source: DocumentationSource) -> Dict:
        """Convert source to dictionary for JSON serialization"""
        return {
            "title": source.title,
            "url": source.url,
            "relevance_score": getattr(source, 'relevance_score', 0.0),
            "content_preview": getattr(source, 'content', '')[:200] + "..." if hasattr(source, 'content') else ""
        }
```

### Phase 2: Streaming Chat Endpoint

Add to `backend/app/api/api_v1/endpoints/chat.py`:

```python
from fastapi.responses import StreamingResponse
from app.services.streaming_ai import StreamingAIService
import json

@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> StreamingResponse:
    """
    Process chat request with step-by-step reasoning display.
    Compatible with existing ChatRequest schema.
    """
    try:
        logger.info(f"Processing streaming chat from user {current_user.email}")
        
        # Get active ruleset (same as regular chat)
        result = await db.execute(
            select(Ruleset).where(
                Ruleset.id == request.ruleset_id,
                Ruleset.is_active == True
            )
        )
        ruleset = result.scalars().first()
        
        if not ruleset:
            # Return error as streamed response
            async def error_stream():
                yield json.dumps({
                    "type": "error",
                    "message": f"Active ruleset with ID {request.ruleset_id} not found"
                }) + "\n"
            
            return StreamingResponse(
                error_stream(), 
                media_type="text/plain",
                headers={"Access-Control-Allow-Origin": "*"}
            )
        
        # Initialize enhanced services
        doc_service = DocumentationService(ruleset, db)
        streaming_ai_service = StreamingAIService(db, doc_service)
        
        # Generate conversation ID if not provided
        conversation_id = request.conversation_id or str(uuid.uuid4())
        
        # Process with reasoning
        return StreamingResponse(
            streaming_ai_service.process_query_with_reasoning(
                query=request.query,
                ruleset=ruleset,
                user_id=current_user.id,
                conversation_id=conversation_id,
                mode=request.mode
            ),
            media_type="text/plain",
            headers={
                "Access-Control-Allow-Origin": "*",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )
        
    except Exception as e:
        logger.error(f"Error in streaming chat: {str(e)}", exc_info=True)
        
        async def error_stream():
            yield json.dumps({
                "type": "error", 
                "message": f"Error processing request: {str(e)}"
            }) + "\n"
        
        return StreamingResponse(error_stream(), media_type="text/plain")
```

### Phase 3: Enhanced Frontend Integration

Update `frontend/src/Chat.js`:

```javascript
const [streamingMessage, setStreamingMessage] = useState("");
const [isThinking, setIsThinking] = useState(false);
const [thinkingSteps, setThinkingSteps] = useState([]);

const handleStreamedChat = async (query, mode = 'company') => {
  setLoading(true);
  setIsThinking(true);
  setThinkingSteps([]);
  setStreamingMessage("");
  
  try {
    const response = await fetch('/api/v1/chat/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify({
        query,
        mode,
        ruleset_id: 1,
        conversation_id: conversationId
      })
    });

    if (!response.ok) {
      throw new Error('Network response was not ok');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split('\n').filter(line => line.trim());

      for (const line of lines) {
        try {
          const data = JSON.parse(line);
          
          if (data.type === 'thinking') {
            setThinkingSteps(prev => [...prev, {
              message: data.message,
              timestamp: data.timestamp
            }]);
          } else if (data.type === 'response') {
            // Final response received
            setIsThinking(false);
            setMessages(prev => [...prev, {
              role: 'assistant',
              content: data.data.response,
              mode: data.data.mode,
              sources: data.data.sources,
              confidence: data.data.confidence,
              timestamp: data.data.timestamp
            }]);
          } else if (data.type === 'error') {
            setIsThinking(false);
            setError(data.message);
          }
        } catch (parseError) {
          console.warn('Failed to parse streaming data:', line);
        }
      }
    }
  } catch (error) {
    console.error('Streaming error:', error);
    setError('Failed to process request');
  } finally {
    setLoading(false);
    setIsThinking(false);
  }
};

// Enhanced UI components
const ThinkingIndicator = () => (
  <div className="thinking-indicator">
    <div className="thinking-header">
      <span className="thinking-icon">🧠</span>
      <span>AI Assistant is thinking...</span>
    </div>
    <div className="thinking-steps">
      {thinkingSteps.map((step, index) => (
        <div key={index} className="thinking-step">
          <span className="step-icon">•</span>
          <span className="step-message">{step.message}</span>
        </div>
      ))}
    </div>
  </div>
);
```

### Phase 4: Enhanced CSS for Thinking Display

Add to `frontend/src/Chat.css`:

```css
/* Thinking indicator styles */
.thinking-indicator {
  background: var(--bg-secondary);
  border-radius: 12px;
  padding: 16px;
  margin: 16px 0;
  border-left: 4px solid var(--flash-primary);
}

.thinking-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: var(--flash-primary);
  margin-bottom: 12px;
}

.thinking-icon {
  animation: pulse 2s infinite;
}

.thinking-steps {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.thinking-step {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 0;
  font-size: 14px;
  color: var(--text-secondary);
  animation: fadeInUp 0.3s ease-out;
}

.step-icon {
  color: var(--flash-primary);
  font-weight: bold;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
```

---

## 🧪 Testing & Validation

1. **Start Services:**
   ```bash
   docker-compose up --build
   ```

2. **Test Questions:**
   ```
   Flash Team Mode: "How do Flash payment systems work?"
   General Mode: "Explain quantum computing"
   ```

3. **Expected Behavior:**
   - Shows thinking steps in real-time
   - Performs actual document searches
   - Displays confidence scores
   - Provides source citations
   - Maintains conversation context

---

## 🚀 Advanced Enhancements

### A. Smart Tool Selection
```python
async def _select_tools(self, query: str) -> List[str]:
    """AI decides which tools/services to use"""
    # Use GPT to analyze what tools are needed
    # Return list like ["vector_search", "web_search", "calculation"]
```

### B. Parallel Operations
```python
async def _parallel_search(self, query: str):
    """Search multiple sources simultaneously"""
    tasks = [
        self.vector_store.search(query),
        self.web_search.search(query),
        self.database.search(query)
    ]
    results = await asyncio.gather(*tasks)
    return self._merge_results(results)
```

### C. Confidence-Based Iteration
```python
async def _iterative_refinement(self, query: str, initial_response: str):
    """Refine response if confidence is low"""
    if confidence < 0.7:
        yield "🔄 Confidence low, searching additional sources..."
        # Perform additional searches or use different strategies
```

---

## ✅ Key Differences from Simple Streaming

**Simple Text Streaming:**
- Just breaks up a pre-generated response
- No real operations during streaming
- Fake progress indicators

**Advanced Reasoning (This Implementation):**
- Performs actual operations (searches, analysis)
- Real-time decision making
- Transparent tool usage
- Confidence assessment
- Context-aware processing

This creates a truly intelligent assistant that shows its work, similar to how Claude operates in Cursor! 🚀
