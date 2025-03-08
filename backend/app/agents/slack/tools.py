from typing import Dict, List, Any, Optional
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_community.graphs import ArangoGraph
from langchain_community.chains.graph_qa.arangodb import ArangoGraphQAChain


@tool
def send_message(channel: str, message: str) -> str:
    """
    Send a Slack message to a channel or user.
    
    Args:
        channel: The channel name or user email to send the message to
        message: The message content to send
    
    Returns:
        Confirmation message
    """
    # For now, just print the payload
    payload = {"action": "send_message", "channel": channel, "message": message}
    print(f"TOOL EXECUTION: {payload}")
    return f"Message sent to {channel}: '{message}'"


@tool
def create_channel(channel_name: str, members: List[str]) -> str:
    """
    Create a new Slack channel with the specified members.
    
    Args:
        channel_name: The name for the new channel
        members: Array of usernames or user emails to add to the channel
    
    Returns:
        Confirmation message
    """
    payload = {"action": "create_channel", "channel_name": channel_name, "members": members}
    print(f"TOOL EXECUTION: {payload}")
    return f"Channel '{channel_name}' created with members: {members}"


@tool
def leave_channel(channel_name: str) -> str:
    """
    Leave a Slack channel.
    
    Args:
        channel_name: The name of the channel to leave
    
    Returns:
        Confirmation message
    """
    payload = {"action": "leave_channel", "channel_name": channel_name}
    print(f"TOOL EXECUTION: {payload}")
    return f"You have left the channel '{channel_name}'"


@tool
def add_to_channel(channel_name: str, members: List[str]) -> str:
    """
    Add members to an existing Slack channel.
    
    Args:
        channel_name: The name of the channel
        members: Array of usernames or user emails to add to the channel
    
    Returns:
        Confirmation message
    """
    payload = {"action": "add_to_channel", "channel_name": channel_name, "members": members}
    print(f"TOOL EXECUTION: {payload}")
    return f"Added {members} to channel '{channel_name}'"


@tool
def remove_from_channel(channel_name: str, members: List[str]) -> str:
    """
    Remove members from a Slack channel.
    
    Args:
        channel_name: The name of the channel
        members: Array of usernames or user emails to remove from the channel
    
    Returns:
        Confirmation message
    """
    payload = {"action": "remove_from_channel", "channel_name": channel_name, "members": members}
    print(f"TOOL EXECUTION: {payload}")
    return f"Removed {members} from channel '{channel_name}'"


@tool
def set_channel_topic(channel_name: str, topic: str) -> str:
    """
    Set the topic for a Slack channel.
    
    Args:
        channel_name: The name of the channel
        topic: The new topic to set for the channel
    
    Returns:
        Confirmation message
    """
    payload = {"action": "set_channel_topic", "channel_name": channel_name, "topic": topic}
    print(f"TOOL EXECUTION: {payload}")
    return f"Topic for channel '{channel_name}' set to: '{topic}'"


@tool
def create_thread(channel: str, message: str, parent_message_ts: str) -> str:
    """
    Create a thread reply to a message in a Slack channel.
    
    Args:
        channel: The channel name or user email containing the parent message
        message: The content of the thread reply
        parent_message_ts: The timestamp of the parent message to reply to
    
    Returns:
        Confirmation message
    """
    payload = {
        "action": "create_thread", 
        "channel": channel, 
        "message": message, 
        "parent_message_ts": parent_message_ts
    }
    print(f"TOOL EXECUTION: {payload}")
    return f"Thread reply sent in {channel}: '{message}'"


@tool
def set_status_with_time(status_text: str, status_emoji: str, end_time: str) -> str:
    """
    Set your Slack status with an automatic expiration time.
    
    Args:
        status_text: The status text to display (e.g., "In a meeting")
        status_emoji: The emoji to show with the status (e.g., ":calendar:", ":coffee:")
        end_time: When the status should expire (in format "YYYY-MM-DD HH:MM" or "in X hours/minutes")
    
    Returns:
        Confirmation message
    """
    payload = {
        "action": "set_status", 
        "status_text": status_text, 
        "status_emoji": status_emoji,
        "end_time": end_time
    }
    print(f"TOOL EXECUTION: {payload}")
    return f"Status set to '{status_emoji} {status_text}' until {end_time}"


@tool
def set_status(status_text: str, status_emoji: str) -> str:
    """
    Set your Slack status without an expiration time (no clear).
    
    Args:
        status_text: The status text to display (e.g., "Working remotely")
        status_emoji: The emoji to show with the status (e.g., ":house:", ":computer:")
    
    Returns:
        Confirmation message
    """
    payload = {
        "action": "set_status", 
        "status_text": status_text, 
        "status_emoji": status_emoji,
        "end_time": "no clear"
    }
    print(f"TOOL EXECUTION: {payload}")
    return f"Status set to '{status_emoji} {status_text}' with no expiration"


# Create separate DB query tools for private and public databases
def private_db_query_factory(model, arango_graph, aql_generation_prompt):
    chain = ArangoGraphQAChain.from_llm(
        llm=model,
        graph=arango_graph,
        verbose=True,
        allow_dangerous_requests=True, 
        aql_generation_prompt=aql_generation_prompt
    )

    @tool
    def private_db_query(query: str) -> str:
        """
        Translates natural language to AQL queries for your private database.
        
        Contains:
        1. Slack channels, messages, and users
        2. Dineout history and preferences
        3. Food preferences
        
        Use this first to get conversation context, find channels or users before using other tools.

        Use this tool multiple times if you get empty results.
        """

        result = chain.invoke(query)
        return str(result["result"])
    
    return private_db_query 