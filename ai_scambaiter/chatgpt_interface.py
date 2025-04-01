import logging
from collections.abc import Sequence
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)
import openai
import tiktoken

from . import ChatGPTInterface, GPTMessage, Role

ROLE_TOKENS = 1  # Role is always 1 token
MESSAGE_TOKENS = 4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
REPLY_TOKENS = 2  # every reply is primed with <im_start>assistant

_logger = logging.getLogger("ChatGPT")


class ChatGPTInterfaceImpl(ChatGPTInterface):
    """Interface to the OpenAI API."""

    def __init__(self, api_key: str):
        self._running = True
        self._client = openai.AsyncOpenAI(api_key=api_key)
        self._openai_model = "gpt-4o-mini"
        self._max_input_tokens = 120000
        try:
            self._token_encoder = tiktoken.encoding_for_model(self._openai_model)
        except KeyError:
            self._token_encoder = tiktoken.get_encoding("cl100k_base")

    def number_of_tokens(self, text: str) -> int:
        return len(self._token_encoder.encode(text)) + ROLE_TOKENS + MESSAGE_TOKENS

    def shorten_history(
        self, n_preamble_tokens: int, history: list[GPTMessage]
    ) -> None:
        """Shortens the history to fit within the token limit."""
        number_of_tokens = (
            n_preamble_tokens + sum(m.n_tokens for m in history) + REPLY_TOKENS
        )
        while number_of_tokens > self._max_input_tokens and history:
            number_of_tokens -= history.pop(0).n_tokens

    async def send_and_receive(self, messages: Sequence[GPTMessage]) -> str:
        _logger.debug(
            "Request from ChatGPT with %i messages: %s",
            len(messages),
            messages[-1].content if messages else None,
        )
        openai_messages: list[ChatCompletionMessageParam] = []
        for m in messages:
            if m.role == Role.SYSTEM:
                openai_messages.append(
                    ChatCompletionSystemMessageParam(role="system", content=m.content)
                )
            elif m.role == Role.USER:
                openai_messages.append(
                    ChatCompletionUserMessageParam(role="user", content=m.content)
                )
            else:
                openai_messages.append(
                    ChatCompletionAssistantMessageParam(
                        role="assistant", content=m.content
                    )
                )
        response = await self._client.chat.completions.create(
            model=self._openai_model,
            messages=openai_messages,
            max_completion_tokens=8000,
            temperature=0.5,
            n=1,
        )
        return response.choices[0].message.content or "Again?"
