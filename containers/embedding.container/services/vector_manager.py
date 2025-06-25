from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import ResponseHandlingException
from typing import List, Dict, Any, Optional
import logging
import asyncio
import numpy as np
from datetime import datetime
import openai

from core.config import settings

logger = logging.getLogger(__name__)

class VectorStoreManager:
    """Enhanced Qdrant vector store manager with lazy loading and optimizations"""
    
    def __init__(self):
        self.client = None
        self.collection_name = settings.QDRANT_COLLECTION_NAME
        self.vector_size = settings.VECTOR_DIMENSIONS
        self._initialized = False
        
        # OpenAI client for embeddings
        openai.api_key = settings.OPENAI_API_KEY
        
    async def _initialize_client(self):
        """Initialize Qdrant client with lazy loading (cow loading pattern)"""
        if self._initialized:
            return
            
        try:
            logger.info("🐄 Initializing Qdrant connection... (Cow loading)")
            
            # Create client
            self.client = QdrantClient(
                url=settings.QDRANT_URL,
                timeout=30,
                prefer_grpc=False
            )
            
            # Test connection
            await asyncio.to_thread(self.client.get_collections)
            
            self._initialized = True
            logger.info("✅ Qdrant connection established")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Qdrant client: {e}")
            raise
    
    async def initialize_collections(self):
        """Initialize required collections with proper configuration"""
        await self._initialize_client()
        
        try:
            # Main documents collection
            await self._ensure_collection_exists(
                self.collection_name,
                vector_size=self.vector_size,
                distance=models.Distance.COSINE
            )
            
            # Aliases collection for semantic relationships
            await self._ensure_collection_exists(
                f"{self.collection_name}_aliases",
                vector_size=self.vector_size,
                distance=models.Distance.COSINE
            )
            
            logger.info("✅ All Qdrant collections verified")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize collections: {e}")
            raise
    
    async def _ensure_collection_exists(
        self, 
        collection_name: str, 
        vector_size: int = 1536,
        distance: models.Distance = models.Distance.COSINE
    ):
        """Ensure a collection exists, create if it doesn't"""
        try:
            # Check if collection exists
            collections = await asyncio.to_thread(self.client.get_collections)
            existing_names = [col.name for col in collections.collections]
            
            if collection_name not in existing_names:
                logger.info(f"Creating collection: {collection_name}")
                await asyncio.to_thread(
                    self.client.create_collection,
                    collection_name=collection_name,
                    vectors_config=models.VectorParams(
                        size=vector_size,
                        distance=distance
                    )
                )
                logger.info(f"✅ Created collection: {collection_name}")
            else:
                logger.info(f"✅ Collection already exists: {collection_name}")
                
        except Exception as e:
            logger.error(f"❌ Error ensuring collection {collection_name}: {e}")
            raise
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenAI with error handling"""
        try:
            response = await asyncio.to_thread(
                openai.embeddings.create,
                input=text,
                model=settings.EMBEDDING_MODEL
            )
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"❌ Failed to generate embedding: {e}")
            raise
    
    async def store_document_embedding(
        self,
        document_id: str,
        text: str,
        metadata: Dict[str, Any],
        collection_name: Optional[str] = None
    ) -> bool:
        """Store a single document embedding with metadata"""
        await self._initialize_client()
        
        try:
            # Generate embedding
            embedding = await self.generate_embedding(text)
            
            # Prepare point
            point = models.PointStruct(
                id=document_id,
                vector=embedding,
                payload={
                    **metadata,
                    "text": text,
                    "indexed_at": datetime.utcnow().isoformat(),
                    "embedding_model": settings.EMBEDDING_MODEL
                }
            )
            
            # Store in collection
            collection = collection_name or self.collection_name
            await asyncio.to_thread(
                self.client.upsert,
                collection_name=collection,
                points=[point]
            )
            
            logger.info(f"✅ Stored embedding for document: {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to store embedding for {document_id}: {e}")
            return False
    
    async def store_batch_embeddings(
        self,
        documents: List[Dict[str, Any]],
        collection_name: Optional[str] = None,
        batch_size: int = 100
    ) -> Dict[str, int]:
        """Store multiple document embeddings in batches"""
        await self._initialize_client()
        
        results = {"success": 0, "failed": 0}
        collection = collection_name or self.collection_name
        
        # Process in batches
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            points = []
            
            try:
                # Generate embeddings for batch
                texts = [doc["text"] for doc in batch]
                embeddings = await self._generate_batch_embeddings(texts)
                
                # Create points
                for doc, embedding in zip(batch, embeddings):
                    point = models.PointStruct(
                        id=doc["id"],
                        vector=embedding,
                        payload={
                            **doc.get("metadata", {}),
                            "text": doc["text"],
                            "indexed_at": datetime.utcnow().isoformat(),
                            "embedding_model": settings.EMBEDDING_MODEL
                        }
                    )
                    points.append(point)
                
                # Store batch
                await asyncio.to_thread(
                    self.client.upsert,
                    collection_name=collection,
                    points=points
                )
                
                results["success"] += len(points)
                logger.info(f"✅ Stored batch of {len(points)} embeddings")
                
            except Exception as e:
                logger.error(f"❌ Failed to store batch: {e}")
                results["failed"] += len(batch)
        
        return results
    
    async def _generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts efficiently"""
        try:
            response = await asyncio.to_thread(
                openai.embeddings.create,
                input=texts,
                model=settings.EMBEDDING_MODEL
            )
            return [data.embedding for data in response.data]
            
        except Exception as e:
            logger.error(f"❌ Failed to generate batch embeddings: {e}")
            raise
    
    async def semantic_search(
        self,
        query: str,
        limit: int = 10,
        score_threshold: float = 0.7,
        filters: Optional[Dict[str, Any]] = None,
        collection_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Perform semantic search with filtering"""
        await self._initialize_client()
        
        try:
            # Generate query embedding
            query_embedding = await self.generate_embedding(query)
            
            # Build search filter
            search_filter = None
            if filters:
                search_filter = models.Filter(
                    must=[
                        models.FieldCondition(
                            key=key,
                            match=models.MatchValue(value=value)
                        )
                        for key, value in filters.items()
                    ]
                )
            
            # Perform search
            collection = collection_name or self.collection_name
            search_results = await asyncio.to_thread(
                self.client.search,
                collection_name=collection,
                query_vector=query_embedding,
                query_filter=search_filter,
                limit=limit,
                score_threshold=score_threshold,
                with_payload=True,
                with_vectors=False
            )
            
            # Format results
            results = []
            for result in search_results:
                results.append({
                    "id": result.id,
                    "score": result.score,
                    "payload": result.payload,
                    "text": result.payload.get("text", ""),
                    "metadata": {k: v for k, v in result.payload.items() if k != "text"}
                })
            
            logger.info(f"✅ Found {len(results)} results for query")
            return results
            
        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            return []
    
    async def delete_document(self, document_id: str, collection_name: Optional[str] = None) -> bool:
        """Delete a document from the vector store"""
        await self._initialize_client()
        
        try:
            collection = collection_name or self.collection_name
            await asyncio.to_thread(
                self.client.delete,
                collection_name=collection,
                points_selector=models.PointIdsList(
                    points=[document_id]
                )
            )
            
            logger.info(f"✅ Deleted document: {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to delete document {document_id}: {e}")
            return False
    
    async def get_collections_info(self) -> List[Dict[str, Any]]:
        """Get information about all collections"""
        await self._initialize_client()
        
        try:
            collections = await asyncio.to_thread(self.client.get_collections)
            
            info = []
            for collection in collections.collections:
                collection_info = await asyncio.to_thread(
                    self.client.get_collection,
                    collection_name=collection.name
                )
                
                info.append({
                    "name": collection.name,
                    "points_count": collection_info.points_count,
                    "segments_count": collection_info.segments_count,
                    "status": collection_info.status.value,
                    "vector_size": collection_info.config.params.vectors.size,
                    "distance": collection_info.config.params.vectors.distance.value
                })
            
            return info
            
        except Exception as e:
            logger.error(f"❌ Failed to get collections info: {e}")
            return []
    
    async def create_collection(self, collection_name: str, vector_size: int = 1536) -> bool:
        """Create a new collection"""
        await self._initialize_client()
        
        try:
            await self._ensure_collection_exists(collection_name, vector_size)
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create collection {collection_name}: {e}")
            return False
    
    async def health_check(self) -> bool:
        """Check if Qdrant is healthy"""
        try:
            await self._initialize_client()
            await asyncio.to_thread(self.client.get_collections)
            return True
            
        except Exception as e:
            logger.error(f"❌ Qdrant health check failed: {e}")
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive vector store statistics"""
        try:
            await self._initialize_client()
            
            collections_info = await self.get_collections_info()
            
            total_points = sum(col["points_count"] for col in collections_info)
            total_collections = len(collections_info)
            
            return {
                "total_collections": total_collections,
                "total_documents": total_points,
                "collections": collections_info,
                "embedding_model": settings.EMBEDDING_MODEL,
                "vector_dimensions": self.vector_size,
                "connection_status": "healthy" if self._initialized else "not_initialized"
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get stats: {e}")
            return {
                "error": str(e),
                "connection_status": "error"
            } 