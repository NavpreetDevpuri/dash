import os
import sys
from typing import List, Dict, Any, Optional
import datetime
from celery import Celery

# Add project root to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from app.db import get_system_db, get_user_db
from app.agents.whatsapp.schemas import Identifiers
from app.common.llm_manager import LLMManager
from app.common.base_consumer import BaseGraphConsumer

# Initialize Celery app
celery_app = Celery('whatsapp_consumer', broker=os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0'))

# Collection names for WhatsApp data
WORK_CONTACTS_COLLECTION = "work_contacts"
WHATSAPP_MESSAGES_COLLECTION = "whatsapp_messages"
IDENTIFIERS_COLLECTION = "identifiers"
WHATSAPP_CONTACT_MESSAGE_EDGE_COLLECTION = "whatsapp_contact_message"
WHATSAPP_IDENTIFIER_MESSAGE_EDGE_COLLECTION = "whatsapp_identifier_message"

class WhatsAppConsumer(BaseGraphConsumer):
    """
    A Celery consumer that processes WhatsApp messages, extracts identifiers,
    and stores them in the database.
    """
    def __init__(self, model_provider: str = "openai", model_name: str = "gpt-4o-mini", 
                temperature: float = 0):
        """
        Initialize the WhatsAppConsumer.
        
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
            message_content: The content of the WhatsApp message
            
        Returns:
            A list of identifiers
        """
        # Construct prompt for identifier extraction
        prompt = f"""
        Extract unique identifiers from this WhatsApp message. Identifiers could be:
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
    
    def _add_work_contact(self, db, phone_number: str, name: str) -> str:
        """
        Add a contact to the work_contacts collection if it doesn't already exist.
        
        Args:
            db: Database connection
            phone_number: Phone number of the contact
            name: Name of the contact
            
        Returns:
            The ID of the contact
        """
        # Check if collection exists, if not it will be created by the migration
        if not db.has_collection(WORK_CONTACTS_COLLECTION):
            return None
        
        # Check if contact already exists
        aql = f"""
        FOR contact IN {WORK_CONTACTS_COLLECTION}
        FILTER contact.phone_number == @phone_number
        RETURN contact._id
        """
        cursor = db.aql.execute(aql, bind_vars={"phone_number": phone_number})
        results = [doc for doc in cursor]
        
        if results:
            return results[0]
        
        # Add new contact
        doc = {
            "phone_number": phone_number,
            "name": name,
            "created_at": str(datetime.datetime.utcnow())
        }
        result = db.collection(WORK_CONTACTS_COLLECTION).insert(doc)
        return result["_id"]
    
    def _add_whatsapp_message(self, db, message_data: Dict[str, Any]) -> str:
        """
        Add a WhatsApp message to the database.
        
        Args:
            db: Database connection
            message_data: WhatsApp message data
            
        Returns:
            The ID of the inserted message
        """
        # Check if collection exists, if not it will be created by the migration
        if not db.has_collection(WHATSAPP_MESSAGES_COLLECTION):
            return None
        
        # Keep the original data structure but ensure required fields
        message_data_copy = message_data.copy()
        
        # Ensure created_at field
        if "created_at" not in message_data_copy:
            message_data_copy["created_at"] = str(datetime.datetime.utcnow())
        
        result = db.collection(WHATSAPP_MESSAGES_COLLECTION).insert(message_data_copy)
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
        Process a WhatsApp message, extract identifiers, and store in the database.
        
        Args:
            user_id: The ID of the user
            message_data: WhatsApp message data including content, phone_number, etc.
            
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
            # Add to work_contacts if phone_number is provided
            contact_id = None
            if "phone_number" in message_data and message_data["phone_number"]:
                contact_id = self._add_work_contact(db, message_data["phone_number"], message_data.get("name", "Unknown"))
            
            # Add whatsapp message
            message_id = self._add_whatsapp_message(db, message_data)
            
            # Link contact to message if both exist
            if contact_id and message_id:
                self._add_edge(db, contact_id, message_id, WHATSAPP_CONTACT_MESSAGE_EDGE_COLLECTION)
            
            # Process identifiers
            identifier_ids = []
            for identifier in identifiers:
                identifier_id = self._add_identifier(db, identifier)
                if identifier_id:
                    identifier_ids.append(identifier_id)
                    
                    # Add edge between identifier and message
                    if message_id:
                        self._add_edge(db, identifier_id, message_id, WHATSAPP_IDENTIFIER_MESSAGE_EDGE_COLLECTION)
            
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

# Celery task to process WhatsApp messages
@celery_app.task(name="whatsapp.process_message")
def process_whatsapp_message(user_id: str, message_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Celery task to process a WhatsApp message.
    
    Args:
        user_id: The ID of the user
        message_data: WhatsApp message data including content, phone_number, etc.
        
    Returns:
        A dictionary with the results of processing
    """
    consumer = WhatsAppConsumer()
    return consumer.process_message(user_id, message_data)


# Test code for WhatsAppConsumer
if __name__ == "__main__":
    # Sample user ID and message data for testing
    test_user_id = "1270834"
    test_message = {
        "content": "Hi, I'm working on the dashboard project for Acme Inc. Please contact john.doe@example.com for more details.",
        "group_id": "dashboard-team-group",
        "phone_number": "+14155552671",
        "name": "John Smith",
        "timestamp": str(datetime.datetime.utcnow())
    }
    
    result = process_whatsapp_message(test_user_id, test_message)
    print(result) 