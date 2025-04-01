from __future__ import annotations
from collections.abc import Sequence
from enum import Enum, auto


__version__ = "0.1.0"

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import AsyncIterator

    from telethon.hints import TotalList
    from telethon.tl.custom import Message
    from ai_scambaiter.agent import Agent


class Role(Enum):
    USER = auto()
    ASSISTANT = auto()
    SYSTEM = auto()


@dataclass
class GPTMessage:
    content: str
    role: Role
    n_tokens: int


class TelegramInterface(ABC):
    @abstractmethod
    async def start(self) -> None:
        raise NotImplementedError()

    @abstractmethod
    async def get_messages(
        self, chat_id: int, number_of_messages: int = 100, oldest_first: bool = False
    ) -> TotalList:
        raise NotImplementedError()

    @property
    @abstractmethod
    def dialogs(self) -> dict[int, object]:
        raise NotImplementedError()

    @abstractmethod
    async def send_message(self, chat_id: int, message: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    async def delete_last_message(self, chat_id: int) -> None:
        raise NotImplementedError()

    @abstractmethod
    async def message_stream(self) -> AsyncIterator[Message]:
        raise NotImplementedError()

    @abstractmethod
    async def _on_new_message(self, event) -> None:
        raise NotImplementedError()


class BotRunner(ABC):
    @abstractmethod
    async def run(self) -> None:
        raise NotImplementedError()

    @abstractmethod
    async def start(self) -> None:
        raise NotImplementedError()

    @property
    @abstractmethod
    def agents(self) -> dict[int, Agent]:
        raise NotImplementedError()


class ChatGPTInterface(ABC):
    @abstractmethod
    def number_of_tokens(self, text: str) -> int:
        raise NotImplementedError()

    @abstractmethod
    def shorten_history(
        self, n_preamble_tokens: int, history: list[GPTMessage]
    ) -> None:
        raise NotImplementedError()

    @abstractmethod
    async def send_and_receive(self, messages: Sequence[GPTMessage]) -> str:
        raise NotImplementedError()
