from langchain_core.prompts import PromptTemplate

PUBLIC_AQL_GENERATION_TEMPLATE = """Task: Generate an ArangoDB Query Language (AQL) query from a User Input.

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

Use case-insensitive searches (LIKE or REGEX_TEST with (?i)) for better matching.
Consider multiple search criteria (name, role, phone number) with OR operators.
Include wildcards (%) or partial matching when appropriate.
Run multiple targeted queries rather than one complex query when needed before giving up.
If initial results are insufficient, refine and retry with alternative search terms.

Under no circumstance should you generate an AQL Query that deletes any data whatsoever.

Bengaluru is also known as Bangalore so be careful with the search.
ALWAYS DO CASE INSENSITIVE SEARCHES.

ArangoDB Schema:
{adb_schema}

AQL Query Examples (Optional):
{aql_examples}

User Input:
{user_input}

AQL Query: 
"""

PUBLIC_AQL_GENERATION_PROMPT = PromptTemplate(
    input_variables=["adb_schema", "aql_examples", "user_input"],
    template=PUBLIC_AQL_GENERATION_TEMPLATE,
)


NETWORKX_QA_TEMPLATE = """Task: Generate a NetworkX algorithm from a User Input.

You are an expert in NetworkX and ArangoDB.

You are given an `ArangoDB Schema`. It is a JSON Object containing:
1. `Graph Schema`: Lists all Graphs within the ArangoDB Database Instance, along with their Edge Relationships.     

You are also given a `User Input`. It is a natural language description of the problem you need to solve.

You need to generate a NetworkX algorithm that can be used to solve the problem.

You should use the `ArangoDB Schema` to generate the NetworkX algorithm.
"""

NETWORKX_GENERATION_TEMPLATE = """Task: Generate Python code using NetworkX to analyze a graph.

I have a NetworkX Graph called `G_adb`. It has the following schema: {graph_schema}

I have the following graph analysis query: {user_input}.

Generate the Python Code required to answer the query using the `G_adb` object.

`G_adb` and `nx` are already imported.

The code is executing in google colab where you can also show the graph using `nx.draw()`. Feel free to use this.

Be very precise on the NetworkX algorithm you select to answer this query. Think step by step.

Only assume that networkx is installed, and other base python dependencies.

Always set the last variable as `FINAL_RESULT`, which represents the answer to the original query.

Only provide python code that I can directly execute via `exec()`. Do not provide any instructions.

Make sure that `FINAL_RESULT` stores a short & concise answer. Avoid setting this variable to a long sequence.

Return the code wrapped in 3 backticks (```).
Do not include any text except the generated Python code.
Do not provide explanations or apologies in your responses.

Your code:
"""

NETWORKX_FIX_PROMPT = """Task: Fix a NetworkX algorithm.

You are an expert in NetworkX and ArangoDB.

You are given a `NetworkX Algorithm`. It is a NetworkX algorithm that can be used to solve the problem.

You need to fix the NetworkX algorithm.

You should use the `ArangoDB Schema` to fix the NetworkX algorithm.

Return the code wrapped in 3 backticks (```).
Do not include any text except the generated Python code.
Do not provide explanations or apologies in your responses.

NetworkX Algorithm:
{code}

Error:
{error}

ArangoDB Schema:
{graph_schema}

User Input:
{user_input}


Your code:
""" 


NETWORKX_QA_PROMPT = PromptTemplate(
    input_variables=["adb_schema", "user_input"],
    template=NETWORKX_QA_TEMPLATE,
)

NETWORKX_GENERATION_PROMPT = PromptTemplate(
    input_variables=["adb_schema", "query"],
    template=NETWORKX_GENERATION_TEMPLATE,
)

NETWORKX_FIX_PROMPT = PromptTemplate(
    input_variables=["adb_schema", "networkx_algorithm"],
    template=NETWORKX_FIX_PROMPT,
)   