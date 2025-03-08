import json
from langchain_core.tools import tool
from langchain_community.chains.graph_qa.arangodb import ArangoGraphQAChain
from langgraph.types import Command, interrupt
from typing import Callable

def about_me_factory(arango_graph):
    cache_me_str = None
    @tool
    def about_me() -> str:
        """
        Use this tool to get information about the user.
        It contains information about the user's name, age, gender, location, and interests.
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
        Use this tool to request human confirmation before sending messages or performing actions.
        When writing and sending content to someone, always confirm first. The query should include
        all details about what you're sending, to whom, and the exact content. This applies to emails,
        messages, channel changes, reservations, or any action requiring approval. Always include the
        complete content in your confirmation request so the user knows exactly what will be sent.

        When user give some suggestions, always ask for confirmation again with updated query.
        
        Args:
            query: A string containing all the details of the action requiring confirmation, such as:
                - The exact content being sent (full message text, email body, etc.)
                - The recipient(s) (name, email, channel, etc.)
                - The purpose or context of the action
                - Any other relevant details (time, date, location, etc.)
                - Use proper markdown formatting to quote the confirmation message.
        
        Returns:
            The user's response to the confirmation request
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
