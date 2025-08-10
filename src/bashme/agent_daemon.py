from contextlib import asynccontextmanager
import os
import logging

import click
from fastapi import FastAPI
from langchain_core.messages.human import HumanMessage
from langgraph.checkpoint.base import Checkpoint
from langgraph.graph.message import AnyMessage
from pydantic import BaseModel
from pydantic_core import to_json
import uvicorn

from bashme.client import create_graph, mcp_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --- Pydantic Models for API validation ---
class ShellContext(BaseModel):
    current_command: str
    fzf_query: str | None = None
    cursor_position: int
    pwd: str
    histfile: str
    path: str


agent_executor = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    This function runs once when the server starts.
    It creates and "warms up" the LangGraph agent.
    """
    global agent_executor
    api_key = os.environ.get("BASHME_API_KEY")
    if not api_key:
        logger.error("BASHME_API_KEY is not set. The agent will not work.")
        return

    logger.info("Creating and warming up the LangGraph agent...")
    try:
        # We need a session to build the graph
        async with mcp_client.session("bashme_core") as session:
            agent_executor = await create_graph(session, api_key)
        logger.info("Agent is ready.")
    except Exception as e:
        logger.exception(f"Failed to create agent on startup: {e}")
    yield


app = FastAPI(lifespan=lifespan)


@app.post("/generate")
async def generate_command(context: ShellContext) -> dict:
    """The main endpoint that receives shell context and returns suggestions."""
    if not agent_executor:
        return {"suggestions": ["# Agent not initialized. Check server logs."]}

    # Format the input as expected by the system prompt
    input_context = context.model_dump()
    user_message = f"""
    Here is the current shell context:
    ```json
    {to_json(input_context, indent=2)}
    ```
    """

    try:
        # Run the agent with the provided context
        response: Checkpoint = await agent_executor.ainvoke({
            "messages": [HumanMessage(content=user_message)]
        })
        final_message: AnyMessage = response["messages"][-1]
        logger.info(f"{final_message=}")
        # Return the content in a structured way
        if final_message and final_message.content:
            return {"suggestions": final_message.content.strip().split("\n")}
        return {"suggestions": []}

    except Exception as e:
        logger.exception(f"Error invoking agent: {e}")
        return {"suggestions": [f"# Error: {e}"]}


@click.command()
@click.option("--host", default="localhost")
@click.option("--port", type=int, default=50052)
@click.option("--log-level", default="INFO")
def main(host, port, log_level):
    uvicorn.run(app, host=host, port=port, log_level=log_level.lower())


if __name__ == "__main__":
    main()
