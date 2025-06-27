from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional
import logging

from core.database import get_db
from services.enhanced_search import EnhancedDocumentationService
from services.vector_manager import VectorStoreManager
from services.alias_discovery import SmartAliasDiscovery

logger = logging.getLogger(__name__)
router = APIRouter()

# Global service instances (will be initialized in main.py)
enhanced_search = None
vector_manager = None
alias_discovery = None

@router.post("/search")
async def semantic_search(
    query: str = Body(..., embed=True),
    max_results: int = Body(10, embed=True),
    min_confidence: float = Body(0.7, embed=True),
    source_types: Optional[List[str]] = Body(None, embed=True),
    context_optimization: Optional[Dict[str, Any]] = Body(None, embed=True),
    user_persona: Optional[Dict[str, Any]] = Body(None, embed=True),
    adaptive_recommendations: Optional[Dict[str, Any]] = Body(None, embed=True),
    db: AsyncSession = Depends(get_db)
):
    """Enhanced semantic search with adaptive context optimization"""
    global enhanced_search, vector_manager
    try:
        logger.info(f"🔍 Search request: '{query[:50]}{'...' if len(query) > 50 else ''}'")
        
        optimized_max_results = max_results
        optimized_confidence = min_confidence
        query_expansion_enabled = True
        
        if adaptive_recommendations and adaptive_recommendations.get("confidence", 0) > 0.5:
            logger.info(f"🧠 Applying adaptive optimization: confidence {adaptive_recommendations.get('confidence', 0):.2f}")
            
            context_opts = context_optimization or adaptive_recommendations.get("context_optimization", {})
            
            relevance_score = context_opts.get("context_relevance_score", 0.5)
            needs_more_context = context_opts.get("needs_more_context", False)
            optimization_level = context_opts.get("context_optimization", "medium")
            
            if needs_more_context or relevance_score < 0.6:
                optimized_max_results = min(max_results * 2, 20)
                optimized_confidence = max(min_confidence - 0.1, 0.5)
                query_expansion_enabled = True
                logger.info(f"🔍 Low relevance context detected - expanding search: results={optimized_max_results}, confidence={optimized_confidence}")
            
            elif relevance_score > 0.8:
                optimized_confidence = min(min_confidence + 0.1, 0.9)
                logger.info(f"🎯 High relevance context detected - precision search: confidence={optimized_confidence}")
            
            if user_persona and user_persona.get("personalization_level") == "high":
                expertise_areas = user_persona.get("user_expertise_areas", [])
                if expertise_areas:
                    optimized_confidence = min(optimized_confidence + 0.05, 0.95)
                    logger.info(f"👨‍💻 Expert user detected in {len(expertise_areas)} areas - increasing precision")
        
        if not enhanced_search:
            enhanced_search = EnhancedDocumentationService(db=db)
        
        if not vector_manager:
            vector_manager = VectorStoreManager()
        
        if query_expansion_enabled and hasattr(enhanced_search, 'search_with_aliases'):
            results = await enhanced_search.search_with_aliases(
                query=query,
                max_results=optimized_max_results,
                min_confidence=optimized_confidence,
                source_types=source_types
            )
        else:
            results = await vector_manager.semantic_search(
                query=query,
                limit=optimized_max_results,
                score_threshold=optimized_confidence,
                filters={"source_type": source_types[0]} if source_types else None
            )
        
        optimization_metadata = {}
        if adaptive_recommendations and adaptive_recommendations.get("confidence", 0) > 0.5:
            optimization_metadata = {
                "adaptive_optimization_applied": True,
                "optimization_confidence": adaptive_recommendations.get("confidence", 0),
                "context_relevance_score": context_optimization.get("context_relevance_score", 0.5) if context_optimization else 0.5,
                "search_expansion": optimized_max_results > max_results,
                "confidence_adjustment": optimized_confidence != min_confidence,
                "suggested_context_types": context_optimization.get("suggested_context_types", []) if context_optimization else []
            }
        
        formatted_results = []
        for result in results:
            formatted_result = {
                "id": result.get("id", ""),
                "title": result.get("title", result.get("metadata", {}).get("title", "Untitled")),
                "content": result.get("text", result.get("content", "")),
                "score": result.get("score", 0.0),
                "source_type": result.get("source_type", result.get("metadata", {}).get("source_type", "unknown")),
                "url": result.get("url", result.get("metadata", {}).get("url", "")),
                "matched_query": result.get("matched_query", query),
                "alias_expanded": result.get("alias_expanded", False)
            }
            formatted_results.append(formatted_result)
        
        logger.info(f"✅ Found {len(formatted_results)} results with adaptive optimization")
        
        return {
            "results": formatted_results,
            "query": query,
            "total_results": len(formatted_results),
            "search_metadata": {
                "max_results_requested": max_results,
                "min_confidence_requested": min_confidence,
                "source_types": source_types,
                "actual_results_limit": optimized_max_results,
                "actual_confidence_threshold": optimized_confidence,
                "optimization_metadata": optimization_metadata
            }
        }
    except Exception as e:
        logger.error(f"Search error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.post("/index")
async def index_document(
    document_data: Dict[str, Any] = Body(...),
    source_type: str = Body("unknown"),
    force_reindex: bool = Body(False),
    db: AsyncSession = Depends(get_db)
):
    """Index a single document with enhanced processing"""
    global enhanced_search
    try:
        if not enhanced_search:
            enhanced_search = EnhancedDocumentationService(db=db)
        
        # Enhanced document indexing
        result = await enhanced_search.index_document_enhanced(
            document_data=document_data,
            source_type=source_type,
            force_reindex=force_reindex
        )
        
        return {
            "status": "success",
            "document_id": result.get("document_id"),
            "chunks_created": result.get("chunks_count", 0),
            "aliases_discovered": result.get("aliases_count", 0),
            "processing_time": result.get("processing_time", 0)
        }
    except Exception as e:
        logger.error(f"Indexing error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")

@router.post("/index/bulk")
async def bulk_index_documents(
    documents: List[Dict[str, Any]] = Body(...),
    source_type: str = Body("unknown"),
    batch_size: int = Body(10),
    db: AsyncSession = Depends(get_db)
):
    """Bulk index multiple documents"""
    global enhanced_search
    try:
        if not enhanced_search:
            enhanced_search = EnhancedDocumentationService(db=db)
        
        results = await enhanced_search.bulk_index_documents(
            documents=documents,
            source_type=source_type,
            batch_size=batch_size
        )
        
        return {
            "status": "success",
            "documents_processed": len(documents),
            "successful_indexing": results.get("success_count", 0),
            "failed_indexing": results.get("failure_count", 0),
            "total_chunks": results.get("total_chunks", 0),
            "processing_time": results.get("total_time", 0)
        }
    except Exception as e:
        logger.error(f"Bulk indexing error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Bulk indexing failed: {str(e)}")

@router.get("/aliases")
async def get_discovered_aliases():
    """Get all discovered semantic aliases"""
    global alias_discovery
    try:
        if not alias_discovery:
            alias_discovery = SmartAliasDiscovery()
        
        aliases = await alias_discovery.get_all_aliases()
        
        return {
            "aliases_count": len(aliases),
            "aliases": aliases,
            "cache_status": alias_discovery.get_cache_status(),
            "last_refresh": alias_discovery.get_last_refresh_time()
        }
    except Exception as e:
        logger.error(f"Aliases retrieval error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get aliases: {str(e)}")

@router.post("/aliases/refresh")
async def refresh_aliases(
    force: bool = Body(False, embed=True),
    db: AsyncSession = Depends(get_db)
):
    """Refresh semantic alias discovery"""
    global alias_discovery, enhanced_search
    try:
        if not alias_discovery:
            alias_discovery = SmartAliasDiscovery()
        
        if not enhanced_search:
            enhanced_search = EnhancedDocumentationService(db=db)
        
        # Trigger alias refresh
        result = await alias_discovery.refresh_aliases(
            enhanced_search=enhanced_search,
            force=force
        )
        
        return {
            "status": "success",
            "aliases_discovered": result.get("new_aliases", 0),
            "aliases_updated": result.get("updated_aliases", 0),
            "processing_time": result.get("processing_time", 0),
            "next_refresh": result.get("next_refresh")
        }
    except Exception as e:
        logger.error(f"Alias refresh error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Alias refresh failed: {str(e)}")

@router.get("/collections")
async def get_collections():
    """Get Qdrant collection information"""
    global vector_manager
    try:
        if not vector_manager:
            vector_manager = VectorStoreManager()
        
        collections = await vector_manager.get_collections_info()
        
        return {
            "collections": collections,
            "status": "active",
            "vector_dimensions": 1536
        }
    except Exception as e:
        logger.error(f"Collections error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get collections: {str(e)}")

@router.post("/collections/create")
async def create_collection(
    collection_name: str = Body(..., embed=True),
    vector_size: int = Body(1536, embed=True)
):
    """Create a new Qdrant collection"""
    global vector_manager
    try:
        if not vector_manager:
            vector_manager = VectorStoreManager()
        
        result = await vector_manager.create_collection(
            collection_name=collection_name,
            vector_size=vector_size
        )
        
        return {
            "status": "success",
            "collection_name": collection_name,
            "vector_size": vector_size,
            "created": result
        }
    except Exception as e:
        logger.error(f"Collection creation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create collection: {str(e)}")

@router.get("/stats")
async def get_embedding_stats(db: AsyncSession = Depends(get_db)):
    """Get comprehensive embedding service statistics"""
    global vector_manager, alias_discovery
    try:
        # Get database stats
        async with db.begin():
            wiki_count_result = await db.execute("SELECT COUNT(*) FROM wikis")
            wiki_count = wiki_count_result.scalar()
            
            page_count_result = await db.execute("SELECT COUNT(*) FROM wiki_page_indexes")
            page_count = page_count_result.scalar()
        
        # Get vector store stats
        if not vector_manager:
            vector_manager = VectorStoreManager()
        
        vector_stats = await vector_manager.get_stats()
        
        # Get alias stats
        if not alias_discovery:
            alias_discovery = SmartAliasDiscovery()
        
        alias_stats = alias_discovery.get_stats()
        
        return {
            "database_stats": {
                "wikis_indexed": wiki_count,
                "pages_processed": page_count
            },
            "vector_stats": vector_stats,
            "alias_stats": alias_stats,
            "service_status": "operational"
        }
    except Exception as e:
        logger.error(f"Stats error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

@router.delete("/index/{document_id}")
async def delete_document(
    document_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a document from the index"""
    global enhanced_search
    try:
        if not enhanced_search:
            enhanced_search = EnhancedDocumentationService(db=db)
        
        result = await enhanced_search.delete_document(document_id)
        
        return {
            "status": "success",
            "document_id": document_id,
            "deleted": result
        }
    except Exception as e:
        logger.error(f"Document deletion error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")

@router.post("/reindex")
async def reindex_all(
    source_type: Optional[str] = Body(None, embed=True),
    force: bool = Body(False, embed=True),
    db: AsyncSession = Depends(get_db)
):
    """Reindex all documents with enhanced processing"""
    global enhanced_search
    try:
        if not enhanced_search:
            enhanced_search = EnhancedDocumentationService(db=db)
        
        result = await enhanced_search.reindex_all(
            source_type=source_type,
            force=force
        )
        
        return {
            "status": "success",
            "documents_reindexed": result.get("reindexed_count", 0),
            "processing_time": result.get("processing_time", 0),
            "aliases_refreshed": result.get("aliases_refreshed", False)
        }
    except Exception as e:
        logger.error(f"Reindex error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Reindex failed: {str(e)}") 