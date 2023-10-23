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
        self, number_of_messages=100, oldest_first=True
    ) -> TotalList[Message]:
        def make_message(i):
            m = Message(i + 100)
            m.text = f"Message {i}"
            m._sender_id = 111 if (i % 2) == 0 else 222
            return m

        return TotalList(make_message(i) for i in range(10))

    async def send_message(self, message):
        print("Send message: " + message)

    async def delete_last_message(self):
        print("Delete last message")