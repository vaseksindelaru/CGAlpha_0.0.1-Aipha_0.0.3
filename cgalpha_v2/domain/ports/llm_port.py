"""
cgalpha.domain.ports.llm_port — Port for LLM text generation.

This port abstracts the external LLM provider.  The domain never knows
whether responses come from OpenAI, Ollama, or a test stub.

Implementations live in cgalpha.infrastructure.llm.
"""

from __future__ import annotations

from typing import Optional, Protocol, runtime_checkable


@runtime_checkable
class LLMProvider(Protocol):
    """
    Port for large language model text generation.

    Used by the Ghost Architect for causal inference and by the
    ProposalParser for natural language understanding.
    """

    def generate(
        self,
        prompt: str,
        *,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> str:
        """
        Generate text from a prompt.

        Args:
            prompt:        User prompt / question.
            system_prompt: Optional system instructions.
            temperature:   Creativity parameter [0.0, 2.0].
            max_tokens:    Maximum tokens in response.

        Returns:
            Generated text response.

        Raises:
            LLMError:           If generation fails.
            LLMConnectionError: If the API is unreachable.
            LLMRateLimitError:  If rate limit is exceeded.
        """
        ...

    def is_available(self) -> bool:
        """
        Check if the LLM provider is configured and reachable.

        Returns:
            True if a valid API key is set and the provider is responsive.
        """
        ...

    @property
    def name(self) -> str:
        """Human-readable name of the provider (e.g. 'OpenAI', 'Ollama')."""
        ...
