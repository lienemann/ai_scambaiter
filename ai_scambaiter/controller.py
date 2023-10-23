import asyncio

from dependency_injector.wiring import Provide, inject

from .container import Container

help_text = """Commands:
    s <message>  - Send message
    p            - show Preamble
    P <preamble> - set Preamble
    d            - Delete previous message
    g            - Generate new message out of order
    h <n>        - show last n messages in History
    u            - paUse
    c            - Continue
    ?            - Show this help
"""


class Controller:
    async def run(self):
        print(help_text)
        while True:
            command = await asyncio.to_thread(input, "Command (? for help)> ")
            parts = command.split(maxsplit=1)
            if not parts:
                continue
            cmd = parts[0]
            args = parts[1] if len(parts) > 1 else ""
            if cmd == "s":
                await self._send_message(args)
            elif cmd == "p":
                await self._show_preamble()
            elif cmd == "P":
                await self._set_preamble(args)
            elif cmd == "d":
                await self._delete_message()
            elif cmd == "g":
                await self._generate_message()
            elif cmd == "h":
                await self._show_history(args)
            elif cmd == "u":
                await self._pause()
            elif cmd == "c":
                await self._continue()
            elif cmd == "?":
                print(help_text)
            else:
                print("Unknown command")

    @inject
    async def _send_message(
        self, message, telegram_interface=Provide[Container.telegram_interface]
    ):
        if not message:
            print("No message specified")
            return
        await telegram_interface.send_message(message)

    @inject
    async def _show_preamble(
        self, chatgpt_interface=Provide[Container.chatgpt_inferface]
    ):
        print(chatgpt_interface.get_preamble())

    @inject
    async def _set_preamble(
        self, preamble, chatgpt_interface=Provide[Container.chatgpt_inferface]
    ):
        if not preamble:
            print("No preamble specified")
            return
        chatgpt_interface.set_preamble(preamble)

    @inject
    async def _delete_message(
        self,
        telegram_interface=Provide[Container.telegram_interface],
        chatgpt_interface=Provide[Container.chatgpt_inferface],
    ):
        await telegram_interface.delete_last_message()
        chatgpt_interface.remove_last_assistant_message()

    @inject
    async def _generate_message(
        self, conversation_gen=Provide[Container.conversation_stream_generator]
    ):
        await conversation_gen.generate_additional_message()

    @inject
    async def _show_history(
        self, n, chatpgt_interface=Provide[Container.chatgpt_inferface]
    ):
        if n:
            try:
                n = int(n)
            except ValueError:
                print("Invalid number")
                return
        else:
            n = None
        print("\n".join(str(m) for m in chatpgt_interface.get_history(n)))

    @inject
    async def _pause(
        self, chatpgt_interface=Provide[Container.chatgpt_inferface],
    ):
        chatpgt_interface.pause_replies()

    @inject
    async def _continue(
        self, chatpgt_interface=Provide[Container.chatgpt_inferface],
    ):
        chatpgt_interface.resume_replies()