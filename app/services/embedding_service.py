"""Text embedding service for the RAG Chatbot.

This module handles:
- Text embedding generation
- Embedding model management
- Batch processing of text chunks
"""

from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer
from app.core.config import settings
from app.core.logging import logger

class EmbeddingService:
    """Service for generating text embeddings.
    
    This class manages the embedding model and provides methods
    for generating embeddings from text chunks.
    
    Attributes:
        model: SentenceTransformer model instance
        embedding_dim: Dimension of generated embeddings
    """
    
    def __init__(self):
        """Initialize embedding service with pre-trained model."""
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of text chunks.
        
        Args:
            texts: List of text chunks to embed
            
        Returns:
            List of embedding vectors
            
        Raises:
            EmbeddingError: If embedding generation fails
        """
        try:
            embeddings = self.model.encode(texts)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise

# Create singleton instance
embedding_service = EmbeddingService()

async def generate_embeddings(texts: List[str]) -> List[np.ndarray]:
    """Helper function to generate embeddings"""
    return await embedding_service.generate_embeddings(texts) 