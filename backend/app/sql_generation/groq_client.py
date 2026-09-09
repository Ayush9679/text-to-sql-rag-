import os

from dotenv import load_dotenv
from groq import Groq


load_dotenv()


class GroqClientError(Exception):
    """
    Raised when the Groq client cannot complete a request.
    """

    def __init__(
        self,
        message: str,
        retryable: bool = False,
    ):
        super().__init__(message)

        self.message = message
        self.retryable = retryable


class GroqLLMClient:
    """
    Thin wrapper around the Groq Python SDK.

    This class is responsible only for communicating
    with Groq.

    Prompt construction and SQL-specific logic belong
    to later Phase 5 components.
    """

    DEFAULT_MODEL = "openai/gpt-oss-120b"

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ):
        self.api_key = (
            api_key
            or os.getenv("GROQ_API_KEY")
        )

        if not self.api_key:
            raise GroqClientError(
                "GROQ_API_KEY is not configured.",
                retryable=False,
            )

        self.model = (
            model
            or os.getenv(
                "GROQ_MODEL",
                self.DEFAULT_MODEL,
            )
        )

        self.client = Groq(
            api_key=self.api_key
        )

    def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        temperature: float = 0.0,
        max_completion_tokens: int = 2048,
    ) -> str:
        """
        Send a prompt to Groq and return the
        generated text.
        """

        prompt = prompt.strip()

        if not prompt:
            raise GroqClientError(
                "Prompt cannot be empty.",
                retryable=False,
            )

        messages = []

        if system_prompt:
            messages.append(
                {
                    "role": "system",
                    "content": system_prompt,
                }
            )

        messages.append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        try:

            response = (
                self.client
                .chat
                .completions
                .create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_completion_tokens=(
                        max_completion_tokens
                    ),
                )
            )

        except Exception as exc:

            raise GroqClientError(
                f"Groq request failed: {exc}",
                retryable=True,
            ) from exc

        if not response.choices:

            raise GroqClientError(
                "Groq returned no choices.",
                retryable=True,
            )

        content = (
            response
            .choices[0]
            .message
            .content
        )

        if not content:

            raise GroqClientError(
                "Groq returned empty content.",
                retryable=True,
            )

        return content.strip()