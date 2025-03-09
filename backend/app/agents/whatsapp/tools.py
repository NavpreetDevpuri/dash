import json
from typing import Dict, List, Any, Optional, Callable
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_community.graphs import ArangoGraph
from app.common.arangodb import ArangoGraphQAChain
import datetime
from celery import Celery
import os

# Initialize Celery app
celery_app = Celery('whatsapp_processing', broker=os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0'))

def save_contact_factory(user_id: str):
    """Factory function to create a save_contact tool with user_id closure"""
    
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
        # Create contact payload
        payload = {"action": "save_contact", "name": name, "phone_number": phone_number}
        
        # Send to Celery task for processing
        celery_app.send_task(
            "whatsapp.process_contact",
            kwargs={
                "user_id": user_id,
                "contact_data": payload
            }
        )
        
        print(f"TOOL EXECUTION: {payload}")
        return f"Contact {name} with number {phone_number} has been saved."
    
    return save_contact


def send_message_factory(user_id: str, whatsapp_number: str = None):
    """Factory function to create a send_message tool with user_id closure"""
    
    @tool
    def send_message(recipient: str, message: str) -> str:
        """
        Send a WhatsApp message to a contact or group.
        
        Args:
            recipient: The phone number with country code without + symbol (e.g., 14155552671) or group name 
            message: The message content to send
        
        Returns:
            Confirmation message
        """
        # Create message payload
        payload = {
            "action": "send_message", 
            "recipient": recipient, 
            "content": message,
            "timestamp": str(datetime.datetime.utcnow()),
            "phone_number": whatsapp_number,
            "is_from_me": True,
        }
        
        # Send to Celery task for processing
        celery_app.send_task(
            "whatsapp.process_message",
            kwargs={
                "user_id": user_id,
                "message_data": payload
            }
        )
        
        print(f"TOOL EXECUTION: {payload}")
        return f"Message sent to {recipient}: '{message}'"
    
    return send_message


def create_group_factory(user_id: str):
    """Factory function to create a create_group tool with user_id closure"""
    
    @tool
    def create_group(group_name: str, participants: List[str]) -> str:
        """
        Create a new WhatsApp group with the specified participants.
        
        Args:
            group_name: The name for the new group
            participants: Array of phone numbers to add to the group
        
        Returns:
            Confirmation message
        """
        # Create group payload
        payload = {
            "action": "create_group", 
            "group_name": group_name, 
            "participants": participants,
            "timestamp": str(datetime.datetime.utcnow()),
            "is_from_me": True
        }
        
        # Send to Celery task for processing
        celery_app.send_task(
            "whatsapp.process_group_action",
            kwargs={
                "user_id": user_id,
                "group_data": payload
            }
        )
        
        print(f"TOOL EXECUTION: {payload}")
        return f"Group {group_name} has been created with {len(participants)} participants."
    
    return create_group


def leave_group_factory(user_id: str):
    """Factory function to create a leave_group tool with user_id closure"""
    
    @tool
    def leave_group(group_name: str) -> str:
        """
        Leave a WhatsApp group.
        
        Args:
            group_name: The name of the group to leave
        
        Returns:
            Confirmation message
        """
        # Create payload
        payload = {
            "action": "leave_group", 
            "group_name": group_name,
            "timestamp": str(datetime.datetime.utcnow()),
            "is_from_me": True
        }
        
        # Send to Celery task for processing
        celery_app.send_task(
            "whatsapp.process_group_action",
            kwargs={
                "user_id": user_id,
                "group_data": payload
            }
        )
        
        print(f"TOOL EXECUTION: {payload}")
        return f"You have left the group {group_name}."
    
    return leave_group


def add_to_group_factory(user_id: str):
    """Factory function to create an add_to_group tool with user_id closure"""
    
    @tool
    def add_to_group(group_name: str, participants: List[str]) -> str:
        """
        Add participants to a WhatsApp group.
        
        Args:
            group_name: The name of the group
            participants: Array of phone numbers to add to the group
        
        Returns:
            Confirmation message
        """
        # Create payload
        payload = {
            "action": "add_to_group", 
            "group_name": group_name, 
            "participants": participants,
            "timestamp": str(datetime.datetime.utcnow()),
            "is_from_me": True
        }
        
        # Send to Celery task for processing
        celery_app.send_task(
            "whatsapp.process_group_action",
            kwargs={
                "user_id": user_id,
                "group_data": payload
            }
        )
        
        print(f"TOOL EXECUTION: {payload}")
        return f"Added {len(participants)} participants to group {group_name}."
    
    return add_to_group


def remove_from_group_factory(user_id: str):
    """Factory function to create a remove_from_group tool with user_id closure"""
    
    @tool
    def remove_from_group(group_name: str, participants: List[str]) -> str:
        """
        Remove participants from a WhatsApp group.
        
        Args:
            group_name: The name of the group
            participants: Array of phone numbers to remove from the group
        
        Returns:
            Confirmation message
        """
        # Create payload
        payload = {
            "action": "remove_from_group", 
            "group_name": group_name, 
            "participants": participants,
            "timestamp": str(datetime.datetime.utcnow()),
            "is_from_me": True
        }
        
        # Send to Celery task for processing
        celery_app.send_task(
            "whatsapp.process_group_action",
            kwargs={
                "user_id": user_id,
                "group_data": payload
            }
        )
        
        print(f"TOOL EXECUTION: {payload}")
        return f"Removed {len(participants)} participants from group {group_name}."
    
    return remove_from_group


def private_db_query_factory(model, arango_graph, aql_generation_prompt, user_id: str):
    """
    Factory function that creates a private database query tool using ArangoDB.
    
    Args:
        model: LLM model for query generation
        arango_graph: ArangoDB graph object
        aql_generation_prompt: Prompt for AQL generation
        user_id: User ID for the query
        
    Returns:
        A tool for querying the private database
    """
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
        This tool can answer questions about your messages, contacts, and conversation history.
        
        Args:
            query: Natural language query about your messaging data
            
        Returns:
            Results from the database in a readable format
        """
        
        # Execute the query
        result = chain.run(query)
        return result
    
    return private_db_query
