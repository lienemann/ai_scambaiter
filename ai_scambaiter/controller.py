from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from dependency_injector.wiring import Provide, inject


from .container import Container

if TYPE_CHECKING:
    from . import BotRunner, TelegramInterface


help_text = """Commands:
    s <chat_index> <message>  - Send message
    p <chat_index>            - show Preamble
    P <chat_index> <preamble> - set Preamble
    d <chat_index>            - Delete previous message
    g <chat_index>            - Generate new message out of order
    h <chat_index> <n>        - show last n messages in History
    u <chat_index>            - paUse
    c <chat_index>            - Continue
    R                         - Restart the telegram client
    ?                         - Show this help
"""


class Controller:
    def __init__(
        self, bot_runner: BotRunner, telegram_interface: TelegramInterface
    ) -> None:
        self._bot_runner = bot_runner
        self._telegram_interface = telegram_interface

    def print_help(self):
        print(help_text)
        print("Chats:\n")
        agents = self._bot_runner.agents.keys()
        for i, chat_id in enumerate(agents):
            dialog = self._telegram_interface.dialogs[chat_id]
            print(f"{i}: {chat_id} - {dialog.title}")

    async def run(self):
        self.print_help()
        while True:
            try:
                command = await asyncio.to_thread(input, "\nCommand (? for help)> ")
                parts = command.split(maxsplit=2)
                if not parts:
                    continue
                cmd = parts[0]
                chat_index = parts[1] if len(parts) > 1 else ""
                args = parts[2] if len(parts) > 2 else ""
                if cmd == "s":
                    await self._send_message(int(chat_index), args)
                elif cmd == "p":
                    await self._show_preamble(int(chat_index))
                elif cmd == "P":
                    await self._set_preamble(int(chat_index), args)
                elif cmd == "d":
                    await self._delete_message(int(chat_index))
                elif cmd == "g":
                    await self._generate_message(int(chat_index))
                elif cmd == "h":
                    await self._show_history(int(chat_index), args)
                elif cmd == "u":
                    await self._pause(int(chat_index))
                elif cmd == "c":
                    await self._continue(int(chat_index))
                elif cmd == "R":
                    await self._restart_telegram()
                elif cmd == "?":
                    self.print_help()
                else:
                    print("Unknown command")
            except ValueError as e:
                print(f"Error: {e}")

    def _get_chat_id(self, chat_index: int) -> int | None:
        if chat_index < 0 or chat_index >= len(self._bot_runner.agents):
            print("Invalid chat_index")
            return None
        return list(self._bot_runner.agents.keys())[chat_index]

    @inject
    async def _send_message(
        self,
        chat_index: int,
        message: str,
        telegram_interface: TelegramInterface = Provide[Container.telegram_interface],
    ):
        if (chat_id := self._get_chat_id(chat_index)) is None:
            return
        if not message:
            print("No message specified")
            return
        await telegram_interface.send_message(chat_id, message)

    @inject
    async def _show_preamble(
        self,
        chat_index: int,
    ):
        if (chat_id := self._get_chat_id(chat_index)) is None:
            return
        print(self._bot_runner.agents[chat_id].get_preamble())

    @inject
    async def _set_preamble(self, chat_index: int, preamble: str):
        if not preamble:
            print("No preamble specified")
            return
        if (chat_id := self._get_chat_id(chat_index)) is None:
            return
        self._bot_runner.agents[chat_id].set_preamble(preamble)

    @inject
    async def _delete_message(
        self,
        chat_index: int,
        telegram_interface: TelegramInterface = Provide[Container.telegram_interface],
    ):
        if (chat_id := self._get_chat_id(chat_index)) is None:
            return
        await telegram_interface.delete_last_message(chat_id)
        self._bot_runner.agents[chat_id].remove_last_assistant_message()

    @inject
    async def _generate_message(
        self,
        chat_index: int,
    ):
        if (chat_id := self._get_chat_id(chat_index)) is None:
            return
        await self._bot_runner.agents[chat_id].receive_message(None)

    @inject
    async def _show_history(self, chat_index: int, n):
        if (chat_id := self._get_chat_id(chat_index)) is None:
            return
        if n:
            try:
                n = int(n)
            except ValueError:
                print("Invalid number")
                return
        else:
            n = None
        print(
            "\n".join(str(m) for m in self._bot_runner.agents[chat_id].get_history(n))
        )

    @inject
    async def _pause(
        self,
        chat_index: int,
    ):
        if (chat_id := self._get_chat_id(chat_index)) is None:
            return
        await self._bot_runner.agents[chat_id].stop()

    @inject
    async def _continue(
        self,
        chat_index: int,
    ):
        if (chat_id := self._get_chat_id(chat_index)) is None:
            return
        await self._bot_runner.agents[chat_id].start()

    @inject
    async def _restart_telegram(
        self,
        telegram_interface: TelegramInterface = Provide[Container.telegram_interface],
    ):
        await telegram_interface.start()
