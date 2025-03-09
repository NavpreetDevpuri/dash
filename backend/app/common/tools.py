import json
from langchain_core.tools import tool
from app.common.arangodb import ArangoGraphQAChain
from langgraph.types import Command, interrupt
from typing import Callable

def about_me_factory(arango_graph):
    cache_me_str = None
    @tool
    def about_me() -> str:
        """
        Use this tool to get information about the user.
        It contains information about the user's name, age, gender, email, phone, whatsapp number, slack email, slack username, location, and interests.
        """
        nonlocal cache_me_str
        try:
            if cache_me_str is None:
                # Use the provided arango_graph to query the me collection
                me_doc = arango_graph.db.collection('me').get('me')
                if me_doc:
                    cache_me_str = json.dumps(me_doc)
                    return cache_me_str
                else:
                    return "Could not find information about the user."
            else:
                return cache_me_str
        except Exception as e:
            return f"Error retrieving information about the user: {str(e)}"
    
    return about_me

def human_confirmation_factory(query_callback: Callable):
    @tool
    def human_confirmation(query: str) -> str:
        """
        Use this tool to request human confirmation before performing actions. Always confirm before
        sending content, including all details about what, to whom, and the exact content. If the user
        suggests changes, request confirmation again with the updated content.
        
        Args:
            query: String with action details including:
                - Exact content being sent
                - Recipient information
                - Purpose/context
                - Relevant details (time, date, location)
                - Use markdown to quote the message
        
        Returns:
            User's response to the confirmation request
        """
        query_callback(query)
        human_response = interrupt({"query": query})
        return human_response["answer"]
    
    return human_confirmation

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
        return_aql_result=True,
        perform_qa=False,
        top_k=5,
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
        return json.dumps(result["aql_result"])
    
    return public_db_query
