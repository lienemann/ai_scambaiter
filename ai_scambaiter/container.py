from dependency_injector import containers, providers

from . import (
    BotRunner,
    ChatGPTInterface,
    TelegramInterface,
)
from .bot_runner import BotRunnerImpl
from .chatgpt_interface import ChatGPTInterfaceImpl
from .telegram_interface import TelegramInterfaceImpl


class Container(containers.DeclarativeContainer):
    config = providers.Configuration(ini_files=["./config.ini"])

    telegram_interface: TelegramInterface = providers.Singleton(
        TelegramInterfaceImpl,
        api_id=config.auth.telegram_api_id,
        api_hash=config.auth.telegram_api_hash,
        phone=config.auth.phone,
    )

    chatgpt_inferface: ChatGPTInterface = providers.Singleton(
        ChatGPTInterfaceImpl,
        api_key=config.auth.openai_api_key,
    )

    bot_runner: BotRunner = providers.Singleton(
        BotRunnerImpl,
        message_stream=telegram_interface.provided.message_stream,
        telegram_interface=telegram_interface,
        chatgpt_interface=chatgpt_inferface,
        conversations=config.conversations.chats,
        own_id=config.auth.own_id,
    )
