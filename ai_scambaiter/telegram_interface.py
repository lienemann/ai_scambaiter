from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, AsyncIterator

from telethon import TelegramClient, events

from . import TelegramInterface

if TYPE_CHECKING:
    from telethon.hints import TotalList
    from telethon.tl.custom import Message

_logger = logging.getLogger("Telegram")


class TelegramInterfaceImpl(TelegramInterface):
    def __init__(self, api_id, api_hash, chat_title=None, chat_id=None):
        self.api_id = api_id
        self.api_hash = api_hash
        self.chat_title = chat_title
        self.chat_id = int(chat_id) if chat_id else None
        self.chat = None
        self.queue: asyncio.Queue[Message] = asyncio.Queue(maxsize=100)

        if not self.chat_title and not self.chat_id:
            raise ValueError("Either chat_title or chat_id must be specified.")

        self.client = TelegramClient("Session", api_id, api_hash)
        self.client.add_event_handler(self._on_new_message, events.NewMessage)

    async def start(self):
        await self.client.start()
        dialogs = await self.client.get_dialogs()
        if self.chat_id:
            self.chat = next(d for d in dialogs if d.id == self.chat_id)
        else:
            self.chat = next(d for d in dialogs if d.title == self.chat_title)
            self.chat_id = self.chat.id

    async def get_messages(
        self, number_of_messages=100, oldest_first=True
    ) -> TotalList[Message]:
        return await self.client.get_messages(
            self.chat, limit=number_of_messages, reverse=oldest_first
        )

    async def send_message(self, message: str):
        _logger.info("Sending telegram message: %s", message)
        await self.client.send_message(self.chat, message)
        # print("** Please send message: " + message)

    async def delete_last_message(self):
        messages = await self.get_messages(number_of_messages=1, oldest_first=False)
        if messages:
            await self.client.delete_messages(None, messages[0], revoke=True)
            _logger.info(
                "Deleted telegram message with id %i: %s",
                messages[0].id,
                messages[0].text,
            )

    async def message_stream(self) -> AsyncIterator[Message]:
        while True:
            yield await self.queue.get()

    async def _on_new_message(self, event: events.NewMessage):
        if event.message.chat_id != self.chat.id:
            return
        _logger.info(
            "Got new message with id %i: %s", event.message.id, event.message.text
        )
        await self.queue.put(event.message)
