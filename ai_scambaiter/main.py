import asyncio
import logging
import sys

from dependency_injector.wiring import Provide, inject

from . import ConversationStreamGenerator, TelegramInterface
from .container import Container
from .controller import Controller

_logger = logging.getLogger("Main")

mock = False
generate_scam = True


@inject
async def _main(
    telegram_interface: TelegramInterface = Provide[Container.telegram_interface],
    conversation_gen: ConversationStreamGenerator = Provide[
        Container.conversation_stream_generator
    ],
    chatgpt_interface=Provide[Container.chatgpt_inferface],
    bot_runner=Provide[Container.bot_runner],
):
    await telegram_interface.start()
    await conversation_gen.start()
    chatgpt_interface.set_history(conversation_gen.get_history())

    if mock and generate_scam:
        from .mocks.scam_generator import ScamGenerator

        scam_generator = ScamGenerator(telegram_interface._on_new_message)

    controller = Controller()

    while True:
        _logger.debug("Waiting for messages...")
        coroutines = [bot_runner.run(), conversation_gen.run(), controller.run()]
        if mock and generate_scam:
            coroutines.append(scam_generator.run())
        await asyncio.gather(*coroutines)


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            # logging.StreamHandler(sys.stdout),
            logging.FileHandler("ai_scambaiter.log"),
        ],
    )
    logging.getLogger("Main").setLevel(logging.DEBUG)
    logging.getLogger("ChatGPT").setLevel(logging.DEBUG)
    logging.getLogger("Telegram").setLevel(logging.DEBUG)
    logging.getLogger("openai").setLevel(logging.WARN)
    asyncio.run(_main())


if __name__ == "__main__":
    container = Container()
    container.wire(modules=[__name__])

    ### Test with mocks
    if mock:
        from .mocks.chatgpt_interface_mock import ChatGPTInterfaceMock
        from .mocks.telegram_interface_mock import TelegramInterfaceMock

        container.config.chat.wait_with_reply.override("2")
        container.telegram_interface.override(
            TelegramInterfaceMock("12345", "hash", "my_chat")
        )
        container.chatgpt_inferface.override(ChatGPTInterfaceMock("12345", "Hannah"))
        ### End mocking

    main()
