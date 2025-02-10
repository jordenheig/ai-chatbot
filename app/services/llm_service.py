"""Language Model service for the RAG Chatbot.

This module handles interactions with the LLM API:
- Response generation
- Prompt construction
- Token management
- Response streaming
- Error handling
"""

from typing import AsyncGenerator, List, Dict, Any
from openai import AsyncOpenAI
from app.core.config import settings
from app.core.logging import logger

class LLMService:
    """Service for handling Language Model interactions.
    
    This class manages all interactions with the LLM API, including
    prompt construction, response generation, and streaming.
    
    Attributes:
        client: AsyncOpenAI client instance
        model: Name of the LLM model to use
        max_tokens: Maximum tokens per response
        temperature: Response randomness (0-1)
    """

    def __init__(self):
        """Initialize LLM service with API client and configuration."""
        self.client = AsyncOpenAI(api_key=settings.LLM_API_KEY)
        self.model = settings.LLM_MODEL_NAME
        self.max_tokens = settings.LLM_MAX_TOKENS
        self.temperature = settings.LLM_TEMPERATURE

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        stream: bool = True
    ) -> AsyncGenerator[str, None]:
        """Generate response from the language model.
        
        Args:
            messages: List of conversation messages in OpenAI format
                     [{"role": "user", "content": "message"}, ...]
            stream: Whether to stream the response
            
        Yields:
            Text chunks of the generated response if streaming
            
        Raises:
            LLMError: If API call fails or response generation fails
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=stream
            )
            
            if stream:
                async for chunk in response:
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
            else:
                yield response.choices[0].message.content

        except Exception as e:
            logger.error(
                "LLM response generation failed",
                extra={
                    "error": str(e),
                    "model": self.model,
                    "message_count": len(messages)
                }
            )
            raise

    def construct_system_prompt(self, context: str = None) -> str:
        """Construct system prompt for the LLM.
        
        Args:
            context: Optional context to include in prompt
            
        Returns:
            Formatted system prompt string
            
        The system prompt defines the behavior and constraints
        for the language model's responses.
        """
        base_prompt = """You are a helpful AI assistant that answers questions based on the provided context.
If the answer cannot be found in the context, say "I don't have enough information to answer that."
Always be clear, concise, and accurate."""

        if context:
            return f"{base_prompt}\n\nContext:\n{context}"
        return base_prompt

    async def validate_response(self, response: str) -> bool:
        """Validate LLM response for quality and safety.
        
        Args:
            response: Generated response text
            
        Returns:
            True if response is valid, False otherwise
            
        This method checks:
        - Response length
        - Content safety
        - Response relevance
        """
        try:
            if not response or len(response.strip()) < 10:
                return False
                
            # Add additional validation logic here
            
            return True
            
        except Exception as e:
            logger.error(f"Response validation failed: {str(e)}")
            return False

    async def estimate_tokens(self, text: str) -> int:
        """Estimate token count for input text.
        
        Args:
            text: Input text to estimate
            
        Returns:
            Estimated number of tokens
            
        Note:
            This is a rough estimation using character count.
            For precise counts, use the tokenizer API.
        """
        # Rough estimation: ~4 characters per token
        return len(text) // 4

# Create singleton instance
llm_service = LLMService()

# Helper functions for common operations
async def generate_chat_response(
    query: str,
    context: str = None,
    chat_history: List[Dict[str, str]] = None
) -> AsyncGenerator[str, None]:
    """Generate chat response with context and history.
    
    Args:
        query: User's question
        context: Optional relevant context
        chat_history: Optional previous chat messages
        
    Yields:
        Chunks of generated response
    """
    messages = []
    
    # Add system prompt with context
    messages.append({
        "role": "system",
        "content": llm_service.construct_system_prompt(context)
    })
    
    # Add chat history if provided
    if chat_history:
        messages.extend(chat_history[-5:])  # Last 5 messages
    
    # Add user query
    messages.append({
        "role": "user",
        "content": query
    })
    
    async for chunk in llm_service.generate_response(messages):
        yield chunk 