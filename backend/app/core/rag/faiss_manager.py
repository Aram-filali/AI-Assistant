"""FAISS index management"""

import os
from typing import List, Tuple, Optional
import numpy as np
import faiss
import pickle
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class FAISSManager:
    """Manage FAISS vector index"""
    
    def __init__(self, index_path: str = "data/faiss_index"):
        self.index_path = Path(index_path)
        self.index_path.mkdir(parents=True, exist_ok=True)
        
        self.index_file = self.index_path / "index.faiss"
        self.metadata_file = self.index_path / "metadata.pkl"
        
        self.index: Optional[faiss.Index] = None
        self.metadata: List[dict] = []
        self.embedding_dim: Optional[int] = None
    
    def create_index(self, embedding_dim: int):
        """
        Create new FAISS index
        
        Args:
            embedding_dim: Dimension of embeddings
        """
        self.embedding_dim = embedding_dim
        
        # Use IndexFlatL2 for exact search (good for small datasets)
        # For large datasets, consider IndexIVFFlat or IndexHNSW
        self.index = faiss.IndexFlatL2(embedding_dim)
        
        logger.info(f"Created FAISS index with dimension {embedding_dim}")
    
    def add_embeddings(
        self,
        embeddings: np.ndarray,
        metadata: List[dict]
    ):
        """
        Add embeddings to index
        
        Args:
            embeddings: Numpy array of embeddings
            metadata: List of metadata dicts for each embedding
        """
        if self.index is None:
            raise ValueError("Index not created. Call create_index first.")
        
        if len(embeddings) != len(metadata):
            raise ValueError("Embeddings and metadata must have same length")
        
        # Ensure float32
        embeddings = embeddings.astype('float32')
        
        # Add to index
        start_id = self.index.ntotal
        self.index.add(embeddings)
        
        # Add IDs to metadata
        for i, meta in enumerate(metadata):
            meta['faiss_id'] = start_id + i
            self.metadata.append(meta)
        
        logger.info(f"Added {len(embeddings)} embeddings. Total: {self.index.ntotal}")
    
    def search(
        self,
        query_embedding: np.ndarray,
        k: int = 5
    ) -> List[Tuple[dict, float]]:
        """
        Search for similar embeddings
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            
        Returns:
            List of (metadata, distance) tuples
        """
        if self.index is None or self.index.ntotal == 0:
            logger.warning("Index is empty")
            return []
        
        # Ensure shape and type
        query_embedding = query_embedding.astype('float32').reshape(1, -1)
        
        # Search
        distances, indices = self.index.search(query_embedding, min(k, self.index.ntotal))
        
        # Get results
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx < len(self.metadata):
                results.append((self.metadata[idx], float(distance)))
        
        return results
    
    def save(self):
        """Save index and metadata to disk"""
        if self.index is None:
            raise ValueError("No index to save")
        
        # Save FAISS index
        faiss.write_index(self.index, str(self.index_file))
        
        # Save metadata
        with open(self.metadata_file, 'wb') as f:
            pickle.dump({
                'metadata': self.metadata,
                'embedding_dim': self.embedding_dim
            }, f)
        
        logger.info(f"Saved index with {self.index.ntotal} vectors")
    
    def load(self):
        """Load index and metadata from disk"""
        if not self.index_file.exists():
            logger.warning("No saved index found")
            return False
        
        try:
            # Load FAISS index
            self.index = faiss.read_index(str(self.index_file))
            
            # Load metadata
            with open(self.metadata_file, 'rb') as f:
                data = pickle.load(f)
                self.metadata = data['metadata']
                self.embedding_dim = data['embedding_dim']
            
            logger.info(f"Loaded index with {self.index.ntotal} vectors")
            return True
        except Exception as e:
            logger.error(f"Error loading index: {e}")
            return False
    
    def clear(self):
        """Clear index and metadata"""
        self.index = None
        self.metadata = []
        self.embedding_dim = None
        logger.info("Cleared index")
    
    def get_stats(self) -> dict:
        """Get index statistics"""
        return {
            'total_vectors': self.index.ntotal if self.index else 0,
            'embedding_dim': self.embedding_dim,
            'total_documents': len(set(m.get('document_id') for m in self.metadata))
        }


# Global instance
faiss_manager = FAISSManager()
