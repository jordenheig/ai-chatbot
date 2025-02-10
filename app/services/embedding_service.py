from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer
from app.core.config import settings
from app.core.logging import logger

class EmbeddingService:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
    
    async def generate_embeddings(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings for a list of text chunks"""
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