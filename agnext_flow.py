import asyncio

from autogen_core.application import SingleThreadedAgentRuntime
from autogen_core.base import AgentId
from autogen_core.components import DefaultSubscription, DefaultTopicId
from autogen_core.components.models import AzureOpenAIChatCompletionClient, UserMessage
from promptflow.core import AzureOpenAIModelConfiguration
from promptflow.tracing import trace

from agents.data_types import GroupChatMessage
from agents.editor import EditorAgent
from agents.email_writer import EmailWriterAgent
from agents.facebook_post_writer import FacebookPostWriterAgent
from agents.marketing_manager import MarketingManagerAgent
from agents.product_info_provider import ProductInfomationProviderAgent
from agents.twitter_post_writer import TwitterPostWriterAgent


class AGNextFlow:
    def __init__(self, model_config: AzureOpenAIModelConfiguration, test_mode=True):
        self.model_config = model_config
        self.output_queue = asyncio.Queue()
        self.test_mode = test_mode

    @trace
    async def __call__(
        self, question: str, chat_history: list = None
    ):  # -> Generator[Any, Any, None]:
        run_task = asyncio.create_task(self.run(question, self.output_queue))
        # Read messages from the output queue
        while True:
            message = await self.output_queue.get()
            if message is None:
                break
            yield message
            await asyncio.sleep(0.1)
        await run_task

    async def run(self, question: str, output_queue: asyncio.Queue):
        aoai_model_client = AzureOpenAIChatCompletionClient(
            model="gpt-4o",
            api_key=self.model_config.api_key,
            api_version="2024-02-15-preview",
            azure_endpoint="https://ss-cchat-sf-ai-aiservices7wx5mg43sbnl4.openai.azure.com/",
            model_capabilities={
                "vision": True,
                "function_calling": True,
                "json_output": True,
            },
        )

        self.runtime = SingleThreadedAgentRuntime()

        editor_type = await self.runtime.register(
            "Editor",
            lambda: EditorAgent(model_client=aoai_model_client),
            subscriptions=lambda: [DefaultSubscription()],
        )
        product_info_provider_type = await self.runtime.register(
            "ProductInformationProvider",
            lambda: ProductInfomationProviderAgent(model_client=aoai_model_client),
            subscriptions=lambda: [DefaultSubscription()],
        )
        email_writer_type = await self.runtime.register(
            "EmailWriter",
            lambda: EmailWriterAgent(model_client=aoai_model_client),
            subscriptions=lambda: [DefaultSubscription()],
        )
        facebook_writer_type = await self.runtime.register(
            "FacebookPostWriter",
            lambda: FacebookPostWriterAgent(model_client=aoai_model_client),
            subscriptions=lambda: [DefaultSubscription()],
        )
        twitter_writer_type = await self.runtime.register(
            "TwitterPostWriter",
            lambda: TwitterPostWriterAgent(model_client=aoai_model_client),
            subscriptions=lambda: [DefaultSubscription()],
        )

        # Create AgentId instances for each agent
        product_info_provider_id = AgentId(product_info_provider_type, "default")
        email_writer_id = AgentId(email_writer_type, "default")
        facebook_writer_id = AgentId(facebook_writer_type, "default")
        twitter_writer_id = AgentId(twitter_writer_type, "default")
        editor_id = AgentId(editor_type, "default")
        # Register the MarketingManagerAgent
        await self.runtime.register(
            "MarketingManager",
            lambda: MarketingManagerAgent(
                product_info_provider=product_info_provider_id,
                writers=[email_writer_id, facebook_writer_id, twitter_writer_id],
                editor=editor_id,
                output_queue=output_queue,
            ),
            subscriptions=lambda: [DefaultSubscription()],
        )

        self.runtime.start()
        await self.runtime.publish_message(
            GroupChatMessage(
                UserMessage(
                    content=question,
                    source="User",
                )
            ),
            DefaultTopicId(),
        )

        await self.runtime.stop_when_idle()
        self.output_queue.put_nowait(None)
