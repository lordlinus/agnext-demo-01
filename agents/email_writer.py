from typing import List

from autogen_core.base import MessageContext
from autogen_core.components import (DefaultTopicId, RoutedAgent,
                                     message_handler)
from autogen_core.components.models import (AssistantMessage,
                                            ChatCompletionClient, LLMMessage,
                                            SystemMessage, UserMessage)

from .data_types import GroupChatMessage, RequestToSpeak


class EmailWriterAgent(RoutedAgent):
    def __init__(self, model_client: ChatCompletionClient) -> None:
        super().__init__("EmailWriter")
        self._model_client = model_client
        self._chat_history: List[LLMMessage] = [
            SystemMessage(
                "Write a compelling email promoting our new product in less than 200 words.Email include the end signature to say - 'Your creative Multi agent Campaign Team'"
            )
        ]

    @message_handler
    async def handle_message(
        self, message: GroupChatMessage, ctx: MessageContext
    ) -> None:
        self._chat_history.append(message.body)
        source = message.body.source
        if source == "MarketingManager":
            # Received product information
            pass  # Handled in chat history
        elif source == "Editor":
            # Received feedback from editor
            pass  # Feedback added to chat history
        else:
            pass  # Other messages

    @message_handler
    async def handle_request_to_speak(
        self, message: RequestToSpeak, ctx: MessageContext
    ) -> None:
        completion = await self._model_client.create(self._chat_history)
        self._chat_history.append(
            AssistantMessage(content=completion.content, source="EmailWriter")
        )
        await self.publish_message(
            GroupChatMessage(
                body=UserMessage(content=completion.content, source="EmailWriter")
            ),
            DefaultTopicId(),
        )
