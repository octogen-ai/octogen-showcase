import argparse
import os
from contextlib import AbstractAsyncContextManager

from dotenv import find_dotenv, load_dotenv
from langchain_openai import ChatOpenAI
from octogen.shop_agent.base import ShopAgent
from octogen.shop_agent.checkpointer import ShopAgentInMemoryCheckpointSaver
from octogen.shop_agent.server import AgentServer
from octogen.showcase.feed.agent import create_feed_agent
from octogen.showcase.feed.router import history_router
from octogen.showcase.feed.schema import AgentResponse


def run_server(host: str, port: int) -> None:
    """Run the feed agent server."""
    # Load environment variables but don't validate MCP settings
    dotenv_path = os.getenv("OCTOGEN_DOTENV_PATH")
    if dotenv_path:
        load_dotenv(dotenv_path)
    else:
        load_dotenv(find_dotenv(usecwd=True))

    # Create server and attach checkpointer to its state
    server = AgentServer(
        title="Feed Agent",
        endpoint_prefix="showcase/feed",
        response_model=AgentResponse,
    )
    server.app.state.checkpointer = ShopAgentInMemoryCheckpointSaver()

    # Define the agent factory using the server's checkpointer
    def agent_factory() -> AbstractAsyncContextManager[ShopAgent]:
        """Factory function returning a configured feed agent."""
        return create_feed_agent(
            model=ChatOpenAI(model="gpt-4.1"),
            checkpointer=server.app.state.checkpointer,
        )

    server.set_agent_factory(agent_factory)

    # Manually include the history router
    server.app.include_router(history_router)

    # ------------------------------------------------------------------
    # Health-check endpoint
    # ------------------------------------------------------------------
    @server.app.get("/healthcheck", include_in_schema=False)
    async def healthcheck() -> dict[str, str]:
        """Simple liveness probe."""
        return {"status": "ok"}

    # Run server
    server.run(host=host, port=port)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the feed agent server")
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host address to bind the server to (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8004,
        help="Port number to bind the server to (default: 8004)",
    )

    args = parser.parse_args()
    run_server(host=args.host, port=args.port)
