"""Text embedding using sentence-transformers"""

from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class TextEmbedder:
    """Generate embeddings for text using sentence-transformers"""
    
    def __init__(self, model_name: str = None):
        self.model_name = model_name or settings.EMBEDDING_MODEL
        logger.info(f"Loading embedding model: {self.model_name}")
        
        try:
            self.model = SentenceTransformer(self.model_name)
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
            logger.info(f"Model loaded. Embedding dimension: {self.embedding_dim}")
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise
    
    def embed_text(self, text: str) -> np.ndarray:
        """
        Generate embedding for single text
        
        Args:
            text: Text to embed
            
        Returns:
            Numpy array of embeddings
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        embedding = self.model.encode(
            text,
            convert_to_numpy=True,
            show_progress_bar=False
        )
        
        return embedding
    
    def embed_texts(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of texts to embed
            batch_size: Batch size for encoding
            
        Returns:
            Numpy array of embeddings (n_texts, embedding_dim)
        """
        if not texts:
            raise ValueError("Texts list cannot be empty")
        
        # Filter empty texts
        valid_texts = [t for t in texts if t and t.strip()]
        
        if not valid_texts:
            raise ValueError("No valid texts to embed")
        
        logger.info(f"Embedding {len(valid_texts)} texts...")
        
        embeddings = self.model.encode(
            valid_texts,
            batch_size=batch_size,
            convert_to_numpy=True,
            show_progress_bar=True
        )
        
        logger.info(f"Generated embeddings: {embeddings.shape}")
        
        return embeddings
    
    def get_embedding_dimension(self) -> int:
        """Get embedding dimension"""
        return self.embedding_dim


# Global instance (lazy loading)
_embedder_instance = None

def get_embedder() -> TextEmbedder:
    """Get global embedder instance"""
    global _embedder_instance
    if _embedder_instance is None:
        _embedder_instance = TextEmbedder()
    return _embedder_instance
