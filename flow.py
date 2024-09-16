import asyncio
import os

import dotenv
from promptflow.core import AzureOpenAIModelConfiguration

from agnext_flow import AGNextFlow

dotenv.load_dotenv()
if __name__ == "__main__":
    from promptflow.tracing import start_trace

    # start_trace()
    config = AzureOpenAIModelConfiguration(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    )

    flow = AGNextFlow(config)

    async def main():
        async for message in flow("Samsung Galaxy S21 Ultra", chat_history=[]):
            print(message)

    asyncio.run(main())
