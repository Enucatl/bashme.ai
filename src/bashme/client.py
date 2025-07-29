import asyncio
import os
import logging
from typing import TypedDict

from langchain_core.messages.human import HumanMessage
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.prompts import load_mcp_prompt
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import AnyMessage, add_messages
from langgraph.prebuilt import tools_condition, ToolNode
from pydantic_core import to_json
import asyncclick as click

client = MultiServerMCPClient({
    "bashme": {
        "command": "uv",
        "args": ["run", "mcp", "run", "./src/bashme/server.py"],
        "transport": "stdio",
    },
})
logger = logging.getLogger(__name__)


class State(TypedDict):
    messages: list[AnyMessage]


async def create_graph(session, api_key):
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-lite", temperature=0.2, api_key=api_key
    )

    tools = await load_mcp_tools(session)
    llm_with_tool = llm.bind_tools(tools)

    system_prompt = await load_mcp_prompt(session, "system_prompt")
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_prompt[0].content),
        MessagesPlaceholder("messages"),
    ])
    llm_chain = prompt_template | llm_with_tool

    # Nodes
    async def chat_node(state: State) -> dict:
        logger.debug(f"{state=}")
        response = await llm_chain.ainvoke({"messages": state["messages"]})
        logger.debug(f"{response=}")
        return {"messages": add_messages(state["messages"], [response])}

    # Building the graph
    graph_builder = StateGraph(State)
    graph_builder.add_node("chat_node", chat_node)
    graph_builder.add_node("tool_node", ToolNode(tools=tools))
    graph_builder.add_edge(START, "chat_node")
    graph_builder.add_conditional_edges(
        "chat_node", tools_condition, {"tools": "tool_node", "__end__": END}
    )
    graph_builder.add_edge("tool_node", "chat_node")
    graph = graph_builder.compile()
    return graph


@click.command()
@click.option(
    "--current-command", required=True, help="The current command line content"
)
@click.option("--fzf-query", default=None, help="The current query from the fzf input")
@click.option(
    "--cursor-position",
    required=True,
    type=int,
    help="The cursor position in the command line",
)
@click.option("--pwd", required=True, help="The current working directory")
@click.option("--os-info", default="Ubuntu", help="Information about the OS")
@click.option("--api-key", default=os.environ.get("API_KEY"))
async def main(current_command, fzf_query, cursor_position, pwd, os_info, api_key):
    """
    This client provides AI-powered bash completions.
    It is intended to be called by a bash script, not run interactively.
    """
    logging.basicConfig(level=logging.DEBUG)
    if not api_key:
        # Fail gracefully if the API key is missing
        return

    # 1. Format the input as expected by the system prompt
    input_context = {
        "current_command": current_command,
        "fzf_query": fzf_query,
        "cursor_position": cursor_position,
        "pwd": pwd,
        "os_info": os_info,
    }
    logger.info(input_context)
    user_message = f"""
    Here is the current shell context:
    ```json
    {to_json(input_context, indent=2)}
    ```
    """
    async with client.session("bashme") as session:
        agent = await create_graph(session, api_key)
        response = await agent.ainvoke({
            "messages": [HumanMessage(content=user_message)]
        })
        final_message = response["messages"][-1]
        if final_message and final_message.content:
            print(final_message.content)


if __name__ == "__main__":
    asyncio.run(main())
