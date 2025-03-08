from langchain_core.tools import tool
from langchain_community.chains.graph_qa.arangodb import ArangoGraphQAChain
from langgraph.types import Command, interrupt

@tool
def human_confirmation(query: str) -> str:
    """
    Use this tool to request human confirmation before sending messages or performing actions.
    When writing and sending content to someone, always confirm first. The query should include
    all details about what you're sending, to whom, and the exact content. This applies to emails,
    messages, channel changes, reservations, or any action requiring approval. Always include the
    complete content in your confirmation request so the user knows exactly what will be sent.
    
    Args:
        query: A string containing all the details of the action requiring confirmation, including:
            - The exact content being sent (full message text, email body, etc.)
            - The recipient(s) (name, email, channel, etc.)
            - The purpose or context of the action
            - Any other relevant details (time, date, location, etc.)
    
    Returns:
        The user's response to the confirmation request
    """
    human_response = interrupt({"query": query})
    return human_response["answer"]

@tool
def get_current_datetime() -> str:
    """
    Get the current date and time.
    
    Returns:
        The current date and time in a readable format
    """
    from datetime import datetime
    now = datetime.now()
    formatted_datetime = now.strftime("%Y-%m-%d %H:%M:%S")
    return f"Current date and time: {formatted_datetime}"


def public_db_query_factory(model, arango_graph, aql_generation_prompt):
    chain = ArangoGraphQAChain.from_llm(
        llm=model,
        graph=arango_graph,
        verbose=True,
        allow_dangerous_requests=True,
        aql_generation_prompt=aql_generation_prompt
    )
    
    @tool
    def public_db_query(query: str) -> str:
        """
        Translates natural language to AQL queries for the public database (common_db).
        
        Contains:
        1. Dine-out restaurants (addresses, ratings, cuisines)
        2. Online food ordering restaurants (menus, delivery times)
        
        Use for restaurant info, menus, and dining options.
        
        Use case-insensitive, generic queries for better results.

        Use this tool multiple times if you get empty results.
        """ 
        result = chain.invoke(query)
        return str(result["result"])
    
    return public_db_query
