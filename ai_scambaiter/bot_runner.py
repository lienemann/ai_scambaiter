from __future__ import annotations

from typing import TYPE_CHECKING, AsyncIterator

from . import BotRunner, GPTMessage

if TYPE_CHECKING:
    from typing import Awaitable, Callable


class BotRunnerImpl(BotRunner):
    def __init__(
        self,
        chatgpt_hook: Callable[[list[GPTMessage]], Awaitable[str]],
        message_stream: Callable[[], AsyncIterator[list[GPTMessage]]],
        send_hook: Callable[[str | None], Awaitable[None]],
    ):
        self._chatgpt_hook = chatgpt_hook
        self._message_stream = message_stream
        self._send_hook = send_hook

    async def run(self):
        while True:
            async for messages in self._message_stream():
                response = await self._chatgpt_hook(messages)
                if response:
                    await self._send_hook(response)
