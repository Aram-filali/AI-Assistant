"""Load documents from various sources"""

import os
from typing import List, Dict, Optional
from pathlib import Path
import PyPDF2
import docx
import markdown
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)


class DocumentLoader:
    """Load and extract text from various document formats"""
    
    SUPPORTED_FORMATS = {
        '.pdf': 'load_pdf',
        '.txt': 'load_text',
        '.md': 'load_markdown',
        '.docx': 'load_docx',
        '.html': 'load_html',
    }
    
    def load_file(self, file_path: str) -> Dict[str, any]:
        """
        Load file and extract text
        
        Args:
            file_path: Path to file
            
        Returns:
            Dict with content, metadata
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        extension = path.suffix.lower()
        
        if extension not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported format: {extension}. "
                f"Supported: {list(self.SUPPORTED_FORMATS.keys())}"
            )
        
        loader_method = getattr(self, self.SUPPORTED_FORMATS[extension])
        content = loader_method(file_path)
        
        metadata = {
            'filename': path.name,
            'extension': extension,
            'size': path.stat().st_size,
            'path': str(path.absolute())
        }
        
        return {
            'content': content,
            'metadata': metadata
        }
    
    def load_pdf(self, file_path: str) -> str:
        """Extract text from PDF"""
        try:
            text = []
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    if page_text.strip():
                        text.append(f"[Page {page_num + 1}]\n{page_text}")
            
            return "\n\n".join(text)
        except Exception as e:
            logger.error(f"Error loading PDF {file_path}: {e}")
            raise
    
    def load_text(self, file_path: str) -> str:
        """Load plain text file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except UnicodeDecodeError:
            # Try with different encoding
            with open(file_path, 'r', encoding='latin-1') as file:
                return file.read()
    
    def load_markdown(self, file_path: str) -> str:
        """Load markdown and convert to text"""
        text = self.load_text(file_path)
        # Convert markdown to HTML then extract text
        html = markdown.markdown(text)
        soup = BeautifulSoup(html, 'html.parser')
        return soup.get_text(separator='\n')
    
    def load_docx(self, file_path: str) -> str:
        """Extract text from DOCX"""
        try:
            doc = docx.Document(file_path)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            return "\n\n".join(paragraphs)
        except Exception as e:
            logger.error(f"Error loading DOCX {file_path}: {e}")
            raise
    
    def load_html(self, file_path: str) -> str:
        """Extract text from HTML"""
        html = self.load_text(file_path)
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        return soup.get_text(separator='\n')
    
    def load_from_url(self, url: str) -> Dict[str, any]:
        """
        Load content from URL
        
        Args:
            url: URL to fetch
            
        Returns:
            Dict with content, metadata
        """
        import httpx
        
        try:
            response = httpx.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'footer', 'header']):
                element.decompose()
            
            content = soup.get_text(separator='\n')
            
            # Clean up whitespace
            lines = [line.strip() for line in content.split('\n')]
            content = '\n'.join(line for line in lines if line)
            
            metadata = {
                'url': url,
                'title': soup.title.string if soup.title else url,
                'source': 'web'
            }
            
            return {
                'content': content,
                'metadata': metadata
            }
        except Exception as e:
            logger.error(f"Error loading URL {url}: {e}")
            raise


# Global instance
document_loader = DocumentLoader()
