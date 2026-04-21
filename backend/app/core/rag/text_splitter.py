"""Intelligent text splitting for RAG"""

from typing import List
from langchain.text_splitter import RecursiveCharacterTextSplitter
import tiktoken

from app.core.config import settings


class SmartTextSplitter:
    """Split text into chunks with overlap"""
    
    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None,
        encoding_name: str = "cl100k_base"  # GPT-4 encoding
    ):
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
        self.encoding = tiktoken.get_encoding(encoding_name)
        
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=self._token_length,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
    
    def _token_length(self, text: str) -> int:
        """Count tokens using tiktoken"""
        return len(self.encoding.encode(text))
    
    def split_text(self, text: str) -> List[str]:
        """
        Split text into chunks
        
        Args:
            text: Text to split
            
        Returns:
            List of text chunks
        """
        return self.splitter.split_text(text)
    
    def split_documents(self, texts: List[str]) -> List[str]:
        """Split multiple documents"""
        all_chunks = []
        for text in texts:
            chunks = self.split_text(text)
            all_chunks.extend(chunks)
        return all_chunks


# Global instance
text_splitter = SmartTextSplitter()
