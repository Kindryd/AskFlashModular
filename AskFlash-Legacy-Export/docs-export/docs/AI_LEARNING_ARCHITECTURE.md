# AskFlash AI Learning Architecture
## Building Robust Persistent Learning for Company AI

### **🎯 Goal: Persistent AI Memory That Survives Restarts**

Transform the current file-based alias system into a robust, database-backed learning system that remembers everything across sessions, containers, and deployments.

---

## **🏗️ Current Learning Foundation (Already Built)**

### **Smart Alias Discovery System** ✅
Your system already has sophisticated learning:

```python
# Learns relationships automatically:
"Chase" → "Captain" (from document mentions)
"Stallions" → "SRE Team" → "Site Reliability Engineering" 
"dynatrace-alerts@company.com" → "Monitoring Team"
```

**Current Capabilities:**
- ✅ Pattern recognition (50+ intelligent patterns)
- ✅ Co-occurrence analysis across documents
- ✅ Confidence scoring and filtering
- ✅ Auto-refresh on content changes
- ✅ Zero manual configuration

**CRITICAL FLAW:**
```python
# File-based storage = lost on restart!
self.cache_file = Path("data/discovered_aliases_cache.json")
```

---

## **🚀 Phase 1: Database-Backed Persistent Learning**

### **1.1 Semantic Relationships Database Schema**

```python
# backend/app/models/semantic_learning.py
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text
from app.core.database import Base
from datetime import datetime

class SemanticRelationship(Base):
    """Persistent storage for learned semantic relationships"""
    __tablename__ = 'semantic_relationships'
    
    id = Column(Integer, primary_key=True)
    term = Column(String(255), index=True)
    related_term = Column(String(255), index=True)
    confidence_score = Column(Float)
    relationship_type = Column(String(50))  # alias, team_member, tool_chain, etc.
    
    # Learning metadata
    first_discovered = Column(DateTime, default=datetime.utcnow)
    last_reinforced = Column(DateTime, default=datetime.utcnow)
    times_reinforced = Column(Integer, default=1)
    source_documents = Column(Text)  # JSON list of document IDs
    
    # Quality controls
    verified_by_human = Column(Boolean, default=False)
    marked_for_review = Column(Boolean, default=False)
    
    def __repr__(self):
        return f"<SemanticRelationship({self.term} ↔ {self.related_term}, confidence={self.confidence_score:.2f})>"

class LearningSession(Base):
    """Track learning sessions to understand when knowledge was acquired"""
    __tablename__ = 'learning_sessions'
    
    id = Column(Integer, primary_key=True)
    session_start = Column(DateTime, default=datetime.utcnow)
    documents_processed = Column(Integer)
    relationships_discovered = Column(Integer)
    relationships_reinforced = Column(Integer)
    learning_source = Column(String(100))  # 'document_analysis', 'user_query', 'conversation'
```

### **1.2 Enhanced Smart Alias Discovery with Persistence**

```python
# backend/app/services/persistent_alias_discovery.py
from app.models.semantic_learning import SemanticRelationship, LearningSession
from app.services.smart_alias_discovery import SmartAliasDiscovery
from sqlalchemy.orm import Session
from typing import Dict, List, Set

class PersistentAliasDiscovery(SmartAliasDiscovery):
    """Enhanced alias discovery with database persistence"""
    
    def __init__(self, db: Session):
        super().__init__()
        self.db = db
    
    async def discover_and_store_relationships(self, documents: List[Dict]) -> Dict[str, List[str]]:
        """Discover relationships and store them persistently"""
        
        # Start learning session
        session = LearningSession(
            documents_processed=len(documents),
            learning_source='document_analysis'
        )
        self.db.add(session)
        self.db.commit()
        
        # Discover new relationships
        discovered = self.analyze_document_collection(documents)
        
        new_relationships = 0
        reinforced_relationships = 0
        
        for term, related_terms in discovered.items():
            for related_term in related_terms:
                # Check if relationship already exists
                existing = self.db.query(SemanticRelationship).filter(
                    ((SemanticRelationship.term == term) & 
                     (SemanticRelationship.related_term == related_term)) |
                    ((SemanticRelationship.term == related_term) & 
                     (SemanticRelationship.related_term == term))
                ).first()
                
                if existing:
                    # Reinforce existing relationship
                    existing.last_reinforced = datetime.utcnow()
                    existing.times_reinforced += 1
                    existing.confidence_score = min(1.0, existing.confidence_score + 0.1)
                    reinforced_relationships += 1
                else:
                    # Create new relationship
                    relationship = SemanticRelationship(
                        term=term,
                        related_term=related_term,
                        confidence_score=self.confidence_threshold,
                        relationship_type='semantic_alias'
                    )
                    self.db.add(relationship)
                    new_relationships += 1
        
        # Update session stats
        session.relationships_discovered = new_relationships
        session.relationships_reinforced = reinforced_relationships
        
        self.db.commit()
        
        logger.info(f"💾 Stored {new_relationships} new relationships, reinforced {reinforced_relationships}")
        return discovered
    
    async def get_persistent_aliases(self) -> Dict[str, List[str]]:
        """Retrieve all learned relationships from database"""
        relationships = self.db.query(SemanticRelationship).filter(
            SemanticRelationship.confidence_score >= self.confidence_threshold
        ).all()
        
        aliases = {}
        for rel in relationships:
            if rel.term not in aliases:
                aliases[rel.term] = []
            if rel.related_term not in aliases[rel.term]:
                aliases[rel.term].append(rel.related_term)
                
            # Make bidirectional
            if rel.related_term not in aliases:
                aliases[rel.related_term] = []
            if rel.term not in aliases[rel.related_term]:
                aliases[rel.related_term].append(rel.term)
        
        return aliases
```

---

## **🧠 Phase 2: Conversational Learning from User Interactions**

### **2.1 Query-Based Learning Engine**

```python
# backend/app/services/conversational_learning.py
class ConversationalLearningService:
    """Learn from user queries and AI responses"""
    
    def __init__(self, db: Session, vector_store: VectorStoreService):
        self.db = db
        self.vector_store = vector_store
        
    async def learn_from_user_query(self, query: str, response: str, user_feedback: str = None):
        """Learn from user questions and AI responses"""
        
        # Extract learning opportunities
        learning_signals = await self._extract_learning_signals(query, response)
        
        for signal in learning_signals:
            await self._process_learning_signal(signal)
    
    async def _extract_learning_signals(self, query: str, response: str) -> List[Dict]:
        """Use AI to extract learning opportunities from conversations"""
        
        learning_prompt = f"""
        Analyze this conversation for learning opportunities:
        
        User Query: {query}
        AI Response: {response}
        
        Extract any semantic relationships, aliases, or knowledge that should be remembered:
        - Name/nickname relationships ("Chase is called Captain")
        - Team/role relationships ("Chase is the SRE lead")
        - Tool/process relationships ("Dynatrace alerts go to Slack #monitoring")
        - Workflow connections ("After deployment, check Dynatrace dashboard")
        
        Return as JSON list of learning signals.
        """
        
        # Send to OpenAI for extraction
        extraction_response = await self.openai_client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": learning_prompt}],
            temperature=0.1
        )
        
        try:
            signals = json.loads(extraction_response.choices[0].message.content)
            return signals
        except:
            return []
    
    async def _process_learning_signal(self, signal: Dict):
        """Process and store a learning signal"""
        
        if signal.get('type') == 'alias_relationship':
            relationship = SemanticRelationship(
                term=signal['term'],
                related_term=signal['related_term'],
                confidence_score=0.7,  # Lower confidence for conversation-based learning
                relationship_type='conversational_alias',
                source_documents=json.dumps([f"conversation_{datetime.utcnow().isoformat()}"])
            )
            self.db.add(relationship)
        
        elif signal.get('type') == 'workflow_step':
            # Store workflow relationships
            pass
            
        self.db.commit()
```

### **2.2 Usage Pattern Learning**

```python
# backend/app/services/usage_pattern_learning.py
class UsagePatternLearningService:
    """Learn from how users actually use the system"""
    
    async def track_query_success(self, query: str, documents_found: List[str], user_satisfaction: bool):
        """Learn which queries lead to successful outcomes"""
        
        # Store successful query patterns
        if user_satisfaction:
            await self._reinforce_successful_patterns(query, documents_found)
        else:
            await self._identify_knowledge_gaps(query)
    
    async def _reinforce_successful_patterns(self, query: str, documents: List[str]):
        """Strengthen confidence in query-document relationships"""
        
        # Extract key terms from successful query
        key_terms = await self._extract_key_terms(query)
        
        for term in key_terms:
            for doc_id in documents:
                # Increase confidence that this term leads to this document
                # This helps with future similar queries
                pass
    
    async def _identify_knowledge_gaps(self, failed_query: str):
        """Identify areas where the AI lacks knowledge"""
        
        # Log failed queries for analysis
        gap = KnowledgeGap(
            query=failed_query,
            identified_at=datetime.utcnow(),
            requires_attention=True
        )
        self.db.add(gap)
        self.db.commit()
```

---

## **🔮 Phase 3: Advanced Vector-Based Learning**

### **3.1 Qdrant Learning Collections**

```python
# Separate collections for different types of learning
COLLECTIONS = {
    'flash_docs': 'Current document embeddings',
    'flash_relationships': 'Learned semantic relationships', 
    'flash_conversations': 'User conversation patterns',
    'flash_workflows': 'Process and tool chains',
    'flash_expertise': 'Who knows what (expert mapping)'
}

class AdvancedVectorLearning:
    """Use Qdrant for sophisticated learning storage"""
    
    async def store_relationship_embedding(self, term1: str, term2: str, relationship_type: str, context: str):
        """Store relationship as vector for semantic similarity"""
        
        # Create relationship text for embedding
        relationship_text = f"{term1} {relationship_type} {term2}. Context: {context}"
        
        embedding = await self.generate_embedding(relationship_text)
        
        await self.qdrant_client.upsert(
            collection_name="flash_relationships",
            points=[{
                "id": f"{term1}_{term2}_{relationship_type}",
                "vector": embedding,
                "payload": {
                    "term1": term1,
                    "term2": term2,
                    "relationship_type": relationship_type,
                    "context": context,
                    "confidence": 0.8,
                    "learned_from": "document_analysis",
                    "created_at": datetime.utcnow().isoformat()
                }
            }]
        )
```

### **3.2 Cross-Session Memory**

```python
class CrossSessionMemory:
    """Remember context across different chat sessions"""
    
    async def remember_user_context(self, user_id: str, context_type: str, content: str):
        """Store user-specific context that persists across sessions"""
        
        # Example: "User John frequently asks about Dynatrace issues"
        # This context helps tailor future responses
        
        memory_embedding = await self.generate_embedding(content)
        
        await self.qdrant_client.upsert(
            collection_name="flash_user_memory",
            points=[{
                "id": f"{user_id}_{context_type}_{int(time.time())}",
                "vector": memory_embedding,
                "payload": {
                    "user_id": user_id,
                    "context_type": context_type,
                    "content": content,
                    "created_at": datetime.utcnow().isoformat(),
                    "last_accessed": datetime.utcnow().isoformat()
                }
            }]
        )
    
    async def retrieve_user_context(self, user_id: str, current_query: str) -> List[str]:
        """Retrieve relevant context for this user's current query"""
        
        query_embedding = await self.generate_embedding(current_query)
        
        results = await self.qdrant_client.search(
            collection_name="flash_user_memory",
            query_vector=query_embedding,
            query_filter={
                "must": [{"key": "user_id", "match": {"value": user_id}}]
            },
            limit=5
        )
        
        return [result.payload["content"] for result in results]
```

---

## **🛡️ Quality Controls & Anti-Bloat Mechanisms**

### **4.1 Information Decay System**

```python
class InformationDecayService:
    """Prevent information bloat through smart decay"""
    
    async def decay_old_relationships(self):
        """Reduce confidence in relationships not recently reinforced"""
        
        # Find relationships not seen in 90 days
        old_relationships = self.db.query(SemanticRelationship).filter(
            SemanticRelationship.last_reinforced < datetime.utcnow() - timedelta(days=90)
        ).all()
        
        for rel in old_relationships:
            # Decay confidence
            rel.confidence_score *= 0.9
            
            # Mark for review if confidence drops too low
            if rel.confidence_score < 0.3:
                rel.marked_for_review = True
        
        self.db.commit()
```

### **4.2 Confidence-Based Filtering**

```python
class QualityControlService:
    """Maintain high-quality learned knowledge"""
    
    def get_high_confidence_relationships(self) -> List[SemanticRelationship]:
        """Return only high-confidence relationships for production use"""
        return self.db.query(SemanticRelationship).filter(
            SemanticRelationship.confidence_score >= 0.7,
            SemanticRelationship.marked_for_review == False
        ).all()
    
    async def validate_new_relationship(self, term1: str, term2: str) -> bool:
        """Use AI to validate if a relationship makes sense"""
        
        validation_prompt = f"""
        Does this relationship make sense in a corporate context?
        Term 1: {term1}
        Term 2: {term2}
        
        Consider: Could these refer to the same thing, person, team, or concept?
        Answer with confidence score 0-1.
        """
        
        # Use AI for validation
        response = await self._ask_ai(validation_prompt)
        return float(response) > 0.6
```

---

## **🚀 Implementation Roadmap**

### **Week 1: Database Migration**
1. Create semantic learning database schema
2. Migrate existing file-based aliases to database
3. Update Enhanced Documentation Service to use database

### **Week 2: Conversational Learning**
1. Implement query-based learning extraction
2. Add user feedback collection
3. Build learning signal processing

### **Week 3: Vector Learning**
1. Create relationship embedding collections
2. Implement cross-session memory
3. Add advanced similarity search

### **Week 4: Quality Controls**
1. Implement confidence decay
2. Add knowledge validation
3. Build admin review interface

---

## **📊 Expected Learning Capabilities**

### **Example Learning Scenarios:**

**User says:** "Chase is our captain for the monitoring team"
**AI learns:** `Chase ↔ Captain ↔ Monitoring Team Lead`

**User asks:** "Who handles Dynatrace alerts?"  
**AI remembers:** Previous conversations about monitoring → Returns Chase/Captain

**Document analysis discovers:** "stallions@company.com" mentioned with "SRE procedures"
**AI learns:** `Stallions ↔ SRE Team ↔ Email Contact`

**Cross-session memory:** User John frequently asks deployment questions
**AI adapts:** Future responses include more deployment context for John

### **Quality Assurance:**
- ✅ **Confidence scoring** prevents low-quality relationships
- ✅ **Decay mechanisms** remove outdated information  
- ✅ **AI validation** prevents nonsensical relationships
- ✅ **Human review** for questionable discoveries
- ✅ **Source tracking** for auditability

---

## **🎯 Business Impact**

With this system, your AI will:

1. **Remember company culture** ("Captain" = Chase, "Stallions" = SRE team)
2. **Learn workflows** (deployment → testing → monitoring → alerts)
3. **Adapt to users** (John gets deployment-focused responses)
4. **Persist knowledge** (survives restarts, updates, scaling)
5. **Self-improve** (gets smarter with every interaction)

**Result:** An AI that truly understands your company and gets better every day. 