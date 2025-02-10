"""Vector store service for document embeddings.

This module handles:
- Storage and retrieval of document embeddings
- Vector index management and optimization
- Similarity search for relevant documents
"""

from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.http import models
from app.core.config import settings
from app.core.logging import logger
from app.worker.main import celery_app

class VectorStore:
    def __init__(self):
        self.client = QdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT
        )
        self.collection_name = "documents"
        self._ensure_collection()
    
    def _ensure_collection(self):
        """Ensure vector collection exists with proper configuration."""
        try:
            self.client.get_collection(self.collection_name)
        except:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=768,  # Embedding dimension
                    distance=models.Distance.COSINE
                )
            )
    
    async def store_document_chunks(
        self,
        document_id: int,
        chunks: List[str],
        embeddings: List[List[float]]
    ):
        """Store document chunks and their embeddings."""
        points = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            points.append(models.PointStruct(
                id=f"{document_id}_{i}",
                vector=embedding,
                payload={
                    "document_id": document_id,
                    "chunk_index": i,
                    "text": chunk
                }
            ))
        
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
    
    async def search_relevant_docs(
        self,
        query_embedding: List[float],
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for relevant document chunks."""
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=limit
        )
        return [hit.payload for hit in results]
    
    async def delete_document(self, document_id: int):
        """Delete all chunks for a document."""
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="document_id",
                            match=models.MatchValue(value=document_id)
                        )
                    ]
                )
            )
        )

@celery_app.task
def optimize_index():
    """Periodic task to optimize vector index."""
    try:
        store = VectorStore()
        store.client.optimize_index(
            collection_name=store.collection_name,
            optimization_params=models.OptimizeParams(
                max_segments_size=10000,
                max_segments_number=10
            )
        )
        logger.info("Vector index optimization completed")
    except Exception as e:
        logger.error(f"Error optimizing vector index: {str(e)}")
        raise

vector_store = VectorStore() 