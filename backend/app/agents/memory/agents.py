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