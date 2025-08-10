import asyncio
import os
import logging
from typing import TypedDict, Annotated

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

from bashme.server import port

mcp_client = MultiServerMCPClient({
    "bashme_core": {
        "transport": "streamable_http",
        "url": f"http://localhost:{port}/mcp",
    },
})
logger = logging.getLogger(__name__)


class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]


async def create_graph(session, api_key):
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-lite",
        temperature=0.2,
        api_key=api_key,
        retry=2,
        thinking_budget=0,
    )

    tools = await load_mcp_tools(session)
    llm_with_tool = llm.bind_tools(tools)
    logger.debug(f"{tools=}")

    system_prompt = await load_mcp_prompt(session, "system_prompt")
    prompt_template = ChatPromptTemplate([
        ("system", system_prompt[0].content),
        MessagesPlaceholder("messages"),
    ])
    llm_chain = prompt_template | llm_with_tool

    # Nodes
    async def chat_node(state: State) -> dict:
        logger.debug(f"{state=}")
        response = await llm_chain.ainvoke({"messages": state["messages"]})
        logger.debug(f"{response=}")
        return {"messages": [response]}

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
