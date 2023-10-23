import logging

import openai
import tiktoken

from . import ChatGPTInterface, GPTMessage

ROLE_TOKENS = 1  # Role is always 1 token
MESSAGE_TOKENS = 4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
REPLY_TOKENS = 2  # every reply is primed with <im_start>assistant

_logger = logging.getLogger("ChatGPT")


def default_preamble(name: str | None) -> str:
    return (
        "I play the role of a scammer who pretends to be a middle aged woman"
        f'{" named "+name if name else ""}. You play the role of the recipient. '
        "The goal is to mess with the scammer and waste as much of their time as "
        "possible. Make the conversation lighthearted, friendly and funny, but "
        "still reasonable so that they remain engaged. Avoid repetitions and too "
        "formal language. Do not offer further assistance. Over time, let the "
        "conversation become more awkward and lengthy, but do not insult. Remain "
        "within lawful limits and the telegram terms-of-service. No harassment, "
        "sexism or racism. Generate output which is compatible with the telegram "
        "messenger."
    )


class ChatGPTInterfaceImpl(ChatGPTInterface):
    def __init__(self, api_key, name: str | None = None, preamble: str | None = None):
        self._running = True
        openai.api_key = api_key
        self._openai_model = "gpt-3.5-turbo"
        self._preamble = {
            "role": "system",
            "content": "",
        }
        self._history: list[tuple[GPTMessage, int]] = []
        self._max_input_tokens = 3000
        try:
            self._token_encoder = tiktoken.encoding_for_model(self._openai_model)
        except KeyError:
            self._token_encoder = tiktoken.get_encoding("cl100k_base")
        self.set_preamble(preamble or default_preamble(name))

    def _number_of_tokens(self, message: GPTMessage) -> int:
        return (
            len(self._token_encoder.encode(message["content"]))
            + ROLE_TOKENS
            + MESSAGE_TOKENS
        )

    def _shorten_history(self):
        """Shortens the history to fit within the token limit."""
        number_of_tokens = (
            self._preamble_tokens + sum(t for _, t in self._history) + REPLY_TOKENS
        )
        while number_of_tokens > self._max_input_tokens and self._history:
            number_of_tokens -= self._history.pop(0)[1]

    async def _send_and_receive(self, messages) -> str:
        response = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=256,
            temperature=0.5,
        )
        return response.choices[0].message.content

    def set_history(self, history: list[GPTMessage]) -> None:
        self._history = [(m, self._number_of_tokens(m)) for m in history]

    def get_history(self, n: int | None = None) -> list[GPTMessage]:
        """Returns the last n messages from the history. If n is None, returns the
        entire history."""
        if n is None:
            return [m for m, _ in self._history]
        else:
            return [m for m, _ in self._history[-n:]]

    async def generate_response(self, messages: list[GPTMessage]) -> str | None:
        # Use the OpenAI API to generate a response to the prompt
        self._history += [(m, self._number_of_tokens(m)) for m in messages]
        if not self._running:
            return ""
        self._shorten_history()
        _logger.debug(
            "Request from ChatGPT with %i messages: %s",
            len(self._history),
            self._history[-1] if self._history else None,
        )
        # Do not append to history - we will anyway received over own message
        # from telegram
        response = await self._send_and_receive(
            [self._preamble] + [m[0] for m in self._history]
        )
        _logger.info("Response from ChatGPT: %s", response)
        return response

    def get_preamble(self) -> str:
        return self._preamble["content"]

    def set_preamble(self, preamble: str):
        self._preamble["content"] = preamble
        self._preamble_tokens = self._number_of_tokens(self._preamble)
        _logger.debug(
            "Setting preamble with %i tokens: %s", self._preamble_tokens, self._preamble
        )

    def remove_last_assistant_message(self) -> None:
        """Removes the last message from the history that was sent by the assistant.
        Do not remove user messages, because they may have been received later."""

        for i in range(len(self._history) - 1, -1, -1):
            if self._history[i][0]["role"] == "assistant":
                del self._history[i]
                return

    def pause_replies(self) -> None:
        self._running = False

    def resume_replies(self) -> None:
        self._running = True
