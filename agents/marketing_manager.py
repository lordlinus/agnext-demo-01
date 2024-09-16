from typing import List

from autogen_core.components import (
    RoutedAgent,
    message_handler,
)
from autogen_core.components.models import (
    UserMessage,
)
from autogen_core.base import MessageContext
from .data_types import GroupChatMessage, RequestToSpeak
from autogen_core.base import MessageContext, AgentId
import asyncio


class MarketingManagerAgent(RoutedAgent):
    def __init__(
        self,
        product_info_provider: AgentId,
        writers: List[AgentId],
        editor: AgentId,
        output_queue: asyncio.Queue,
    ) -> None:
        super().__init__("MarketingManager")
        self._product_info_provider = product_info_provider
        self._writers = writers
        self._editor = editor
        self._current_writer_index = 0
        self._chat_history: List[GroupChatMessage] = []
        self._product_info = None
        self._approved_writers = set()
        self._output_queue = output_queue
        self._writer_drafts = {}  # Keep track of drafts per writer

    @message_handler
    async def handle_message(
        self, message: GroupChatMessage, ctx: MessageContext
    ) -> None:
        # print(f"Received message: {message.body.content} from {message.body.source}")
        self._chat_history.append(message)
        self._output_queue.put_nowait(message.to_dict())
        source = message.body.source

        if source == "ProductInformationProvider":
            # Received product information
            self._product_info = message.body.content
            # print(f"Received product information: {self._product_info}")

            # Send product information to all writer agents
            for writer in self._writers:
                await self.send_message(
                    GroupChatMessage(
                        body=UserMessage(
                            content=self._product_info, source="MarketingManager"
                        )
                    ),
                    writer,
                )
                # Request each speaker to speak
                await self.send_message(RequestToSpeak(), writer)

        elif source in ["EmailWriter", "FacebookPostWriter", "TwitterPostWriter"]:
            # Store the draft from the writer
            self._writer_drafts[source] = message.body.content

            # Send draft to Editor along with the writer's identifier
            await self.send_message(
                GroupChatMessage(
                    body=UserMessage(
                        content=message.body.content,
                        source=source,  # Include writer's source
                    )
                ),
                self._editor,
            )
            # Request Editor to speak
            await self.send_message(RequestToSpeak(), self._editor)

        elif source == "Editor":
            # Editor's feedback or approval
            content = message.body.content.upper()
            # Extract the writer's identifier from the previous message
            last_message = self._chat_history[-2]
            writer_source = last_message.body.source  # The writer's identifier

            if "APPROVE" in content:
                # Mark writer as approved
                self._approved_writers.add(writer_source)
                print(f"{writer_source}'s draft has been approved.")
                self._output_queue.put_nowait(
                    {
                        "body": {
                            "source": "Editor",
                            "target": writer_source,
                            "status": "approved",
                        }
                    }
                )

                if len(self._approved_writers) == len(self._writers):
                    print("All drafts have been approved.")
            else:
                # Send feedback back to the specific writer
                print(f"Asking {writer_source} to revise the draft.")
                await self.send_message(
                    GroupChatMessage(body=message.body),
                    AgentId(writer_source, "default"),  # Route to the correct writer
                )
                self._output_queue.put_nowait(
                    {
                        "source": "Editor",
                        "target": writer_source,
                        "status": "review",
                    }
                )
                # Request writer to revise
                await self.send_message(
                    RequestToSpeak(), AgentId(writer_source, "default")
                )

        elif source == "User":
            # Forward the product name to ProductInformationProviderAgent
            await self.send_message(
                GroupChatMessage(
                    body=UserMessage(
                        content=message.body.content, source="MarketingManager"
                    )
                ),
                self._product_info_provider,
            )
            # Request ProductInformationProviderAgent to speak
            await self.send_message(RequestToSpeak(), self._product_info_provider)
        else:
            # Handle other cases if needed
            print(f"Received message from {source}: {message.body.content}")
            pass

    @message_handler
    async def handle_request_to_speak(
        self, message: RequestToSpeak, ctx: MessageContext
    ) -> None:
        if self._product_info is None:
            # Start by requesting product information
            await self.send_message(RequestToSpeak(), self._product_info_provider)
        else:
            print("All agents have spoken. MarketingManager is idle.")
