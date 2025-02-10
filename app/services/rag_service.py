"""RAG (Retrieval-Augmented Generation) service.

This module implements the core RAG functionality:
- Document context retrieval from vector store
- Query embedding and semantic search
- Context-aware prompt construction
- LLM response generation with streaming

The RAG pipeline combines retrieved document context with the user's query
to generate more accurate and contextually relevant responses.
"""

from typing import List, Dict, Any, AsyncGenerator
from app.services.vector_store import vector_store
from app.services.embedding_service import generate_embeddings
from app.core.config import settings
from openai import AsyncOpenAI
from app.core.logging import logger
import json

class RAGService:
    """Service for handling RAG (Retrieval-Augmented Generation) operations.
    
    This class manages the entire RAG pipeline, from context retrieval to
    response generation. It uses vector similarity search to find relevant
    document chunks and incorporates them into LLM prompts.
    
    Attributes:
        client: AsyncOpenAI client for API calls
        max_context_chunks: Maximum number of document chunks to include in context
    """

    def __init__(self):
        """Initialize RAG service with OpenAI client and configuration."""
        self.client = AsyncOpenAI(api_key=settings.LLM_API_KEY)
        self.max_context_chunks = 5  # Limit context window for performance
        
    async def get_relevant_context(self, query: str) -> List[str]:
        """Retrieve relevant document chunks for the query.
        
        Args:
            query: User's question or input text
            
        Returns:
            List of relevant text chunks from documents
            
        Process:
            1. Generate embedding for query
            2. Perform similarity search in vector store
            3. Extract and return text from matching chunks
        """
        query_embedding = await generate_embeddings([query])
        
        relevant_chunks = await vector_store.search_relevant_docs(
            query_embedding[0],
            limit=self.max_context_chunks
        )
        
        return [chunk["text"] for chunk in relevant_chunks]
    
    def construct_prompt(self, query: str, context_chunks: List[str]) -> str:
        """Construct LLM prompt with query and context.
        
        Args:
            query: User's question
            context_chunks: Retrieved relevant document chunks
            
        Returns:
            Formatted prompt string combining context and query
            
        The prompt instructs the LLM to:
        1. Use provided context to answer
        2. Admit when information is insufficient
        3. Stay focused on the context
        """
        context_str = "\n\n".join(context_chunks)
        
        return f"""Answer the question based on the following context. 
If the answer cannot be found in the context, say "I don't have enough information to answer that."

Context:
{context_str}

Question: {query}

Answer:"""
    
    async def generate_response(
        self, 
        query: str, 
        chat_history: List[Dict[str, Any]] = None
    ) -> AsyncGenerator[str, None]:
        """Generate response using complete RAG pipeline.
        
        Args:
            query: User's question
            chat_history: Optional list of previous chat messages
            
        Returns:
            Streaming response from LLM
            
        Process:
            1. Retrieve relevant context
            2. Construct prompt with context
            3. Include recent chat history
            4. Generate streaming response
            
        Raises:
            Exception: If any step in the pipeline fails
        """
        try:
            context_chunks = await self.get_relevant_context(query)
            
            messages = []
            if chat_history:
                # Include limited recent history for context
                messages.extend([
                    {"role": msg["role"], "content": msg["content"]}
                    for msg in chat_history[-5:]
                ])
            
            messages.extend([
                {
                    "role": "system",
                    "content": self.construct_prompt(query, context_chunks)
                },
                {
                    "role": "user",
                    "content": query
                }
            ])
            
            response = await self.client.chat.completions.create(
                model=settings.LLM_MODEL_NAME,
                messages=messages,
                temperature=settings.TEMPERATURE,
                max_tokens=settings.MAX_TOKENS,
                stream=True
            )
            
            return response
            
        except Exception as e:
            logger.error(
                "RAG pipeline error",
                extra={
                    "error": str(e),
                    "query": query,
                    "context_chunks": len(context_chunks)
                }
            )
            raise
    
    async def process_stream(self, stream) -> AsyncGenerator[str, None]:
        """Process streaming response from LLM.
        
        Args:
            stream: AsyncGenerator from OpenAI API
            
        Yields:
            Individual text chunks from the response
            
        This method handles the streaming response and yields
        text chunks as they become available, enabling real-time
        response display.
        """
        collected_chunks = []
        async for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                collected_chunks.append(content)
                yield content

# Create singleton instance
rag_service = RAGService() 