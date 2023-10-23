from __future__ import annotations

__version__ = "0.1.0"

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import AsyncIterator

    from telethon.hints import TotalList
    from telethon.tl.custom import Message

GPTMessage = dict[str, str]


class TelegramInterface(ABC):
    @abstractmethod
    async def start(self):
        raise NotImplementedError()

    @abstractmethod
    async def get_messages(
        self, number_of_messages=100, oldest_first=False
    ) -> TotalList[Message]:
        raise NotImplementedError()

    @abstractmethod
    async def send_message(self, message: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    async def delete_last_message(self):
        raise NotImplementedError()

    @abstractmethod
    async def message_stream(self) -> AsyncIterator[Message]:
        raise NotImplementedError()

    @abstractmethod
    async def _on_new_message(self, event) -> None:
        raise NotImplementedError()


class ConversationStreamGenerator(ABC):
    @abstractmethod
    async def start(self) -> None:
        raise NotImplementedError()

    @abstractmethod
    async def run(self):
        raise NotImplementedError()

    @abstractmethod
    async def message_stream(self) -> AsyncIterator[list[GPTMessage]]:
        raise NotImplementedError()

    @abstractmethod
    def get_history(self) -> list[GPTMessage]:
        raise NotImplementedError()

    @abstractmethod
    async def generate_additional_message(self) -> None:
        raise NotImplementedError()


class BotRunner(ABC):
    @abstractmethod
    async def run(self):
        raise NotImplementedError()


class ChatGPTInterface(ABC):
    @abstractmethod
    def set_history(self, history: list[GPTMessage]) -> None:
        raise NotImplementedError()

    @abstractmethod
    def get_history(self, n: int | None) -> list[GPTMessage]:
        raise NotImplementedError()

    @abstractmethod
    async def generate_response(self, messages: list[GPTMessage]) -> str:
        raise NotImplementedError()

    @abstractmethod
    def get_preamble(self) -> str:
        raise NotImplementedError()

    @abstractmethod
    def set_preamble(self, preamble: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def remove_last_assistant_message(self) -> None:
        raise NotImplementedError()

    @abstractmethod
    def pause_replies(self) -> None:
        raise NotImplementedError()

    @abstractmethod
    def resume_replies(self) -> None:
        raise NotImplementedError()
