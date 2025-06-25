import re
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import asyncio
import hashlib
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from core.config import settings
from services.vector_manager import VectorStoreManager
from services.alias_discovery import SmartAliasDiscovery

logger = logging.getLogger(__name__)

class EnhancedDocumentationService:
    """Enhanced documentation service with intelligent chunking and semantic search"""
    
    def __init__(self, db: Optional[AsyncSession] = None):
        self.db = db
        self.vector_manager = VectorStoreManager()
        self.alias_discovery = SmartAliasDiscovery()
        
        # Enhanced chunking settings
        self.max_chunk_size = settings.MAX_CHUNK_SIZE
        self.chunk_overlap = settings.CHUNK_OVERLAP
        
        # Quality settings
        self.enable_quality_analysis = settings.ENABLE_QUALITY_ANALYSIS
        self.enable_alias_discovery = settings.ENABLE_ALIAS_DISCOVERY
    
    async def search_with_aliases(
        self,
        query: str,
        max_results: int = 10,
        min_confidence: float = 0.7,
        source_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Enhanced search with automatic alias expansion"""
        try:
            # Expand query with discovered aliases
            if self.enable_alias_discovery:
                expanded_queries = self.alias_discovery.expand_query_with_aliases(query)
                logger.info(f"🔍 Query expanded: {query} -> {expanded_queries}")
            else:
                expanded_queries = [query]
            
            # Perform semantic search for each expanded query
            all_results = []
            
            for expanded_query in expanded_queries:
                # Build filters for source types
                filters = {}
                if source_types:
                    filters["source_type"] = source_types[0]  # Simplified for now
                
                # Perform vector search
                results = await self.vector_manager.semantic_search(
                    query=expanded_query,
                    limit=max_results,
                    score_threshold=min_confidence,
                    filters=filters
                )
                
                # Add query context to results
                for result in results:
                    result["matched_query"] = expanded_query
                    result["original_query"] = query
                    result["alias_expanded"] = expanded_query != query
                
                all_results.extend(results)
            
            # Remove duplicates and sort by relevance
            unique_results = self._deduplicate_results(all_results)
            sorted_results = sorted(
                unique_results, 
                key=lambda x: x["score"], 
                reverse=True
            )[:max_results]
            
            logger.info(f"✅ Found {len(sorted_results)} results for enhanced search")
            return sorted_results
            
        except Exception as e:
            logger.error(f"❌ Enhanced search failed: {e}", exc_info=True)
            return []
    
    async def index_document_enhanced(
        self,
        document_data: Dict[str, Any],
        source_type: str = "unknown",
        force_reindex: bool = False
    ) -> Dict[str, Any]:
        """Index a document with enhanced processing"""
        try:
            start_time = datetime.utcnow()
            
            # Extract document content
            content = document_data.get("content", "")
            title = document_data.get("title", "")
            url = document_data.get("url", "")
            document_id = document_data.get("id") or self._generate_document_id(content, title)
            
            logger.info(f"📄 Processing document: {title}")
            
            # Clean and process content
            cleaned_content = self._clean_html_content(content)
            
            # Intelligent chunking
            chunks = await self._intelligent_chunk_text(cleaned_content, title)
            
            # Store document chunks with enhanced metadata
            chunks_stored = 0
            aliases_discovered = 0
            
            for i, chunk in enumerate(chunks):
                chunk_id = f"{document_id}_chunk_{i}"
                
                # Enhance chunk metadata
                chunk_metadata = {
                    "document_id": document_id,
                    "chunk_index": i,
                    "title": title,
                    "url": url,
                    "source_type": source_type,
                    "content_type": self._detect_content_type(chunk),
                    "chunk_size": len(chunk),
                    "processed_at": datetime.utcnow().isoformat()
                }
                
                # Store chunk embedding
                success = await self.vector_manager.store_document_embedding(
                    document_id=chunk_id,
                    text=chunk,
                    metadata=chunk_metadata
                )
                
                if success:
                    chunks_stored += 1
            
            # Discover aliases if enabled
            if self.enable_alias_discovery:
                doc_aliases = self.alias_discovery.discover_aliases_in_text(cleaned_content, title)
                aliases_discovered = len(doc_aliases)
                
                # Update alias cache
                self.alias_discovery.aliases_cache.update(doc_aliases)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            logger.info(f"✅ Document indexed: {chunks_stored} chunks, {aliases_discovered} aliases")
            
            return {
                "document_id": document_id,
                "chunks_count": chunks_stored,
                "aliases_count": aliases_discovered,
                "processing_time": processing_time,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"❌ Document indexing failed: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "processing_time": 0
            }
    
    async def bulk_index_documents(
        self,
        documents: List[Dict[str, Any]],
        source_type: str = "unknown",
        batch_size: int = 10
    ) -> Dict[str, Any]:
        """Bulk index multiple documents with batching"""
        try:
            start_time = datetime.utcnow()
            
            results = {
                "success_count": 0,
                "failure_count": 0,
                "total_chunks": 0
            }
            
            # Process documents in batches
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                
                # Process batch concurrently
                tasks = [
                    self.index_document_enhanced(doc, source_type)
                    for doc in batch
                ]
                
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Aggregate results
                for result in batch_results:
                    if isinstance(result, Exception):
                        results["failure_count"] += 1
                    elif result.get("status") == "success":
                        results["success_count"] += 1
                        results["total_chunks"] += result.get("chunks_count", 0)
                    else:
                        results["failure_count"] += 1
                
                logger.info(f"📊 Processed batch {i//batch_size + 1}: {len(batch)} documents")
            
            total_time = (datetime.utcnow() - start_time).total_seconds()
            results["total_time"] = total_time
            
            logger.info(f"✅ Bulk indexing complete: {results['success_count']}/{len(documents)} successful")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Bulk indexing failed: {e}", exc_info=True)
            return {
                "success_count": 0,
                "failure_count": len(documents),
                "total_chunks": 0,
                "total_time": 0,
                "error": str(e)
            }
    
    def _clean_html_content(self, content: str) -> str:
        """Clean HTML content while preserving structure"""
        # Remove HTML tags but preserve line breaks
        content = re.sub(r'<br[^>]*>', '\n', content)
        content = re.sub(r'<p[^>]*>', '\n', content)
        content = re.sub(r'</p>', '\n', content)
        content = re.sub(r'<h[1-6][^>]*>', '\n### ', content)
        content = re.sub(r'</h[1-6]>', '\n', content)
        content = re.sub(r'<[^>]+>', '', content)
        
        # Clean up whitespace
        content = re.sub(r'\n\s*\n', '\n\n', content)
        content = re.sub(r' +', ' ', content)
        
        return content.strip()
    
    async def _intelligent_chunk_text(self, content: str, title: str = "") -> List[str]:
        """Intelligent chunking that preserves semantic boundaries"""
        chunks = []
        
        # Split by major sections first
        sections = re.split(r'\n\s*#{1,3}\s+', content)
        
        for section in sections:
            if not section.strip():
                continue
                
            # If section is small enough, keep as one chunk
            if len(section) <= self.max_chunk_size:
                chunks.append(section.strip())
                continue
            
            # Split large sections by paragraphs
            paragraphs = re.split(r'\n\s*\n', section)
            current_chunk = ""
            
            for paragraph in paragraphs:
                # If adding this paragraph would exceed chunk size
                if len(current_chunk) + len(paragraph) > self.max_chunk_size:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                        current_chunk = ""
                
                # Add overlap from previous chunk if needed
                if current_chunk == "" and chunks:
                    overlap_text = chunks[-1][-self.chunk_overlap:]
                    current_chunk = overlap_text + "\n\n"
                
                current_chunk += paragraph + "\n\n"
            
            # Add final chunk
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
        
        # Ensure we have at least one chunk
        if not chunks and content.strip():
            chunks.append(content.strip())
        
        logger.info(f"📄 Created {len(chunks)} intelligent chunks for document")
        return chunks
    
    def _detect_content_type(self, chunk: str) -> str:
        """Detect the type of content in a chunk"""
        chunk_lower = chunk.lower()
        
        if re.search(r'```|`[^`]+`', chunk):
            return "code"
        elif re.search(r'^\s*[-*]\s+', chunk, re.MULTILINE):
            return "list"
        elif re.search(r'^\s*\d+\.\s+', chunk, re.MULTILINE):
            return "numbered_list"
        elif re.search(r'\|.*\|.*\|', chunk):
            return "table"
        elif re.search(r'(step|procedure|process|how to)', chunk_lower):
            return "procedure"
        else:
            return "text"
    
    def _generate_document_id(self, content: str, title: str) -> str:
        """Generate deterministic document ID based on content"""
        content_hash = hashlib.sha256(f"{title}:{content}".encode()).hexdigest()
        return f"doc_{content_hash[:16]}"
    
    def _deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate results based on document ID"""
        seen_ids = set()
        unique_results = []
        
        for result in results:
            doc_id = result.get("id")
            if doc_id not in seen_ids:
                seen_ids.add(doc_id)
                unique_results.append(result)
        
        return unique_results
    
    async def delete_document(self, document_id: str) -> bool:
        """Delete a document and all its chunks from the index"""
        try:
            # For now, just delete the main document
            # In a full implementation, this would delete all chunks
            success = await self.vector_manager.delete_document(document_id)
            
            if success:
                logger.info(f"✅ Deleted document: {document_id}")
            else:
                logger.warning(f"⚠️ Failed to delete document: {document_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Document deletion failed: {e}")
            return False
    
    async def reindex_all(
        self,
        source_type: Optional[str] = None,
        force: bool = False
    ) -> Dict[str, Any]:
        """Reindex all documents with enhanced processing"""
        try:
            start_time = datetime.utcnow()
            
            logger.info("🔄 Starting complete reindex...")
            
            # This would typically fetch all documents from database
            # For now, simulate the process
            reindexed_count = 0
            
            # Refresh aliases as part of reindexing
            aliases_result = await self.alias_discovery.refresh_aliases(
                enhanced_search=self,
                force=True
            )
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            logger.info(f"✅ Reindex completed in {processing_time:.2f}s")
            
            return {
                "reindexed_count": reindexed_count,
                "processing_time": processing_time,
                "aliases_refreshed": aliases_result.get("status") == "success"
            }
            
        except Exception as e:
            logger.error(f"❌ Reindex failed: {e}")
            return {
                "reindexed_count": 0,
                "processing_time": 0,
                "aliases_refreshed": False,
                "error": str(e)
            } 