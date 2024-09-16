from typing import List

from autogen_core.components import (
    DefaultTopicId,
    RoutedAgent,
    message_handler,
)
from autogen_core.components.models import (
    LLMMessage,
    AssistantMessage,
    ChatCompletionClient,
    SystemMessage,
    UserMessage,
)
from autogen_core.base import MessageContext
from .data_types import GroupChatMessage, RequestToSpeak


class FacebookPostWriterAgent(RoutedAgent):
    def __init__(self, model_client: ChatCompletionClient) -> None:
        super().__init__("FacebookPostWriter")
        self._model_client = model_client
        self._chat_history: List[LLMMessage] = [
            SystemMessage("Write an engaging Facebook post in less than 100 words.")
        ]

    @message_handler
    async def handle_message(
        self, message: GroupChatMessage, ctx: MessageContext
    ) -> None:
        self._chat_history.append(message.body)

    @message_handler
    async def handle_request_to_speak(
        self, message: RequestToSpeak, ctx: MessageContext
    ) -> None:
        completion = await self._model_client.create(self._chat_history)
        self._chat_history.append(
            AssistantMessage(content=completion.content, source="FacebookPostWriter")
        )
        await self.publish_message(
            GroupChatMessage(
                body=UserMessage(
                    content=completion.content, source="FacebookPostWriter"
                )
            ),
            DefaultTopicId(),
        )
