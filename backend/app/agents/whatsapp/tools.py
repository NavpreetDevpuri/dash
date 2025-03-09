import json
from typing import Dict, List, Any, Optional
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_community.graphs import ArangoGraph
from app.common.arangodb import ArangoGraphQAChain


@tool
def save_contact(name: str, phone_number: str) -> str:
    """
    Save a new contact to your contacts list.
    
    Args:
        name: The name of the contact
        phone_number: The phone number of the contact
    
    Returns:
        Confirmation message
    """
    # For now, just print the payload
    payload = {"action": "save_contact", "name": name, "phone_number": phone_number}
    print(f"TOOL EXECUTION: {payload}")
    return f"Contact {name} with number {phone_number} has been saved."


@tool
def send_message(recipient: str, message: str) -> str:
    """
    Send a WhatsApp message to a contact or group.
    
    Args:
        recipient: The phone number with country code without + symbol (e.g., 14155552671)
        message: The message content to send
    
    Returns:
        Confirmation message
    """
    # For now, just print the payload
    payload = {"action": "send_message", "recipient": recipient, "message": message}
    print(f"TOOL EXECUTION: {payload}")
    return f"Message sent to {recipient}: '{message}'"


@tool
def create_group(group_name: str, participants: List[str]) -> str:
    """
    Create a new WhatsApp group with the specified participants.
    
    Args:
        group_name: The name for the new group
        participants: Array of phone numbers with country code without + symbol (e.g., ["14155552671", "14155552672"])
    
    Returns:
        Confirmation message
    """
    payload = {"action": "create_group", "group_name": group_name, "participants": participants}
    print(f"TOOL EXECUTION: {payload}")
    return f"Group '{group_name}' created with participants: {participants}"


@tool
def leave_group(group_name: str) -> str:
    """
    Leave a WhatsApp group.
    
    Args:
        group_name: The name of the group to leave
    
    Returns:
        Confirmation message
    """
    payload = {"action": "leave_group", "group_name": group_name}
    print(f"TOOL EXECUTION: {payload}")
    return f"You have left the group '{group_name}'"


@tool
def add_to_group(group_name: str, participants: List[str]) -> str:
    """
    Add participants to an existing WhatsApp group.
    
    Args:
        group_name: The name of the group
        participants: Array of phone numbers with country code without + symbol (e.g., ["14155552671", "14155552672"])
    
    Returns:
        Confirmation message
    """
    payload = {"action": "add_to_group", "group_name": group_name, "participants": participants}
    print(f"TOOL EXECUTION: {payload}")
    return f"Added {participants} to group '{group_name}'"


@tool
def remove_from_group(group_name: str, participants: List[str]) -> str:
    """
    Remove participants from a WhatsApp group.
    
    Args:
        group_name: The name of the group
        participants: Array of phone numbers with country code without + symbol (e.g., ["14155552671", "14155552672"])
    
    Returns:
        Confirmation message
    """
    payload = {"action": "remove_from_group", "group_name": group_name, "participants": participants}
    print(f"TOOL EXECUTION: {payload}")
    return f"Removed {participants} from group '{group_name}'"

# Create separate DB query tools for private and public databases
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
        Translates natural language to AQL queries for your private database.
        
        Contains:
        1. WhatsApp contacts, messages, groups
        2. Dineout history and preferences
        3. Food preferences
        
        Use this first to get conversation context, find contacts or groups before using other tools.

        Use this tool multiple times if you get empty results.
        """

        result = chain.invoke(query)
        return json.dumps(result["aql_result"])
    
    return private_db_query
