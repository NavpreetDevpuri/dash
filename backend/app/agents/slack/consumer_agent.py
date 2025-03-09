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

# Define edge definitions for Slack graph
SLACK_EDGE_DEFINITIONS = [
    {
        "edge_collection": "contact_message",
        "from_vertex_collections": ["work_contacts"],
        "to_vertex_collections": ["slack_messages"],
    },
    {
        "edge_collection": "identifier_message",
        "from_vertex_collections": ["identifiers"],
        "to_vertex_collections": ["slack_messages"],
    },
]

# Define orphan collections
SLACK_ORPHAN_COLLECTIONS = ["work_contacts", "slack_messages", "identifiers"]

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
    
    def _add_work_contact(self, email: str, slack_username: str) -> str:
        """
        Add a contact to the work_contacts collection if it doesn't already exist.
        
        Args:
            email: Email of the contact
            
        Returns:
            The ID of the contact
        """
        return self.add_node(
            collection_name="work_contacts",
            data={"email": email, "slack_username": slack_username},
            unique_key="email",
            unique_value=email, 
        )
    
    def _add_slack_message(self, message_data: Dict[str, Any]) -> str:
        """
        Add a Slack message to the database.
        
        Args:
            message_data: Slack message data
            
        Returns:
            The ID of the inserted message
        """
        # Keep the original data structure but ensure required fields
        message_data_copy = message_data.copy()
        
        # Ensure created_at field
        if "created_at" not in message_data_copy:
            message_data_copy["created_at"] = str(datetime.datetime.utcnow())
            
        return self.add_node(
            collection_name="slack_messages",
            data=message_data_copy
        )
    
    def _add_identifier(self, identifier: str) -> str:
        """
        Add an identifier to the database.
        
        Args:
            identifier: The identifier string
            
        Returns:
            The ID of the inserted identifier
        """
        return self.add_node(
            collection_name="identifiers",
            data={"value": identifier},
            unique_key="value",
            unique_value=identifier
        )

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
        
        # Get database connection for the user and set up graph
        db = get_user_db(user_id)
        if not db:
            return {"error": "Failed to connect to database", "status": "failed"}
        
        # Set up graph using the provided database connection
        self.setup_graph(db, "slack_data", SLACK_EDGE_DEFINITIONS, SLACK_ORPHAN_COLLECTIONS)
        
        try:
            # Add to work_contacts if email is provided
            contact_id = None
            if "email" in message_data and message_data["email"]:
                contact_id = self._add_work_contact(message_data["email"], message_data["username"])
            
            # Add slack message
            message_id = self._add_slack_message(message_data)
            
            # Link contact to message if both exist
            if contact_id and message_id:
                self.add_edge("contact_message", contact_id, message_id)
            
            # Process identifiers
            identifier_ids = []
            for identifier in identifiers:
                identifier_id = self._add_identifier(identifier)
                identifier_ids.append(identifier_id)
                
                # Add edge between identifier and message
                self.add_edge("identifier_message", identifier_id, message_id)
            
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

# Celery task to process Slack messages
@celery_app.task(name="slack.process_message")
def process_slack_message(user_id: str, message_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Celery task to process a Slack message.
    
    Args:
        user_id: The ID of the user
        message_data: Slack message data including content, channel, etc.
        
    Returns:
        A dictionary with the results of processing
    """
    consumer = SlackConsumer()
    return consumer.process_message(user_id, message_data)


# Test code for SlackConsumer
if __name__ == "__main__":
    # Sample user ID and message data for testing
    test_user_id = "1270834"
    test_message = {
        "content": "Hi, I'm working on the dashboard project for Acme Inc. Please contact john.doe@example.com for more details.",
        "channel": "dashboard-team",
        "username": "user123",  # Using username consistently instead of sender
        "email": "sender@example.com",
        "timestamp": str(datetime.datetime.utcnow())
    }
    
    result = process_slack_message(test_user_id, test_message)
    print(result)
