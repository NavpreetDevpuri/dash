import os
import sys
from typing import List, Dict, Any, Optional
import datetime
from celery import Celery

# Add project root to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from app.db import get_system_db, get_user_db
from app.agents.slack.schemas import Identifiers
from app.common.llm_manager import LLMManager
from app.common.base_consumer import BaseGraphConsumer

# Initialize Celery app
celery_app = Celery('slack_consumer', broker=os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0'))

# Collection names for Slack data
WORK_CONTACTS_COLLECTION = "work_contacts"
SLACK_MESSAGES_COLLECTION = "slack_messages"
IDENTIFIERS_COLLECTION = "identifiers"
SLACK_CONTACT_MESSAGE_EDGE_COLLECTION = "slack_contact_message"
SLACK_IDENTIFIER_MESSAGE_EDGE_COLLECTION = "slack_identifier_message"

class SlackConsumer(BaseGraphConsumer):
    """
    A Celery consumer that processes Slack messages, extracts identifiers,
    and stores them in the database.
    """
    def __init__(self, model_provider: str = "openai", model_name: str = "gpt-4o-mini", 
                temperature: float = 0):
        """
        Initialize the SlackConsumer.
        
        Args:
            model_provider: The LLM provider to use (openai, anthropic, gemini)
            model_name: The model name to use
            temperature: The temperature for the model
        """
        super().__init__()
        self.llm = LLMManager.get_model(
            provider=model_provider,
            model_name=model_name,
            temperature=temperature
        ).with_structured_output(Identifiers)
    
    def extract_identifiers(self, message_content: str) -> List[str]:
        """
        Use an LLM to extract identifiers from the message content.
        
        Args:
            message_content: The content of the Slack message
            
        Returns:
            A list of identifiers
        """
        # Construct prompt for identifier extraction
        prompt = f"""
        Extract unique identifiers from this Slack message. Identifiers could be:
        - Email addresses
        - Person names
        - Company names
        - Project names
        - Technical terms
        - Keywords that seem important in the context

        Return only the identifiers as a list.
        
        Message:
        {message_content}
        """
        
        # Call the model
        response = self.llm.invoke([{"role": "user", "content": prompt}])
        
        # Create and return an Identifiers object with lowercase identifiers
        return [identifier.lower() for identifier in response.identifiers]
    
    def _add_work_contact(self, db, email: str, slack_username: str) -> str:
        """
        Add a contact to the work_contacts collection if it doesn't already exist.
        
        Args:
            db: Database connection
            email: Email of the contact
            slack_username: Slack username of the contact
            
        Returns:
            The ID of the contact
        """
        # Check if collection exists, if not it will be created by the migration
        if not db.has_collection(WORK_CONTACTS_COLLECTION):
            return None
        
        # Check if contact already exists
        aql = f"""
        FOR contact IN {WORK_CONTACTS_COLLECTION}
        FILTER contact.email == @email
        RETURN contact._id
        """
        cursor = db.aql.execute(aql, bind_vars={"email": email})
        results = [doc for doc in cursor]
        
        if results:
            return results[0]
        
        # Add new contact
        doc = {
            "email": email,
            "slack_username": slack_username,
            "created_at": str(datetime.datetime.utcnow())
        }
        result = db.collection(WORK_CONTACTS_COLLECTION).insert(doc)
        return result["_id"]
    
    def _add_slack_message(self, db, message_data: Dict[str, Any]) -> str:
        """
        Add a Slack message to the database.
        
        Args:
            db: Database connection
            message_data: Slack message data
            
        Returns:
            The ID of the inserted message
        """
        # Check if collection exists, if not it will be created by the migration
        if not db.has_collection(SLACK_MESSAGES_COLLECTION):
            return None
        
        # Keep the original data structure but ensure required fields
        message_data_copy = message_data.copy()
        
        # Ensure created_at field
        if "created_at" not in message_data_copy:
            message_data_copy["created_at"] = str(datetime.datetime.utcnow())
        
        result = db.collection(SLACK_MESSAGES_COLLECTION).insert(message_data_copy)
        return result["_id"]
    
    def _add_identifier(self, db, identifier: str) -> str:
        """
        Add an identifier to the database.
        
        Args:
            db: Database connection
            identifier: The identifier string
            
        Returns:
            The ID of the inserted identifier
        """
        # Check if collection exists, if not it will be created by the migration
        if not db.has_collection(IDENTIFIERS_COLLECTION):
            return None
        
        # Check if identifier already exists
        aql = f"""
        FOR ident IN {IDENTIFIERS_COLLECTION}
        FILTER ident.value == @value
        RETURN ident._id
        """
        cursor = db.aql.execute(aql, bind_vars={"value": identifier})
        results = [doc for doc in cursor]
        
        if results:
            return results[0]
        
        # Add new identifier
        doc = {
            "value": identifier,
            "created_at": str(datetime.datetime.utcnow())
        }
        result = db.collection(IDENTIFIERS_COLLECTION).insert(doc)
        return result["_id"]
    
    def _add_edge(self, db, from_id: str, to_id: str, collection_name: str, data: Dict[str, Any] = None) -> str:
        """
        Add an edge between two vertices.
        
        Args:
            db: Database connection
            from_id: The ID of the source vertex
            to_id: The ID of the target vertex
            collection_name: The name of the edge collection
            data: Additional edge data
            
        Returns:
            The ID of the inserted edge
        """
        # Check if collection exists, if not it will be created by the migration
        if not db.has_collection(collection_name):
            return None
        
        # Prepare edge document
        edge_doc = {
            "_from": from_id,
            "_to": to_id,
            "created_at": str(datetime.datetime.utcnow())
        }
        
        # Add optional data if provided
        if data:
            edge_doc.update(data)
        
        # Insert edge
        result = db.collection(collection_name).insert(edge_doc)
        return result["_id"]

    def process_message(self, user_id: str, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a Slack message, extract identifiers, and store in the database.
        
        Args:
            user_id: The ID of the user
            message_data: Slack message data including content, channel, etc.
            
        Returns:
            A dictionary with the results of processing
        """
        # Extract identifiers from message
        identifiers = self.extract_identifiers(message_data.get("content", ""))
        
        # Get database connection for the user
        db = get_user_db(user_id)
        if not db:
            return {"error": "Failed to connect to database", "status": "failed"}
        
        try:
            # Add to work_contacts if email is provided
            contact_id = None
            if "email" in message_data and message_data["email"]:
                contact_id = self._add_work_contact(db, message_data["email"], message_data["username"])
            
            # Add slack message
            message_id = self._add_slack_message(db, message_data)
            
            # Link contact to message if both exist
            if contact_id and message_id:
                self._add_edge(db, contact_id, message_id, SLACK_CONTACT_MESSAGE_EDGE_COLLECTION)
            
            # Process identifiers
            identifier_ids = []
            for identifier in identifiers:
                identifier_id = self._add_identifier(db, identifier)
                if identifier_id:
                    identifier_ids.append(identifier_id)
                    
                    # Add edge between identifier and message
                    if message_id:
                        self._add_edge(db, identifier_id, message_id, SLACK_IDENTIFIER_MESSAGE_EDGE_COLLECTION)
            
            return {
                "status": "success",
                "message_id": message_id,
                "identifiers": identifiers,
                "identifier_ids": identifier_ids
            }
        
        except Exception as e:
            return {
                "error": str(e),
                "status": "failed"
            }

# Test code for SlackConsumer
if __name__ == "__main__":
    # Sample user ID and message data for testing
    test_user_id = "1270834"
    test_message = {
        "content": "Hi, I'm working on the dashboard project for Acme Inc. Please contact john.doe@example.com for more details.",
        "channel": "dashboard-team",
        "sender_username": "user123",  # Using username consistently instead of sender
        "sender_email": "sender@example.com",
        "timestamp": str(datetime.datetime.utcnow())
    }
    
    result = SlackConsumer().process_message(test_user_id, test_message)
    print(result)
