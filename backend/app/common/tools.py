from langchain_core.tools import tool
from langchain_community.chains.graph_qa.arangodb import ArangoGraphQAChain


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
