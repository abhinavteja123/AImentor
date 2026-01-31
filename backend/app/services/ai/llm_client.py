"""
LLM Client - DeepSeek Integration
"""

import json
import logging
from typing import Optional, Dict, Any, List
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings

logger = logging.getLogger(__name__)


class LLMClient:
    """
    LLM Client using DeepSeek API.
    DeepSeek is compatible with OpenAI API format.
    """
    
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL
        )
        self.model = settings.DEEPSEEK_MODEL
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def generate_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        response_format: Optional[str] = None
    ) -> str:
        """
        Generate a completion using DeepSeek.
        
        Args:
            system_prompt: System message for context
            user_prompt: User message/query
            temperature: Creativity (0-1)
            max_tokens: Maximum response length
            response_format: "json" for JSON responses
            
        Returns:
            Generated text response
        """
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            # DeepSeek supports JSON mode
            if response_format == "json":
                kwargs["response_format"] = {"type": "json_object"}
            
            response = await self.client.chat.completions.create(**kwargs)
            
            content = response.choices[0].message.content
            
            logger.debug(f"LLM Response: {content[:200]}...")
            
            return content
            
        except Exception as e:
            logger.error(f"LLM Error: {str(e)}")
            raise
    
    async def generate_with_context(
        self,
        prompt: str,
        context: Dict[str, Any],
        temperature: float = 0.7
    ) -> str:
        """
        Generate completion with additional context.
        """
        system_prompt = """You are an AI career mentor assistant. 
        Use the provided context to give personalized, helpful responses.
        Be encouraging, specific, and actionable in your advice."""
        
        context_str = json.dumps(context, indent=2, default=str)
        user_prompt = f"""Context:
{context_str}

Query: {prompt}

Provide a helpful, personalized response."""
        
        return await self.generate_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature
        )
    
    async def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Generate a JSON response.
        """
        response = await self.generate_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            response_format="json"
        )
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            start = response.find("{")
            end = response.rfind("}") + 1
            if start != -1 and end > start:
                return json.loads(response[start:end])
            raise ValueError("Could not parse JSON response")
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1500
    ) -> str:
        """
        Multi-turn chat completion.
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Chat Error: {str(e)}")
            raise


# Singleton instance
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Get LLM client singleton."""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
