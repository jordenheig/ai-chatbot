"""RAG (Retrieval-Augmented Generation) service.

This module handles:
- Context retrieval from vector store
- Query embedding generation
- LLM prompt construction with context
- Response generation
"""

from typing import List, Dict, Any
from app.services.vector_store import vector_store
from app.services.embedding_service import generate_embeddings
from app.core.config import settings
from openai import AsyncOpenAI
import json

class RAGService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.LLM_API_KEY)
        self.max_context_chunks = 5
        
    async def get_relevant_context(self, query: str) -> List[str]:
        """Retrieve relevant document chunks for the query."""
        # Generate query embedding
        query_embedding = await generate_embeddings([query])
        
        # Search vector store
        relevant_chunks = await vector_store.search_relevant_docs(
            query_embedding[0],
            limit=self.max_context_chunks
        )
        
        return [chunk["text"] for chunk in relevant_chunks]
    
    def construct_prompt(self, query: str, context_chunks: List[str]) -> str:
        """Construct prompt with query and context."""
        context_str = "\n\n".join(context_chunks)
        
        return f"""Answer the question based on the following context. 
If the answer cannot be found in the context, say "I don't have enough information to answer that."

Context:
{context_str}

Question: {query}

Answer:"""
    
    async def generate_response(self, query: str, chat_history: List[Dict[str, Any]] = None) -> str:
        """Generate response using RAG pipeline."""
        try:
            # Get relevant context
            context_chunks = await self.get_relevant_context(query)
            
            # Construct messages array with chat history
            messages = []
            if chat_history:
                messages.extend([
                    {"role": msg["role"], "content": msg["content"]}
                    for msg in chat_history[-5:]  # Include last 5 messages for context
                ])
            
            # Add system message with context
            messages.append({
                "role": "system",
                "content": self.construct_prompt(query, context_chunks)
            })
            
            # Add user query
            messages.append({
                "role": "user",
                "content": query
            })
            
            # Generate response
            response = await self.client.chat.completions.create(
                model=settings.LLM_MODEL_NAME,
                messages=messages,
                temperature=0.7,
                max_tokens=1000,
                stream=True
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error in RAG pipeline: {str(e)}")
            raise
    
    async def process_stream(self, stream):
        """Process streaming response from LLM."""
        collected_chunks = []
        async for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                collected_chunks.append(content)
                yield content

rag_service = RAGService() 