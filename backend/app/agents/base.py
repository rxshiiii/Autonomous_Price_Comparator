"""
Base agent class with GROQ LLM integration.
"""
import json
from typing import Any, Dict, Optional
from decimal import Decimal
import structlog
import asyncio
from groq import Groq
from app.config import settings


logger = structlog.get_logger()


class BaseAgent:
    """Base class for all AI agents."""

    def __init__(self):
        """Initialize GROQ client."""
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model_name = settings.GROQ_MODEL
        self.logger = logger.bind(agent=self.__class__.__name__)

    async def call_groq(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> Optional[str]:
        """
        Call GROQ API with a prompt and return response.

        Args:
            prompt: The prompt to send to GROQ
            temperature: Temperature for response generation (0-2)
            max_tokens: Maximum tokens in response

        Returns:
            Response text from GROQ or None if error
        """
        try:
            self.logger.debug("calling_groq", prompt_length=len(prompt))

            # Run GROQ call in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_tokens=max_tokens,
                ),
            )

            result = response.choices[0].message.content
            self.logger.debug("groq_response_received", response_length=len(result))
            return result

        except Exception as e:
            self.logger.error("groq_call_failed", error=str(e))
            return None

    async def call_groq_json(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> Optional[Dict[str, Any]]:
        """
        Call GROQ API and parse response as JSON.

        Args:
            prompt: The prompt to send to GROQ (should request JSON response)
            temperature: Temperature for response generation
            max_tokens: Maximum tokens in response

        Returns:
            Parsed JSON dict or None if error or invalid JSON
        """
        response = await self.call_groq(prompt, temperature, max_tokens)

        if not response:
            return None

        try:
            # Try to extract JSON from response
            # GROQ might include text before/after JSON
            start_idx = response.find("{")
            end_idx = response.rfind("}") + 1

            if start_idx == -1 or end_idx == 0:
                # Try with square brackets for arrays
                start_idx = response.find("[")
                end_idx = response.rfind("]") + 1

            if start_idx >= 0 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                parsed = json.loads(json_str)
                self.logger.debug("json_parsed_successfully")
                return parsed
            else:
                self.logger.error("no_json_found_in_response")
                return None

        except json.JSONDecodeError as e:
            self.logger.error("json_parse_error", error=str(e))
            return None

    def _format_price(self, price: Optional[Decimal]) -> str:
        """Format price for display in prompts."""
        if price is None:
            return "N/A"
        return f"₹{float(price):,.0f}"

    def _format_decimal(self, value: Optional[Decimal], decimals: int = 2) -> str:
        """Format decimal value for display."""
        if value is None:
            return "N/A"
        return f"{float(value):.{decimals}f}"
