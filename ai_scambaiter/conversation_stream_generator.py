from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, AsyncIterator, Awaitable, Callable

from . import ConversationStreamGenerator, GPTMessage

if TYPE_CHECKING:
    from telethon.hints import TotalList
    from telethon.tl.custom import Message


class ConversationStreamGeneratorImpl(ConversationStreamGenerator):
    def __init__(
        self,
        get_messages_hook: Callable[[int], Awaitable[TotalList[Message]]],
        message_stream_hook: Callable[[], AsyncIterator[Message]],
        own_id: int,
        wait_with_reply=20,
        number_of_old_messages: int = 1000,
    ):
        self._get_messages_hook = get_messages_hook
        self._message_stream_hook = message_stream_hook
        self._conversation_queue: asyncio.Queue[GPTMessage] = asyncio.Queue(maxsize=100)
        self._last_update: datetime | None = None
        self._own_id = int(own_id)
        self._wait_with_reply: timedelta = timedelta(
            seconds=(float(wait_with_reply) or 20)
        )
        self._number_of_old_messages = number_of_old_messages or 1000
        self._history: list[GPTMessage] = []

    async def start(self):
        messages = await self._get_messages_hook(
            number_of_messages=self._number_of_old_messages
        )
        self._history = [self._message_to_gpt(m) for m in messages if m.text]
        self._last_update = datetime.now() - self._wait_with_reply

    async def run(self):
        while True:
            async for message in self._message_stream_hook():
                await self._conversation_queue.put(self._message_to_gpt(message))
                self._last_update = datetime.now()

    def _message_to_gpt(self, message) -> GPTMessage:
        return {
            "role": ("assistant" if message.sender_id == self._own_id else "user"),
            "content": message.text.replace("\n", " "),
        }

    async def message_stream(self) -> AsyncIterator[list[GPTMessage]]:
        message_list: list[GPTMessage] = []
        while True:
            message = await self._conversation_queue.get()
            if not message:
                # A None message means that an additonal assistant message should be
                # generated
                yield []
                continue
            message_list.append(message)
            self._last_update = datetime.now()
            # Wait a bit in case the other user adds more messages
            while True:
                now = datetime.now()
                wait_until = self._last_update + self._wait_with_reply
                if now >= wait_until:
                    break
                await asyncio.sleep((wait_until - now).total_seconds())
            # Get all messages which have arrived in the meantime
            send_immediately = False
            while not self._conversation_queue.empty():
                message = self._conversation_queue.get_nowait()
                if message:
                    message_list.append(message)
                else:
                    send_immediately = True
            # If the last message is ours ("assistant"), do not send it off; wait
            # until it was the other person's ("user") turn again.
            if message_list[-1]["role"] == "user" or send_immediately:
                yield message_list
                message_list = []

    def get_history(self) -> list[GPTMessage]:
        return self._history

    async def generate_additional_message(self):
        await self._conversation_queue.put(None)
