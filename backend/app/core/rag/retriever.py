"""Semantic retrieval using embeddings and FAISS"""

from typing import List, Dict, Optional
import logging

from app.core.rag.embedder import get_embedder
from app.core.rag.faiss_manager import faiss_manager

logger = logging.getLogger(__name__)


class SemanticRetriever:
    """Retrieve relevant chunks using semantic search"""
    
    def __init__(self):
        self.embedder = get_embedder()
        self.faiss_manager = faiss_manager
    
    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        min_score: Optional[float] = None
    ) -> List[Dict]:
        """
        Retrieve relevant chunks for query
        
        Args:
            query: Search query
            top_k: Number of results
            min_score: Minimum similarity score (optional)
            
        Returns:
            List of dicts with text, metadata, and score
        """
        try:
            # Generate query embedding
            logger.info(f"Retrieving for query: {query[:50]}...")
            query_embedding = self.embedder.embed_text(query)
            
            # Search FAISS
            results = self.faiss_manager.search(
                query_embedding=query_embedding,
                k=top_k
            )
            
            if not results:
                logger.warning("No results found")
                return []
            
            # Format results
            formatted_results = []
            for metadata, distance in results:
                # Convert distance to similarity score (lower distance = higher similarity)
                # Using exponential decay: score = exp(-distance)
                import math
                score = math.exp(-distance)
                
                # Filter by min_score if provided
                if min_score and score < min_score:
                    continue
                
                formatted_results.append({
                    'text': metadata.get('text', ''),
                    'metadata': metadata,
                    'score': score,
                    'distance': distance
                })
            
            logger.info(f"Retrieved {len(formatted_results)} chunks")
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error retrieving: {e}")
            raise
    
    def get_stats(self) -> Dict:
        """Get retriever statistics"""
        return self.faiss_manager.get_stats()


# Global instance
semantic_retriever = SemanticRetriever()
