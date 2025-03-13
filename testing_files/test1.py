
import os
import uuid
from langchain_core.tools import tool

from arango import ArangoClient
from langchain_community.graphs import ArangoGraph
from langchain_community.chains.graph_qa.arangodb import ArangoGraphQAChain
import re
import networkx as nx


import nx_arangodb as nxadb
os.environ["DATABASE_HOST"] = "http://localhost:8529"
os.environ["DATABASE_USERNAME"] = "root"
os.environ["DATABASE_PASSWORD"] = "zxcv"
os.environ["DATABASE_NAME"] = "common_db"

# G_adb = nxadb.Graph(name="restaurants")

# print(G_adb.number_of_nodes(), G_adb.number_of_edges())

# 1. Connect to ArangoDB
db_client = ArangoClient(hosts="http://localhost:8529")
db = db_client.db("common_db", username="root", password="zxcv", verify=True)
arango_graph = ArangoGraph(db)

@tool
def text_to_aql_to_text(query: str):
    """This tool is available to invoke the
    ArangoGraphQAChain object, which enables you to
    translate a Natural Language Query into AQL, execute
    the query, and translate the result back into Natural Language.
    The database contains information about restaurants and their menus.
    Try to write multiple queries to get the best answer.
    Based on the query, you can use the tool multiple times.
    Try to find dishes first.
    make sure to query in case insensitive manner.
    """

    llm = ChatOpenAI(temperature=0, model_name="gpt-4o")

    chain = ArangoGraphQAChain.from_llm(
    	llm=llm,
    	graph=arango_graph,
    	verbose=True,
        allow_dangerous_requests=True
    )
    
    result = chain.invoke(query)

    return str(result["result"])

from langgraph.prebuilt import create_react_agent
from langchain_core.messages import AIMessage,HumanMessage,SystemMessage
from langgraph.checkpoint.memory import MemorySaver

checkpointer=MemorySaver()
#Create list of tools available to the agent
agent_tools=[text_to_aql_to_text]

from langchain_openai import ChatOpenAI

model=ChatOpenAI(model="gpt-4o-mini", temperature=0)
#System prompt
system_prompt = SystemMessage(
    """You are a helpful assistant that can answer questions and help with tasks."""
)

agent_graph=create_react_agent(
    model=model, 
    state_modifier=system_prompt,
    tools=agent_tools,
    checkpointer=checkpointer
)

# Interactive loop to keep asking questions

thread_id = str(uuid.uuid4())
while True:
    # Get user input
    user_question = input("Ask a question (or type 'exit' to quit): ")
    
    # Check if user wants to exit
    if user_question.lower() == 'exit':
        break
    
    # Create input for the agent
    inputs = {"messages": [HumanMessage(content=user_question)]}
    
    
    config = { "configurable": {"thread_id": thread_id} }
    # Invoke the agent
    result = agent_graph.invoke(inputs, config)
    
    for stream in agent_graph.stream(inputs, config, stream_mode="values"):
        message=stream["messages"][-1]
    if isinstance(message, tuple):
        print(message)
    else:
        message.pretty_print()
