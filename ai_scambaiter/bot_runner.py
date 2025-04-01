from __future__ import annotations

import logging
from typing import TYPE_CHECKING, AsyncIterator

from ai_scambaiter.agent import Agent

from . import BotRunner

if TYPE_CHECKING:
    from typing import Callable

    from . import ChatGPTInterface, GPTMessage, TelegramInterface

_logger = logging.getLogger("BotRunner")


class BotRunnerImpl(BotRunner):
    def __init__(
        self,
        message_stream: Callable[[], AsyncIterator[list[GPTMessage]]],
        telegram_interface: TelegramInterface,
        chatgpt_interface: ChatGPTInterface,
        conversations: str,
        own_id: str,
    ):
        self._message_stream = message_stream
        self._agents: dict[int, Agent] = {}
        self._conversations: list[str] = conversations.strip().split("\n")
        self._telegram_interface: TelegramInterface = telegram_interface
        self._chatgpt_interface: ChatGPTInterface = chatgpt_interface
        self._own_id: int = int(own_id)

    async def start(self) -> None:
        for conv in self._conversations:
            agent = Agent(
                conv, self._own_id, self._telegram_interface, self._chatgpt_interface
            )
            await agent.start()
            self._agents[agent.chat_id] = agent

    async def run(self):
        while True:
            async for message in self._message_stream():
                try:
                    chat_id = message.chat_id
                    if chat_id not in self._agents:
                        _logger.debug(
                            "Got new other message with chat id %i: %s",
                            message.chat_id,
                            message.text,
                        )
                        continue
                    _logger.info(
                        "Got new message with chat id %i: %s",
                        message.chat_id,
                        message.text,
                    )
                except AttributeError:
                    continue
                agent = self._agents[chat_id]
                await agent.receive_message(message)

    @property
    def agents(self) -> dict[int, Agent]:
        return self._agents
