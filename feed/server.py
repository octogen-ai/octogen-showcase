from typing import AsyncGenerator

from dotenv import find_dotenv, load_dotenv
from langchain_openai import ChatOpenAI
from octogen.shop_agent.base import ShopAgent
from octogen.shop_agent.checkpointer import ShopAgentInMemoryCheckpointSaver
from octogen.shop_agent.server import AgentServer
from octogen.showcase.feed.agent import create_feed_agent
from octogen.showcase.feed.router import history_router
from octogen.showcase.feed.schema import AgentResponse


def run_server(host: str = "0.0.0.0", port: int = 8004) -> None:
    """Run the feed agent server."""
    # Load environment variables but don't validate MCP settings
    load_dotenv(find_dotenv(usecwd=True))

    # Create server and attach checkpointer to its state
    server = AgentServer(
        title="Feed Agent",
        endpoint_prefix="showcase/feed/chat",
        response_model=AgentResponse,
    )
    server.app.state.checkpointer = ShopAgentInMemoryCheckpointSaver()

    # Define the agent factory using the server's checkpointer
    def agent_factory() -> AsyncGenerator[ShopAgent, None]:
        """Factory function returning a configured feed agent."""
        return create_feed_agent(
            model=ChatOpenAI(model="gpt-4.1"),
            checkpointer=server.app.state.checkpointer,
        )

    server.set_agent_factory(agent_factory)

    # Manually include the history router
    server.app.include_router(history_router)

    # Run server
    server.run(host=host, port=port)


if __name__ == "__main__":
    run_server()
