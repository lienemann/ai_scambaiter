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
    def __init__(
        self,
        api_id: str | int,
        api_hash: str,
        phone: str,
    ):
        self.phone = phone
        self.api_id = api_id
        self.api_hash = api_hash
        self.queue: asyncio.Queue[Message] = asyncio.Queue(maxsize=100)
        self._dialogs: dict[int, object] = []

        self.client = TelegramClient("Session", int(api_id), api_hash)
        self.client.add_event_handler(self._on_new_message, events.NewMessage)

    async def start(self):
        await self.client.start(phone=self.phone)  # type: ignore
        self._dialogs = {d.id: d for d in await self.client.get_dialogs()}
        _logger.info("Got %i chats", len(self._dialogs))

    @property
    def dialogs(self) -> dict[int, object]:
        """Get all dialogs (chats) from the telegram client."""
        return self._dialogs

    async def get_messages(
        self, chat_id: int, number_of_messages: int = 100, oldest_first: bool = True
    ) -> TotalList:
        return await self.client.get_messages(
            self._dialogs[chat_id], limit=number_of_messages, reverse=oldest_first
        )

    async def send_message(self, chat_id: int, message: str):
        _logger.info("Sending telegram message to %i: %s", chat_id, message)
        try:
            msg = await self.client.send_message(self._dialogs[chat_id], message)
            if not msg:
                raise RuntimeError("Message not sent")
        except Exception as e:
            _logger.error("Error sending message to %i: %s", chat_id, e)
            raise e

    async def delete_last_message(self, chat_id: int):
        messages = await self.get_messages(
            chat_id, number_of_messages=1, oldest_first=False
        )
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
        await self.queue.put(event.message)
