import json
from typing import Dict, List, Any, Optional
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_community.graphs import ArangoGraph
from app.common.arangodb import ArangoGraphQAChain
from celery import Celery
import os
import datetime
import sys

# Add project root to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from app.db import get_system_db, get_user_db

# Initialize Celery app
# celery_app = Celery('email_tools', broker=os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0'))

def send_email_factory(user_id: str):
    """Factory function to create a send_email tool with user_id closure"""
    
    @tool
    def send_email(to: List[str], subject: str, body: str, cc: Optional[List[str]] = None, bcc: Optional[List[str]] = None) -> str:
        """
        Send an email to the specified recipients.
        
        Args:
            to: List of recipient email addresses
            subject: Email subject line
            body: Email body content
            cc: Optional list of CC recipients
            bcc: Optional list of BCC recipients
            
        Returns:
            Confirmation message
        """
        # Prepare email data
        email_data = {
            "to": to,
            "subject": subject,
            "body": body,
            "cc": cc or [],
            "bcc": bcc or [],
            "date": datetime.datetime.utcnow().isoformat()
        }
        
        # # Send to Celery task for processing
        # result = celery_app.send_task(
        #     "email.send_email",
        #     kwargs={
        #         "user_id": user_id,
        #         "email_data": email_data
        #     }
        # )
        
        print(f"TOOL EXECUTION: {email_data}")
        return f"Email sent to {', '.join(to)} with subject '{subject}'."
    
    return send_email

def reply_to_email_factory(user_id: str):
    """Factory function to create a reply_to_email tool with user_id closure"""
    
    @tool
    def reply_to_email(email_id: str, body: str, include_all: bool = False) -> str:
        """
        Reply to an existing email.
        
        Args:
            email_id: ID of the email to reply to
            body: Content of the reply
            include_all: Whether to include all recipients in the reply (True) or just the sender (False)
            
        Returns:
            Confirmation message
        """
        # Prepare reply data
        reply_data = {
            "email_id": email_id,
            "body": body,
            "include_all": include_all,
            "response_type": "reply",
            "date": datetime.datetime.utcnow().isoformat()
        }
        
        # # Send to Celery task for processing
        # celery_app.send_task(
        #     "email.generate_email_response",
        #     kwargs={
        #         "user_id": user_id,
        #         "email_id": email_id,
        #         "response_type": "reply",
        #         "instructions": body
        #     }
        # )
        
        print(f"TOOL EXECUTION: {reply_data}")
        return f"Reply sent to email {email_id}."
    
    return reply_to_email

def forward_email_factory(user_id: str):
    """Factory function to create a forward_email tool with user_id closure"""
    
    @tool
    def forward_email(email_id: str, to: List[str], additional_comment: Optional[str] = None) -> str:
        """
        Forward an existing email to new recipients.
        
        Args:
            email_id: ID of the email to forward
            to: List of recipient email addresses
            additional_comment: Optional comment to add to the forwarded email
            
        Returns:
            Confirmation message
        """
        # Prepare forward data
        forward_data = {
            "email_id": email_id,
            "to": to,
            "additional_comment": additional_comment,
            "response_type": "forward",
            "date": datetime.datetime.utcnow().isoformat()
        }
        
        # # Send to Celery task for processing
        # celery_app.send_task(
        #     "email.generate_email_response",
        #     kwargs={
        #         "user_id": user_id,
        #         "email_id": email_id,
        #         "response_type": "forward",
        #         "instructions": additional_comment
        #     }
        # )
        
        print(f"TOOL EXECUTION: {forward_data}")
        return f"Email {email_id} forwarded to {', '.join(to)}."
    
    return forward_email

def create_folder_factory(user_id: str):
    """Factory function to create a create_folder tool with user_id closure"""
    
    @tool
    def create_folder(folder_name: str, folder_type: str = "CUSTOM") -> str:
        """
        Create a new email folder.
        
        Args:
            folder_name: Name of the folder to create
            folder_type: Type of folder (CUSTOM, INBOX, SENT, DRAFTS, etc.)
            
        Returns:
            Confirmation message
        """
        # Prepare folder data
        folder_data = {
            "name": folder_name,
            "type": folder_type,
            "action": "create"
        }
        
        # # Send to Celery task for processing
        # celery_app.send_task(
        #     "email.process_folder_action",
        #     kwargs={
        #         "user_id": user_id,
        #         "folder_data": folder_data
        #     }
        # )
        
        print(f"TOOL EXECUTION: {folder_data}")
        return f"Folder '{folder_name}' created successfully."
    
    return create_folder

def move_email_factory(user_id: str):
    """Factory function to create a move_email tool with user_id closure"""
    
    @tool
    def move_email(email_id: str, destination_folder: str) -> str:
        """
        Move an email to a different folder.
        
        Args:
            email_id: ID of the email to move
            destination_folder: Name of the destination folder
            
        Returns:
            Confirmation message
        """
        # Prepare move data
        move_data = {
            "email_id": email_id,
            "destination_folder": destination_folder,
            "action": "move"
        }
        
        # # Send to Celery task for processing
        # celery_app.send_task(
        #     "email.move_email",
        #     kwargs={
        #         "user_id": user_id,
        #         "email_id": email_id,
        #         "destination_folder": destination_folder
        #     }
        # )
        
        print(f"TOOL EXECUTION: {move_data}")
        return f"Email {email_id} moved to folder '{destination_folder}'."
    
    return move_email

# Database query tools
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
        Query your private Slack data using natural language.
        
        Args:
            query: Natural language query (e.g., "Find recent messages from John about the project deadline")
            
        Returns:
            Query results as text
        """
        result = chain.invoke(query)
        return result
    
    return private_db_query 