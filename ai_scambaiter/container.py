from dependency_injector import containers, providers

from . import (
    BotRunner,
    ChatGPTInterface,
    ConversationStreamGenerator,
    TelegramInterface,
)
from .bot_runner import BotRunnerImpl
from .chatgpt_interface import ChatGPTInterfaceImpl
from .conversation_stream_generator import ConversationStreamGeneratorImpl
from .telegram_interface import TelegramInterfaceImpl


class Container(containers.DeclarativeContainer):
    config = providers.Configuration(ini_files=["./config.ini"])

    telegram_interface: TelegramInterface = providers.Singleton(
        TelegramInterfaceImpl,
        api_id=config.auth.telegram_api_id,
        api_hash=config.auth.telegram_api_hash,
        chat_title=config.chat.chat_title,
        chat_id=config.chat.chat_id,
    )

    conversation_stream_generator: ConversationStreamGenerator = providers.Singleton(
        ConversationStreamGeneratorImpl,
        get_messages_hook=telegram_interface.provided.get_messages,
        message_stream_hook=telegram_interface.provided.message_stream,
        own_id=config.auth.own_id,
        wait_with_reply=config.chat.wait_with_reply,
        number_of_old_messages=config.chat.number_of_old_messages or 1000,
    )

    chatgpt_inferface: ChatGPTInterface = providers.Singleton(
        ChatGPTInterfaceImpl,
        api_key=config.auth.openai_api_key,
        name=config.chat.chat_title,
        preamble=config.chat.preamble,
    )

    bot_runner: BotRunner = providers.Singleton(
        BotRunnerImpl,
        chatgpt_hook=chatgpt_inferface.provided.generate_response,
        message_stream=conversation_stream_generator.provided.message_stream,
        send_hook=telegram_interface.provided.send_message,
    )
