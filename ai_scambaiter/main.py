import asyncio
import logging

from dependency_injector.wiring import Provide, inject

from . import TelegramInterface, BotRunner
from .container import Container
from .controller import Controller

_logger = logging.getLogger("Main")

mock = False
generate_scam = True


@inject
async def _main(
    telegram_interface: TelegramInterface = Provide[Container.telegram_interface],
    bot_runner: BotRunner = Provide[Container.bot_runner],
):
    await telegram_interface.start()
    await bot_runner.start()
    if mock and generate_scam:
        from .mocks.scam_generator import ScamGenerator

        scam_generator = ScamGenerator(telegram_interface._on_new_message)

    controller = Controller(bot_runner, telegram_interface)

    while True:
        _logger.debug("Waiting for messages...")
        coroutines = [bot_runner.run(), controller.run()]
        if mock and generate_scam:
            coroutines.append(scam_generator.run())
        await asyncio.gather(*coroutines)


def main():
    log_level = logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            # logging.StreamHandler(sys.stdout),
            logging.FileHandler("ai_scambaiter.log", encoding="utf-8"),
        ],
    )
    logging.getLogger("Main").setLevel(log_level)
    logging.getLogger("BotRunner").setLevel(log_level)
    logging.getLogger("Agent").setLevel(log_level)
    logging.getLogger("ChatGPT").setLevel(log_level)
    logging.getLogger("Telegram").setLevel(log_level)
    logging.getLogger("openai").setLevel(logging.WARN)
    logging.getLogger("telethon").setLevel(logging.WARN)
    logging.getLogger("httpcore").setLevel(logging.WARN)
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
            TelegramInterfaceMock("12345", "hash", "my_chat", "Hannah")
        )
        container.chatgpt_inferface.override(
            ChatGPTInterfaceMock("12345", {1234: "Hannah"})
        )
        ### End mocking

    main()
