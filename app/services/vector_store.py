from typing import List, Dict, Any
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http import models
from app.core.config import settings
from app.core.logging import logger

class VectorStore:
    def __init__(self):
        self.client = QdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT
        )
        self.collection_name = "documents"
        self._ensure_collection()
    
    def _ensure_collection(self):
        """Ensure the collection exists with proper configuration"""
        try:
            self.client.get_collection(self.collection_name)
        except:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=384,  # Dimension of all-MiniLM-L6-v2 embeddings
                    distance=models.Distance.COSINE
                )
            )
    
    async def store_chunks(
        self,
        document_id: int,
        chunks: List[str],
        embeddings: List[List[float]]
    ):
        """Store document chunks and their embeddings"""
        try:
            points = [
                models.PointStruct(
                    id=i,
                    vector=embedding,
                    payload={
                        "document_id": document_id,
                        "chunk_index": i,
                        "text": chunk
                    }
                )
                for i, (chunk, embedding) in enumerate(zip(chunks, embeddings))
            ]
            
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
        except Exception as e:
            logger.error(f"Error storing chunks in vector store: {str(e)}")
            raise
    
    async def search_similar(
        self,
        query_embedding: List[float],
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for similar chunks"""
        try:
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit
            )
            
            return [
                {
                    "text": hit.payload["text"],
                    "document_id": hit.payload["document_id"],
                    "score": hit.score
                }
                for hit in results
            ]
            
        except Exception as e:
            logger.error(f"Error searching vector store: {str(e)}")
            raise

# Create singleton instance
vector_store = VectorStore()

async def store_document_chunks(
    document_id: int,
    chunks: List[str],
    embeddings: List[List[float]]
):
    """Helper function to store document chunks"""
    return await vector_store.store_chunks(document_id, chunks, embeddings)

async def search_relevant_docs(query: str) -> List[Dict[str, Any]]:
    """Helper function to search relevant documents"""
    # Generate embedding for query
    query_embedding = await generate_embeddings([query])
    return await vector_store.search_similar(query_embedding[0]) 