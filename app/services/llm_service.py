from typing import List, Dict, Any, AsyncGenerator
from openai import AsyncOpenAI
from app.core.config import settings
from app.core.logging import logger

class LLMService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.LLM_API_KEY)
        self.model = settings.LLM_MODEL_NAME

    async def generate_response(
        self,
        query: str,
        context_docs: List[Dict[str, Any]]
    ) -> AsyncGenerator[str, None]:
        try:
            # Prepare context from relevant documents
            context = "\n".join([doc["text"] for doc in context_docs])
            
            # Prepare messages for chat completion
            messages = [
                {"role": "system", "content": "You are a helpful assistant. Use the provided context to answer questions accurately."},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
            ]
            
            # Create streaming response
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"Error generating LLM response: {str(e)}")
            raise

# Create singleton instance
llm_service = LLMService()

async def generate_response(
    query: str,
    context_docs: List[Dict[str, Any]]
) -> AsyncGenerator[str, None]:
    """Helper function to generate responses"""
    async for token in llm_service.generate_response(query, context_docs):
        yield token 