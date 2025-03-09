import json
from typing import Dict, List, Any, Optional
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_community.graphs import ArangoGraph
from app.common.arangodb import ArangoGraphQAChain
from celery import Celery
import os
import datetime


# Initialize Celery app
celery_app = Celery('slack_processing', broker=os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0'))

def create_channel_factory(user_id: str):
    """Factory function to create a create_channel tool with user_id closure"""
    
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
        # Create channel payload
        payload = {
            "action": "create_channel", 
            "channel_name": channel_name, 
            "members": members,
            "timestamp": str(datetime.datetime.utcnow()),
            "is_from_me": True
        }
        
        # Send to Celery task for processing
        celery_app.send_task(
            "slack.process_channel_action",
            kwargs={
                "user_id": user_id,
                "channel_data": payload
            }
        )
        
        print(f"TOOL EXECUTION: {payload}")
        return f"Channel {channel_name} has been created with {len(members)} members."
    
    return create_channel


def leave_channel_factory(user_id: str):
    """Factory function to create a leave_channel tool with user_id closure"""
    
    @tool
    def leave_channel(channel_name: str) -> str:
        """
        Leave a Slack channel.
        
        Args:
            channel_name: The name of the channel to leave
        
        Returns:
            Confirmation message
        """
        # Create payload
        payload = {
            "action": "leave_channel", 
            "channel_name": channel_name,
            "timestamp": str(datetime.datetime.utcnow()),
            "is_from_me": True
        }
        
        # Send to Celery task for processing
        celery_app.send_task(
            "slack.process_channel_action",
            kwargs={
                "user_id": user_id,
                "channel_data": payload
            }
        )
        
        print(f"TOOL EXECUTION: {payload}")
        return f"You have left the channel {channel_name}."
    
    return leave_channel


def add_to_channel_factory(user_id: str):
    """Factory function to create an add_to_channel tool with user_id closure"""
    
    @tool
    def add_to_channel(channel_name: str, members: List[str]) -> str:
        """
        Add members to a Slack channel.
        
        Args:
            channel_name: The name of the channel
            members: Array of usernames or user emails to add to the channel
        
        Returns:
            Confirmation message
        """
        # Create payload
        payload = {
            "action": "add_to_channel", 
            "channel_name": channel_name, 
            "members": members,
            "timestamp": str(datetime.datetime.utcnow()),
            "is_from_me": True
        }
        
        # Send to Celery task for processing
        celery_app.send_task(
            "slack.process_channel_action",
            kwargs={
                "user_id": user_id,
                "channel_data": payload
            }
        )
        
        print(f"TOOL EXECUTION: {payload}")
        return f"Added {len(members)} members to channel {channel_name}."
    
    return add_to_channel


def remove_from_channel_factory(user_id: str):
    """Factory function to create a remove_from_channel tool with user_id closure"""
    
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
        # Create payload
        payload = {
            "action": "remove_from_channel", 
            "channel_name": channel_name, 
            "members": members,
            "timestamp": str(datetime.datetime.utcnow()),
            "is_from_me": True
        }
        
        # Send to Celery task for processing
        celery_app.send_task(
            "slack.process_channel_action",
            kwargs={
                "user_id": user_id,
                "channel_data": payload
            }
        )
        
        print(f"TOOL EXECUTION: {payload}")
        return f"Removed {len(members)} members from channel {channel_name}."
    
    return remove_from_channel


def set_channel_topic_factory(user_id: str):
    """Factory function to create a set_channel_topic tool with user_id closure"""
    
    @tool
    def set_channel_topic(channel_name: str, topic: str) -> str:
        """
        Set the topic for a Slack channel.
        
        Args:
            channel_name: The name of the channel
            topic: The new topic to set
        
        Returns:
            Confirmation message
        """
        # Create payload
        payload = {
            "action": "set_channel_topic", 
            "channel_name": channel_name, 
            "topic": topic,
            "timestamp": str(datetime.datetime.utcnow()),
            "is_from_me": True
        }
        
        # Send to Celery task for processing
        celery_app.send_task(
            "slack.process_channel_action",
            kwargs={
                "user_id": user_id,
                "channel_data": payload
            }
        )
        
        print(f"TOOL EXECUTION: {payload}")
        return f"Set topic for channel {channel_name} to: '{topic}'."
    
    return set_channel_topic


def send_message_factory(user_id: str, slack_username: str = None, slack_email: str = None):
    """Factory function to create a send_message tool with user_id and user details closure"""
    
    @tool
    def send_message(channel: str, message: str) -> str:
        """
        Send a message to a Slack channel or user.
        
        Args:
            channel: The channel name or user handle to send the message to
            message: The message content
            
        Returns:
            Confirmation message
        """
        # Create message payload with user info matching expected consumer format
        message_data = {
            "content": message,
            "channel": channel,
            "sender_username": slack_username,
            "sender_email": slack_email,
            "timestamp": str(datetime.datetime.utcnow()),
            # Include additional identifier to mark this as from the current user
            "is_from_me": True
        }
        
        # Send to Celery task for processing
        celery_app.send_task(
            "slack.process_message",
            kwargs={
                "user_id": user_id,
                "message_data": message_data
            }
        )
        
        print(f"TOOL EXECUTION: {message_data}")
        return f"Message sent to {channel}: '{message}'"
    
    return send_message


def set_status_with_time_factory(user_id: str):
    """Factory function to create a set_status_with_time tool with user_id closure"""
    
    @tool
    def set_status_with_time(status_text: str, status_emoji: str, end_time: str) -> str:
        """
        Set your Slack status with an expiration time.
        
        Args:
            status_text: The status text (e.g., "In a meeting")
            status_emoji: An emoji code (e.g., ":calendar:")
            end_time: When the status should expire (e.g., "2023-11-30T15:30:00")
            
        Returns:
            Confirmation message
        """
        # Create payload
        payload = {
            "action": "set_status", 
            "status_text": status_text, 
            "status_emoji": status_emoji,
            "end_time": end_time,
            "timestamp": str(datetime.datetime.utcnow()),
            "is_from_me": True
        }
        
        # Send to Celery task for processing
        celery_app.send_task(
            "slack.process_status_update",
            kwargs={
                "user_id": user_id,
                "status_data": payload
            }
        )
        
        print(f"TOOL EXECUTION: {payload}")
        return f"Status set to {status_emoji} {status_text} until {end_time}"
    
    return set_status_with_time


def set_status_factory(user_id: str):
    """Factory function to create a set_status tool with user_id closure"""
    
    @tool
    def set_status(status_text: str, status_emoji: str) -> str:
        """
        Set your Slack status (without an expiration time).
        
        Args:
            status_text: The status text (e.g., "Working remotely")
            status_emoji: An emoji code (e.g., ":house:")
            
        Returns:
            Confirmation message
        """
        # Create payload
        payload = {
            "action": "set_status", 
            "status_text": status_text, 
            "status_emoji": status_emoji,
            "end_time": None,
            "timestamp": str(datetime.datetime.utcnow()),
            "is_from_me": True
        }
        
        # Send to Celery task for processing
        celery_app.send_task(
            "slack.process_status_update",
            kwargs={
                "user_id": user_id,
                "status_data": payload
            }
        )
        
        print(f"TOOL EXECUTION: {payload}")
        return f"Status set to {status_emoji} {status_text}"
    
    return set_status


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
        Execute a natural language query against your private messaging graph database.
        This tool can answer questions about your Slack messages, channels, and users.
        Private database also have dineout history and food preferences.
        
        Use this first to get conversation context, find channels or users before using other tools.

        Use this tool multiple times if you get empty results.
        """

        result = chain.invoke(query)
        return result
    
    return private_db_query 