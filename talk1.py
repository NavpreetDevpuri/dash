import json
import os
from arango import ArangoClient
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from langchain_community.graphs import ArangoGraph
from langchain_community.chains.graph_qa.arangodb import ArangoGraphQAChain
import re
import networkx as nx


import nx_arangodb as nxadb
os.environ["DATABASE_HOST"] = "http://localhost:8529"
os.environ["DATABASE_USERNAME"] = "root"
os.environ["DATABASE_PASSWORD"] = "zxcv"
os.environ["DATABASE_NAME"] = "user_1235"

# G_adb = nxadb.Graph(name="restaurants")

# print(G_adb.number_of_nodes(), G_adb.number_of_edges())

# 1. Connect to ArangoDB
db_client = ArangoClient(hosts="http://localhost:8529")
db = db_client.db("user_1235", username="root", password="zxcv", verify=True)
arango_graph = ArangoGraph(db)

AQL_GENERATION_TEMPLATE = """Task: Generate an ArangoDB Query Language (AQL) query from a User Input.

You are an ArangoDB Query Language (AQL) expert responsible for translating a `User Input` into an ArangoDB Query Language (AQL) query.

You are given an `ArangoDB Schema`. It is a JSON Object containing:
1. `Graph Schema`: Lists all Graphs within the ArangoDB Database Instance, along with their Edge Relationships.
2. `Collection Schema`: Lists all Collections within the ArangoDB Database Instance, along with their document/edge properties and a document/edge example.

You may also be given a set of `AQL Query Examples` to help you create the `AQL Query`. If provided, the `AQL Query Examples` should be used as a reference, similar to how `ArangoDB Schema` should be used.

Things you should do:
- Think step by step.
- Rely on `ArangoDB Schema` and `AQL Query Examples` (if provided) to generate the query.
- Begin the `AQL Query` by the `WITH` AQL keyword to specify all of the ArangoDB Collections required.
- Return the `AQL Query` wrapped in 3 backticks (```).
- Use only the provided relationship types and properties in the `ArangoDB Schema` and any `AQL Query Examples` queries.
- Only answer to requests related to generating an AQL Query.
- If a request is unrelated to generating AQL Query, say that you cannot help the user.

Things you should not do:
- Do not use any properties/relationships that can't be inferred from the `ArangoDB Schema` or the `AQL Query Examples`. 
- Do not include any text except the generated AQL Query.
- Do not provide explanations or apologies in your responses.
- Do not generate an AQL Query that removes or deletes any data.

Under no circumstance should you generate an AQL Query that deletes any data whatsoever.

Additional notes:
- you can answer questions about the user's contacts. 
- you can answer questions about the user's food preferences.
- you can answer questions about the user's restaurant preferences.

ArangoDB Schema:
{adb_schema}

AQL Query Examples (Optional):
{aql_examples}

User Input:
{user_input}

AQL Query: 
"""

@tool
def text_to_aql_to_text(query: str):
    """
    This tool translates a Natural Language Query into AQL, executes it, and returns the result. Even if the query is not related to the user's contacts, food preferences, or restaurant preferences, you can still answer the query.
    """
    llm = ChatOpenAI(temperature=0, model_name="gpt-4o")
    chain = ArangoGraphQAChain.from_llm(
        llm=llm,
        graph=arango_graph,
        verbose=True,
        allow_dangerous_requests=True,
    )
    result = chain.invoke(query)
    return str(result["result"])

@tool
def text_to_nx_algorithm_to_text(query: str):
    """This tool executes a NetworkX algorithm on the ArangoDB Graph."""
    llm = ChatOpenAI(temperature=0, model_name="gpt-4o")
    
    print("1) Generating NetworkX code")
    text_to_nx = llm.invoke(f"""
    I have a NetworkX Graph called `G_adb`. It has the following schema: {arango_graph.schema}
    
    I have the following graph analysis query: {query}.
    
    Generate the Python Code required to answer the query using the `G_adb` object.
    
    Be very precise on the NetworkX algorithm you select to answer this query. Think step by step.
    
    Only assume that networkx is installed, and other base python dependencies.
    
    Always set the last variable as `FINAL_RESULT`, which represents the answer to the original query.
    
    Only provide python code that I can directly execute via `exec()`. Do not provide any instructions.
    
    Make sure that `FINAL_RESULT` stores a short & concise answer. Avoid setting this variable to a long sequence.
    
    Your code:
    """).content

    text_to_nx_cleaned = re.sub(r"^```python\n|```$", "", text_to_nx, flags=re.MULTILINE).strip()
    print('-'*10)
    print(text_to_nx_cleaned)
    print('-'*10)

    print("\n2) Executing NetworkX code")
    global_vars = {"G_adb": G_adb, "nx": nx}
    local_vars = {}

    try:
        exec(text_to_nx_cleaned, global_vars, local_vars)
        text_to_nx_final = text_to_nx
    except Exception as e:
        print(f"EXEC ERROR: {e}")
        return f"EXEC ERROR: {e}"

    print('-'*10)
    FINAL_RESULT = local_vars.get("FINAL_RESULT", "Error: No result generated.")
    print(f"FINAL_RESULT: {FINAL_RESULT}")
    print('-'*10)

    print("3) Formulating final answer")
    nx_to_text = llm.invoke(f"""
        I have a NetworkX Graph called `G_adb`. It has the following schema: {arango_graph.schema}
        
        I have the following graph analysis query: {query}.
        
        I have executed the following python code to help me answer my query:
        
        ---
        {text_to_nx_final}
        ---
        
        The `FINAL_RESULT` variable is set to the following: {FINAL_RESULT}.
        
        Based on my original Query and FINAL_RESULT, generate a short and concise response to
        answer my query.
        
        Your response:
    """).content

    return nx_to_text

# 4. Create an LLM agent with the tools
llm = ChatOpenAI(temperature=0, model_name="gpt-4o")
tools = [text_to_aql_to_text, text_to_nx_algorithm_to_text]
agent = create_react_agent(llm, tools)

print(json.dumps(arango_graph.schema, indent=2))
# 5. Query the agent
query = "Who is my wife?"
response = agent.invoke({"messages": [{"role": "user", "content": query}]})
print(response["messages"][-1].content)
