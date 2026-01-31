"""
LLM Client - Google Gemini Integration
"""

import json
import logging
from typing import Optional, Dict, Any, List
import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings

logger = logging.getLogger(__name__)


class LLMClient:
    """
    LLM Client using Google Gemini API.
    Uses gemini-2.0-flash-exp model for fast, efficient responses.
    """
    
    def __init__(self):
        # Configure Gemini API
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.model_name = "gemini-2.5-flash-preview-09-2025"
        
        # Generation config for better responses
        self.generation_config = {
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 2048,
        }
        
        # Safety settings (permissive for educational content)
        self.safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_NONE"
            },
        ]
    
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
        Generate a completion using Google Gemini.
        
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
            # Create model instance
            model = genai.GenerativeModel(
                model_name="gemini-2.5-flash-preview-09-2025",
                generation_config={
                    **self.generation_config,
                    "temperature": temperature,
                    "max_output_tokens": max_tokens,
                },
                safety_settings=self.safety_settings,
                system_instruction=system_prompt
            )
            
            # Add JSON instruction if needed
            if response_format == "json":
                user_prompt = f"{user_prompt}\n\nRespond with valid JSON only, no markdown formatting."
            
            # Generate response
            response = await model.generate_content_async(user_prompt)
            
            content = response.text
            
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
            # Clean response - remove markdown code blocks if present
            cleaned = response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
            
            return json.loads(cleaned)
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
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Creativity level
            max_tokens: Max response length
            
        Returns:
            Assistant's response
        """
        try:
            # Extract system message if present
            system_instruction = None
            chat_messages = []
            
            for msg in messages:
                if msg["role"] == "system":
                    system_instruction = msg["content"]
                elif msg["role"] == "user":
                    chat_messages.append({"role": "user", "parts": [msg["content"]]})
                elif msg["role"] == "assistant":
                    chat_messages.append({"role": "model", "parts": [msg["content"]]})
            
            # Create model
            model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config={
                    **self.generation_config,
                    "temperature": temperature,
                    "max_output_tokens": max_tokens,
                },
                safety_settings=self.safety_settings,
                system_instruction=system_instruction
            )
            
            # Start chat with history
            chat = model.start_chat(history=chat_messages[:-1] if len(chat_messages) > 1 else [])
            
            # Send last message
            last_message = chat_messages[-1]["parts"][0] if chat_messages else ""
            response = await chat.send_message_async(last_message)
            
            return response.text
            
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
