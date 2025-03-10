import json
import re
from langchain_core.tools import tool
from app.common.arangodb import ArangoGraphQAChain, ArangoNetworkxQAChain
from langgraph.types import Command, interrupt
from typing import Callable

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.common.load_arangodb_graph_to_networkx import load_arangodb_graph_to_networkx

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

        "Popularity" field is not what we show, we show ratings and reviews because it is for internal use.
        """ 
        result = chain.invoke(query)
        return json.dumps(result["aql_result"])
    
    return public_db_query

def private_db_query_factory(model, arango_graph, aql_generation_prompt):
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
    def private_db_query(query: str) -> str:
        """
        Translates natural language to AQL queries for the private database (private_db).
        
        Contains:
        1. User's contacts (name, phone number, email, etc.)
        2. User's messages (content, sender, timestamp, etc.)
        3. User's groups (name, participants, messages, etc.)
        4. User preferences (language, timezone, etc.)

        Do not use user name in this tool because those are simple contacts documents.
        
        Use case-insensitive, generic queries for better results.

        Use this tool multiple times if you get empty results.
        """ 
        result = chain.invoke(query)
        return json.dumps(result["aql_result"])
    
    return private_db_query


def text_to_nx_algorithm_for_public_db_factory(model, db, arango_graph, graph_schema):
    G_adb = load_arangodb_graph_to_networkx(db, arango_graph)
    chain = ArangoNetworkxQAChain.from_llm(
        G_adb=G_adb,
        llm=model,
        db=db,
        graph=arango_graph,
        verbose=True,
        allow_dangerous_requests=True,
        return_nx_result=True,
        graph_schema=graph_schema
    )
    @tool
    def text_to_nx_algorithm_for_public_db(query):
        """
        This tool is for public database.
        This tool is available to invoke a NetworkX Algorithm on
        the ArangoDB Graph. You are responsible for accepting the
        Natural Language Query, establishing which algorithm needs to
        be executed, executing the algorithm, and translating the results back
        to Natural Language, with respect to the original query.

        If the query (e.g traversals, shortest path, etc.) can be solved using the Arango Query Language, then do not use
        this tool.

        NOTE: You can also use this for visualizing the graph because it has `nx.draw()`.

        Public database contains:
        1. Dine-out restaurants (addresses, ratings, cuisines)
        2. Online food ordering restaurants (menus, dishes)
        """

        result = chain.invoke(query)
        return json.dumps(result["nx_result"])

    return text_to_nx_algorithm_for_public_db