import asyncio
import itertools
from typing import Callable

from telethon import events
from telethon.tl.custom import Message


class ScamGenerator:
    def __init__(self, message_hook: Callable[[events.NewMessage], None]):
        self._thread = None
        self._message_hook = message_hook

    async def run(self):
        counter = itertools.count(100)
        while True:
            await asyncio.sleep(5)
            event = events.NewMessage()
            i = next(counter)
            m = Message(i)
            m.text = f"Message {i}"
            m._chat_peer = 1234567
            m._sender_id = 111 if (i % 4) == 0 else 222
            event.message = m
            await self._message_hook(event)
