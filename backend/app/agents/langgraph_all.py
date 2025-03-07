from typing import Annotated
from typing_extensions import TypedDict

from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId, tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.types import Command, interrupt


import os

# Define a custom State with messages and extra keys (name, birthday)
class State(TypedDict):
    messages: Annotated[list, add_messages]
    name: str
    birthday: str

# ---------------------------
# Define a human assistance tool with an explicit description.
@tool(description="Request human assistance to verify provided details and update the state accordingly.")
def human_assistance(
    name: str, birthday: str, tool_call_id: Annotated[str, InjectedToolCallId]
) -> str:
    """
    Request assistance from a human to verify provided name and birthday.
    Uses interrupt to pause execution until human input is provided.
    """
    human_response = interrupt({"question": "Is this correct?", "name": name, "birthday": birthday})
    if human_response.get("correct", "").lower().startswith("y"):
        verified_name, verified_birthday, response = name, birthday, "Correct"
    else:
        verified_name = human_response.get("name", name)
        verified_birthday = human_response.get("birthday", birthday)
        response = f"Correction: {human_response}"
    state_update = {
        "name": verified_name,
        "birthday": verified_birthday,
        "messages": [ToolMessage(response, tool_call_id=tool_call_id)],
    }
    return Command(update=state_update)

# # Define a web search tool (using Tavily) and bind both tools.
# search_tool = TavilySearchResults(max_results=2)

# ---------------------------
# Define a web search tool with hardcoded results using a tool decorator.
@tool(description="Perform a web search and return hardcoded results.")
def search_tool() -> str:
    """
    Returns hardcoded search results for LangGraph.
    """
    results = [
        {"url": "https://www.langchain.com/langgraph", "content": "Build and scale agentic applications with LangGraph Platform."},
        {"url": "https://langchain-ai.github.io/langgraph/tutorials/introduction/", "content": "LangGraph offers new ways to create complex, stateful, and interactive AI systems."}
    ]
    return results

tools = [search_tool, human_assistance]

# Bind tools to our LLM using ChatOpenAI with a hardcoded API key.
llm = ChatOpenAI(
    temperature=0,
    model_name="gpt-4o",
)
llm_with_tools = llm.bind_tools(tools)

# ---------------------------
# Define the chatbot node function.
def chatbot(state: State):
    message = llm_with_tools.invoke(state["messages"])
    # Ensure that only one tool call is executed, if any.
    # assert len(message.tool_calls) <= 1
    return {"messages": [message]}

# ---------------------------
# Build the StateGraph using our custom State.
graph_builder = StateGraph(State)
graph_builder.add_node("chatbot", chatbot)
tool_node = ToolNode(tools=tools)
graph_builder.add_node("tools", tool_node)
# Conditional routing: if the chatbot's output includes a tool call, route to "tools".
graph_builder.add_conditional_edges("chatbot", tools_condition)
graph_builder.add_edge("tools", "chatbot")
graph_builder.add_edge(START, "chatbot")

# Enable memory checkpointing using an in-memory checkpointer.
memory = MemorySaver()
graph = graph_builder.compile(checkpointer=memory)

# ---------------------------
# EXAMPLE USAGE
# Use a unique thread_id so the conversation state is persisted.
config = {"configurable": {"thread_id": "1"}}

# (1) Start a conversation with a user input.
initial_input = {
    "messages": [{"role": "user", "content": "Hi, what is LangGraph?"}],
    "name": "",
    "birthday": ""
}
print("=== Initial Conversation ===")
for event in graph.stream(initial_input, config, stream_mode="values"):
    event["messages"][-1].pretty_print()

# (2) Manually update the state with custom keys.
graph.update_state(config, {"name": "LangGraph", "birthday": "Jan 17, 2024"})

# (3) Continue the conversation (the chatbot may trigger human assistance if needed).
followup = {"messages": [{"role": "user", "content": "Can you verify your release date using human assistance?"}]}
print("\n=== Follow-up Conversation (may trigger human assistance) ===")
for event in graph.stream(followup, config, stream_mode="values"):
    event["messages"][-1].pretty_print()

# (4) Time Travel: Retrieve state history and resume from an earlier checkpoint.
to_replay = None
print("\n=== State History Checkpoints ===")
for state in graph.get_state_history(config):
    print("Num Messages: ", len(state.values["messages"]), "Next: ", state.next)
    print("-" * 80)
    if len(state.values["messages"]) == 6:
        to_replay = state

if to_replay:
    print("\n=== Resuming from Checkpoint ===", to_replay.config)
    for event in graph.stream(None, to_replay.config, stream_mode="values"):
        if "messages" in event:
            event["messages"][-1].pretty_print()