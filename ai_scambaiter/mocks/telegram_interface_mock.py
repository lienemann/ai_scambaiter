from __future__ import annotations

import logging
from unittest.mock import Mock

from telethon.hints import TotalList
from telethon.tl.custom import Message

from ..telegram_interface import TelegramInterfaceImpl

_logger = logging.getLogger("Telegram")


class TelegramInterfaceMock(TelegramInterfaceImpl):
    async def start(self):
        _logger.debug("Started telegram interface")
        self.chat = Mock(id=1234567)

    async def get_messages(
        self, chat_id: int, number_of_messages: int = 100, oldest_first: bool = True
    ) -> TotalList:
        def make_message(i):
            m = Message(i + 100)
            m.text = f"Message {i}"
            m._sender_id = 111 if (i % 2) == 0 else 222
            return m

        return TotalList(make_message(i) for i in range(10))

    async def send_message(self, chat_id: int, message: str):
        print("Send message: " + message)

    async def delete_last_message(self, chat_id: int):
        print("Delete last message")
