from typing import Dict, List, Any, Optional
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_community.graphs import ArangoGraph
from langchain_community.chains.graph_qa.arangodb import ArangoGraphQAChain
from celery import Celery
import os
import datetime


# Initialize Celery app
celery_app = Celery('slack_tools', broker=os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0'))

def send_message_factory(arango_graph: ArangoGraph):
    """
    Factory function to create a send_message tool that includes user context.
    
    Args:
        arango_graph: ArangoDB graph connection
    """
    # Get user information from the 'me' collection once at tool creation time
    try:
        user_data = arango_graph.db.collection('me').get('me')
        slack_username = user_data.get('slack_username', 'unknown')
        slack_email = user_data.get('slack_email', 'unknown')
    except Exception as e:
        print(f"Error fetching user data: {str(e)}")
        slack_username = 'unknown'
        slack_email = 'unknown'
    
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
        # Create message payload with user info matching expected consumer format
        message_data = {
            "content": message,
            "channel": channel,
            "username": slack_username,
            "email": slack_email,
            "timestamp": str(datetime.datetime.utcnow()),
            # Include additional identifier to mark this as from the current user
            "is_from_me": True
        }
        
        # Send to Celery task for processing
        celery_app.send_task(
            "slack.process_message",
            kwargs={
                "user_id": "me",  # This will be replaced with actual user ID in production
                "message_data": message_data
            }
        )
        
        print(f"TOOL EXECUTION: {message_data}")
        return f"Message sent to {channel}: '{message}'"
    
    return send_message


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