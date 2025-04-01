from collections.abc import Sequence
from ai_scambaiter import GPTMessage
from ai_scambaiter.chatgpt_interface import ChatGPTInterfaceImpl


class ChatGPTInterfaceMock(ChatGPTInterfaceImpl):
    async def send_and_receive(self, messages: Sequence[GPTMessage]) -> str | None:
        return f"This is a sample reply to the message {messages[-1].content}."
