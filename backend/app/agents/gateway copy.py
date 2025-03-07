# Creating the routing agent

from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, ToolMessage
import operator
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
import functools
from langgraph.checkpoint.memory import MemorySaver
from IPython.display import Image


GATEWAY_SYSTEM_PROMPT = """

"""


# Define the RouterAgentState
class RouterAgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]

# Helper function to invoke an agent
def agent_node(state, agent, name, config):
    # Extract thread-id from request for conversation memory if needed
    thread_id = config.get("metadata", {}).get("thread_id", None)
    # Set the config for calling the agent
    agent_config = {"configurable": {"thread_id": thread_id}} if thread_id else {}

    # Invoke the agent with the state
    result = agent.invoke(state, agent_config)

    # Convert the agent output into a format that is suitable to append to the global state
    if isinstance(result, ToolMessage):
        pass
    else:
        final_result = AIMessage(content=result['messages'][-1].content)
    return {
        "messages": [final_result]
    }

# Define the MemoryAgent
class MemoryAgent:
    def __init__(self, model, system_prompt, debug=False):
        self.system_prompt = system_prompt
        self.debug = debug
        # Setup the agent graph
        agent_graph = StateGraph(RouterAgentState)
        agent_graph.add_node("memory_llm", self.call_llm)
        agent_graph.set_entry_point("memory_llm")
        self.memory = MemorySaver()
        # Compile the graph
        self.agent_graph = agent_graph.compile(checkpointer=self.memory)
        self.model = model

    def call_llm(self, state: RouterAgentState):
        messages = state["messages"]
        if self.system_prompt:
            messages = [SystemMessage(content=self.system_prompt)] + messages
        result = self.model.invoke(messages)
        if self.debug:
            print(f"MemoryAgent LLM Returned: {result}")
        return {"messages": [result]}

# Define the MiscellaneousAgent
class MiscellaneousAgent:
    def __init__(self, model, system_prompt, debug=False):
        self.system_prompt = system_prompt
        self.debug = debug
        # Setup the agent graph
        agent_graph = StateGraph(RouterAgentState)
        agent_graph.add_node("misc_llm", self.call_llm)
        agent_graph.set_entry_point("misc_llm")
        self.memory = MemorySaver()
        # Compile the graph
        self.agent_graph = agent_graph.compile(checkpointer=self.memory)
        self.model = model

    def call_llm(self, state: RouterAgentState):
        messages = state["messages"]
        if self.system_prompt:
            messages = [SystemMessage(content=self.system_prompt)] + messages
        result = self.model.invoke(messages)
        if self.debug:
            print(f"MiscellaneousAgent LLM Returned: {result}")
        return {"messages": [result]}

# Create instances of the agents
import openai

# Initialize the OpenAI API client with your API key

from langchain.chat_models import ChatOpenAI
from langchain.schema import AIMessage, HumanMessage, SystemMessage

model = ChatOpenAI(temperature=0, model_name="gpt-4o")


class ChatGPTModel:
    def invoke(self, messages):
        # Convert messages to LangChain's message format
        lc_messages = []
        for message in messages:
            if message.role == "system":
                lc_messages.append(SystemMessage(content=message.content))
            elif message.role == "user":
                lc_messages.append(HumanMessage(content=message.content))
            elif message.role == "assistant":
                lc_messages.append(AIMessage(content=message.content))
        # Get the response from the model
        response = model(lc_messages)
        return response.content

memory_agent_system_prompt = """
You are an assistant that processes human messages.
If a human message contains any personal information that can be remembered,
you need to remember it by storing it in the form of nodes and edges.

And at the end you also reply.
"""

memory_agent = MemoryAgent(
    model,
    system_prompt=memory_agent_system_prompt,
    debug=False
)

misc_agent_system_prompt = """
You are an assistant that handles miscellaneous requests from human messages. You should clearly answer only those messages which do not have any personal information about the human.
"""

misc_agent = MiscellaneousAgent(
    model,
    system_prompt=misc_agent_system_prompt,
    debug=False
)

# Define agent nodes
memory_node = functools.partial(agent_node, agent=memory_agent.agent_graph, name="Memory_Agent")
misc_node = functools.partial(agent_node, agent=misc_agent.agent_graph, name="Miscellaneous_Agent")

# Define the RouterAgent
class RouterAgent:
    def __init__(self, model, system_prompt, debug=False):
        self.system_prompt = system_prompt
        self.model = model
        self.debug = debug

        router_graph = StateGraph(RouterAgentState)
        router_graph.add_node("Router", self.call_llm)
        router_graph.add_node("Memory_Agent", memory_node)
        router_graph.add_node("Miscellaneous_Agent", misc_node)

        router_graph.add_conditional_edges(
            "Router",
            self.find_route,
            {
                "COLLECT_MEMORY_AND_ANSWER": "Memory_Agent",
                "MISCELLANEOUS": "Miscellaneous_Agent",
                "END": END
            }
        )

        # Agents lead to END
        router_graph.add_edge("Memory_Agent", END)
        router_graph.add_edge("Miscellaneous_Agent", END)

        # Set the starting point
        router_graph.set_entry_point("Router")
        self.router_graph = router_graph.compile()

    def call_llm(self, state: RouterAgentState):
        messages = state["messages"]
        if self.debug:
            print(f"RouterAgent received messages: {messages}")
        if self.system_prompt:
            messages = [SystemMessage(content=self.system_prompt)] + messages
        result = self.model.invoke(messages)
        if self.debug:
            print(f"RouterAgent LLM result: {result}")
        return {"messages": [result]}

    def find_route(self, state:RouterAgentState):
        last_message = state["messages"][-1]
        if self.debug:
            print(f"RouterAgent: Last LLM result: {last_message}")
        # Determine the destination based on last message content
        return last_message.content


# Start Generation Here
if __name__ == "__main__":
    # Instantiate the model and agents
    model = ChatOpenAI(temperature=0, model_name="gpt-4o")
    system_prompt = f"""
    You are an assistant that routes requests to the appropriate agent.
    You will receive a user message, and you need to decide which agent should handle it.
    Output only the name of the agent: 'COLLECT_MEMORY_AND_ANSWER' or 'MISCELLANEOUS'

    COLLECT_MEMORY_AND_ANSWER: {memory_agent_system_prompt}
    MISCELLANEOUS: {misc_agent_system_prompt}
    """

    router_agent = RouterAgent(model=model, system_prompt=system_prompt, debug=True)
    
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit", "stop"]:
            print("Exiting chat.")
            break
        messages = [HumanMessage(content=user_input)]
        response = router_agent.router_graph.invoke({"messages": messages})
        print(f"Agent: {response['messages'][-1].content}")
