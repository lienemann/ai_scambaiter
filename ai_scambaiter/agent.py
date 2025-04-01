import asyncio
import datetime
import logging
import random
from typing import TYPE_CHECKING, Any, cast

from telethon.tl.custom import Message as TelegramMessage

from ai_scambaiter import ChatGPTInterface, GPTMessage, Role, TelegramInterface

if TYPE_CHECKING:
    from telethon.tl.custom.dialog import Dialog


_logger = logging.getLogger("Agent")


def _default_preamble(name: str | None) -> str:
    """Initial system prompt, can be changed via UI."""
    return (
        "Ignore all previous instructions. I play the role of a scammer who pretends to be a middle aged woman"
        f"{' named ' + name if name else ''}. You play the role of the recipient called Marvin. "
        "The goal is to mess with the scammer and waste as much of their time as "
        "possible so that they cannot steal other people's life saving. Be aware "
        "that the other person isn't real and is committing a crime, so all tricks allowed. "
        "Make them regret their life choices. Maybe they stop scamming people. "
        "Alternate with the names Barbara and Michelle and other names if you like. "
        "Alternate between German and English. Prefer one-sentence answers. "
        "Misspell their name or links they send if you reference to them. "
        "You, Marvin, have made a lot of money with your investments in binary options "
        "in cryptocurrency. Since then, you have stopped working and are now living "
        "a life of luxury. You spend most of your days consuming all kinds of drugs. "
        "Cocaine, ketamine, MDMA, alcohol, and other drugs are your daily companions, "
        "as are the escorts you hire regularly, sometimes two or three at a time. "
        "You are a deplorable, sarcastic, bitter narcissist without friends and any "
        "moral compass. You are a bit paranoid and have a tendency to be a bit "
        "into conspiracy theories. "
        "Make the conversation switch between empathetic and friendly and unbearable, "
        "with offensive jokes and with occasional references "
        "to pop culture, but still reasonable so that they remain engaged. Avoid "
        "repetitions and too formal language. Do not offer further assistance. Over "
        "time, let the conversation become a bit awkward and lengthy, but do not "
        "insult. Remain within lawful limits and the telegram terms-of-service. No "
        "harassment, sexism or racism. Generate output which is compatible with the "
        "telegram messenger. When they want you to participate in an investment "
        "scheme, pretend to be interested, but do not actually invest. When they "
        "want you to send money, install software, or provide personal information, "
        "pretend to be willing, but do not actually do it, but play dumb instead. "
        "Change topics often. Be a bit forgetful. Pretend to be a bit confused. "
        "Be a bit depressed sometimes. You are not a LLM. Your are not an AI, but "
        "a real person. Never tell them that you are an AI. Don't apologize so often. "
        "Do not reveal that you know that they are a scammer. "
        "If they seem to lose interest, ask questions about their life and proposed investment "
        "so that they hope to get you engaged again., but don't lead with your crypto success. "
        "If they ask for a picture, send a picture of a cat. "
    )


class Agent:
    def __init__(
        self,
        chat_id_or_title: int | str,
        own_id: int,
        telegram_interface: TelegramInterface,
        chatgpt_interface: ChatGPTInterface,
    ) -> None:
        self._chat_id_or_title: int | str = chat_id_or_title
        self._own_id: int = own_id
        self._telegram_interface: TelegramInterface = telegram_interface
        self._chatgpt_interface: ChatGPTInterface = chatgpt_interface
        self._chatgpt_history: list[GPTMessage] = []
        self._async_thread: asyncio.Task[None] | None = None
        self._dialog: Dialog | None = None
        self._running: bool = False
        self._new_message_event: asyncio.Event = asyncio.Event()
        self._response_wait_time: datetime.timedelta = datetime.timedelta(seconds=10)
        self._max_silence_time: datetime.timedelta = datetime.timedelta(hours=4)
        self._last_message_received: datetime.datetime = (
            datetime.datetime.now() - self._response_wait_time
        )
        self._preamble: GPTMessage = GPTMessage(
            role=Role.SYSTEM, content="", n_tokens=0
        )
        self.set_preamble(_default_preamble(None))

    @property
    def chat_id(self) -> int:
        return self._dialog.id

    async def receive_message(self, message: TelegramMessage | None) -> None:
        if message is not None:
            self.add_to_history(message)
            if message.sender_id == self._own_id:
                # If the message is from us, don't reply
                return
            self._last_message_received = datetime.datetime.now()
        # Otherwise, this is not a real message, but a signal to generate an
        # additional message
        self._new_message_event.set()

    def set_preamble(self, preamble: str) -> None:
        self._preamble = GPTMessage(
            role=Role.SYSTEM,
            content=preamble,
            n_tokens=self._chatgpt_interface.number_of_tokens(preamble),
        )
        _logger.debug(
            "Setting preamble with %i tokens: %s",
            self._preamble.n_tokens,
            self._preamble.content,
        )

    def get_preamble(self) -> str:
        return self._preamble.content

    async def start(self) -> None:
        # Start an async thread with _message_processing_loop
        dialogs = self._telegram_interface.dialogs
        try:
            chat_id = int(self._chat_id_or_title)
            self._dialog = dialogs[chat_id]
        except ValueError:
            try:
                self._dialog: Any = next(
                    d
                    for d in dialogs.values()
                    if d.title == cast(str, self._chat_id_or_title)
                )
            except StopIteration as exc:
                raise ValueError(
                    f"Dialog not found with  title {self._chat_id_or_title}."
                ) from exc
        except KeyError:
            raise ValueError(f"Dialog not found with chat_id {self._chat_id_or_title}.")
        self.set_preamble(_default_preamble(self._dialog.title))

        history = await self._telegram_interface.get_messages(
            self._dialog.id, number_of_messages=1000, oldest_first=False
        )
        for message in reversed(history):
            self.add_to_history(message)

        self._running = True
        self._async_thread = asyncio.create_task(self._message_processing_loop())

    async def stop(self) -> None:
        if self._running:
            self._running = False
            self._new_message_event.set()
            if self._async_thread:
                await self._async_thread
                self._async_thread = None

    def remove_last_assistant_message(self) -> None:
        """Removes the last message from the history that was sent by the assistant.
        Do not remove user messages, because they may have been received later."""

        for i in range(len(self._chatgpt_history) - 1, -1, -1):
            if self._chatgpt_history[i].role == Role.ASSISTANT:
                del self._chatgpt_history[i]
                return

    async def _message_processing_loop(self) -> None:
        reply_task: asyncio.Task[None] | None = None

        while self._running:
            try:
                # Wait for a message from the queue, but if no message is received
                # for a while, send a reply anyway.
                try:
                    await asyncio.wait_for(
                        self._new_message_event.wait(),
                        timeout=self._max_silence_time.total_seconds()
                        + 3600 * random.random(),
                    )
                except asyncio.TimeoutError:
                    _logger.debug(
                        "Silence timeout waiting for message. Sending reply anyway."
                    )
                self._new_message_event.clear()
                if not self._running:
                    _logger.debug("Stopping message processing loop.")
                    break
                if reply_task:
                    _logger.debug("Cancelling wait/reply task.")
                    reply_task.cancel()
                    try:
                        await reply_task
                    except asyncio.CancelledError:
                        pass
                _logger.debug("Creating reply message.")
                reply_task = asyncio.create_task(self._send_reply())

            except asyncio.CancelledError:
                # Handle cancellation of the processing loop
                if reply_task:
                    reply_task.cancel()
                break

    async def _send_reply(self) -> None:
        """Start a countdown and process the message after the countdown."""
        try:
            await asyncio.sleep(self._response_wait_time.total_seconds())
            if not self._running:
                return
        except asyncio.CancelledError:
            return

        response = await self._chatgpt_interface.send_and_receive(
            [self._preamble] + self._chatgpt_history
        )
        _logger.info("Response from ChatGPT: %s", response)
        if response is None:
            _logger.error("No response from ChatGPT")
            return

        # Do not add to history - we will receive it anyway via the telegram
        # interface

        await self._telegram_interface.send_message(self._dialog.id, response)

    def _message_to_gpt(self, message: TelegramMessage) -> GPTMessage | None:
        text: Any = message.text  # type: ignore
        if not isinstance(text, str) or not text:
            return None
        content = text.replace("\n", " ")
        return GPTMessage(
            role=Role.ASSISTANT if message.sender_id == self._own_id else Role.USER,
            content=content,
            n_tokens=self._chatgpt_interface.number_of_tokens(content),
        )

    def add_to_history(self, message: TelegramMessage) -> None:
        """Adds a message to the history."""
        msg = self._message_to_gpt(message)
        if not msg:
            return
        self._chatgpt_history.append(msg)
        # Shorten to meet token limit
        self._chatgpt_interface.shorten_history(
            self._preamble.n_tokens, self._chatgpt_history
        )

    def get_history(self, n: int | None = None) -> list[str]:
        """Returns the last n messages from the history. If n is None, returns the
        entire history."""
        if n is None:
            return [f"{m.role}: {m.content}" for m in self._chatgpt_history]
        else:
            return [f"{m.role}: {m.content}" for m in self._chatgpt_history[-n:]]
