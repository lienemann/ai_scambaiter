from ..chatgpt_interface import ChatGPTInterfaceImpl


class ChatGPTInterfaceMock(ChatGPTInterfaceImpl):
    async def _send_and_receive(self, messages) -> str:
        return f"This is a sample reply to the message {messages[-1]}."
