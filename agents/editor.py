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
from datetime import datetime
from .data_types import GroupChatMessage, RequestToSpeak


class EditorAgent(RoutedAgent):
    def __init__(self, model_client: ChatCompletionClient) -> None:
        super().__init__("Editor")
        self._model_client = model_client
        self._chat_history: List[LLMMessage] = [
            SystemMessage(
                f"You are an social media post and email editor. Review the draft and reply with 'APPROVE' if it's good, or provide suggestions to make for improvement. Consider the below guidelines when reviewing:\n\n1. Is the content engaging and informative?\n2. Is the tone appropriate for the target audience?\n3. Are there any grammatical errors or typos? 3. Request to include current month and year. Current Month and Year is {datetime.now().strftime('%B %Y')}."  # noqa
            )
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
        # print(f"Editor: {completion.content}")
        self._chat_history.append(
            AssistantMessage(content=completion.content, source="Editor")
        )
        await self.publish_message(
            GroupChatMessage(
                body=UserMessage(content=completion.content, source="Editor")
            ),
            DefaultTopicId(),
        )
