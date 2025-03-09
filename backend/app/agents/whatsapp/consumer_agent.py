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
celery_app = Celery(
    'whatsapp_consumer', 
    broker=os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
)

# Vertex collections
CONTACTS_COLLECTION = "contacts"
WHATSAPP_GROUPS_COLLECTION = "whatsapp_groups"
WHATSAPP_MESSAGES_COLLECTION = "whatsapp_messages"
IDENTIFIERS_COLLECTION = "identifiers"

# Edge collections (with updated names)
CONTACT_WHATSAPP_MESSAGE_EDGE_COLLECTION = "contact__whatsapp_message"
CONTACT_WHATSAPP_GROUP_EDGE_COLLECTION = "contact__whatsapp_group"
WHATSAPP_GROUP_MESSAGE_EDGE_COLLECTION = "whatsapp_group__message"
WHATSAPP_IDENTIFIER_MESSAGE_EDGE_COLLECTION = "whatsapp_identifier__message"

class WhatsAppConsumer(BaseGraphConsumer):
    """
    Processes WhatsApp messages by storing a simplified message document,
    creating vertices for contacts and groups, and linking identifier vertices.
    
    Expected incoming message_data structure:
      - payload: The text content of the message.
      - from: Sender's phone number (always a number; stored as whatsapp_number in contact).
      - to: For group messages, the group identifier; for direct messages, the recipient identifier.
      - is_group: Boolean flag indicating if the message comes from a group.
    """
    def __init__(self, model_provider: str = "openai", model_name: str = "gpt-4o-mini", temperature: float = 0):
        super().__init__()
        self.llm = LLMManager.get_model(
            provider=model_provider,
            model_name=model_name,
            temperature=temperature
        ).with_structured_output(Identifiers)
    
    def extract_identifiers(self, message_content: str) -> List[str]:
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
        response = self.llm.invoke([{"role": "user", "content": prompt}])
        return [identifier.lower() for identifier in response.identifiers]
    
    def _add_contact(self, db, whatsapp_number: str) -> Optional[str]:
        if not db.has_collection(CONTACTS_COLLECTION):
            return None
        
        aql = f'''
        FOR contact IN {CONTACTS_COLLECTION}
          FILTER contact.whatsapp_number == "{whatsapp_number}"
          RETURN contact._id
        '''
        cursor = db.aql.execute(aql)
        contact_ids = list(cursor)
        
        if contact_ids:
            return contact_ids[0]
        
        contact_doc = {
            "whatsapp_number": whatsapp_number,
            "created_at": datetime.datetime.now().isoformat(),
            "active": True
        }
        result = db.collection(CONTACTS_COLLECTION).insert(contact_doc)
        return result["_id"]
    
    def _add_whatsapp_group(self, db, group_identifier: str) -> Optional[str]:
        if not db.has_collection(WHATSAPP_GROUPS_COLLECTION):
            return None
        
        aql = f'''
        FOR group IN {WHATSAPP_GROUPS_COLLECTION}
          FILTER group.identifier == "{group_identifier}"
          RETURN group._id
        '''
        cursor = db.aql.execute(aql)
        group_ids = list(cursor)
        
        if group_ids:
            return group_ids[0]
        
        group_doc = {
            "identifier": group_identifier,
            "created_at": datetime.datetime.now().isoformat(),
            "active": True
        }
        result = db.collection(WHATSAPP_GROUPS_COLLECTION).insert(group_doc)
        return result["_id"]
    
    def _add_whatsapp_message(self, db, message_data: Dict[str, Any]) -> Optional[str]:
        if not db.has_collection(WHATSAPP_MESSAGES_COLLECTION):
            return None
        
        message_doc = {
            "text": message_data.get("text", ""),
            "from": message_data.get("from"),
            "to": message_data.get("to"),
            "created_at": datetime.datetime.now().isoformat()
        }
        result = db.collection(WHATSAPP_MESSAGES_COLLECTION).insert(message_doc)
        return result["_id"]
        
    def _add_identifier(self, db, identifier: str) -> Optional[str]:
        if not db.has_collection(IDENTIFIERS_COLLECTION):
            return None
        
        aql = f'''
        FOR ident IN {IDENTIFIERS_COLLECTION}
          FILTER ident.value == "{identifier}"
          RETURN ident._id
        '''
        cursor = db.aql.execute(aql)
        identifier_ids = list(cursor)
        
        if identifier_ids:
            return identifier_ids[0]
        
        identifier_doc = {
            "value": identifier,
            "created_at": datetime.datetime.now().isoformat()
        }
        result = db.collection(IDENTIFIERS_COLLECTION).insert(identifier_doc)
        return result["_id"]
    
    def _add_edge(self, db, from_id: str, to_id: str, collection_name: str, data: Dict[str, Any] = None) -> Optional[str]:
        if not db.has_collection(collection_name):
            return None

        aql = f'''
        FOR edge IN {collection_name}
          FILTER edge._from == "{from_id}" AND edge._to == "{to_id}"
          RETURN edge._id
        '''
        cursor = db.aql.execute(aql)
        edge_ids = list(cursor)

        if edge_ids:
            return edge_ids[0]

        edge_doc = {
            "_from": from_id,
            "_to": to_id,
            "created_at": datetime.datetime.now().isoformat()
        }
        if data:
            edge_doc.update(data)

        result = db.collection(collection_name).insert(edge_doc)
        return result["_id"]
    
    def process_message(self, user_id: str, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a WhatsApp message by:
          - Storing a simplified message document.
          - Creating a contact vertex (from sender's phone number).
          - For group messages, creating a group vertex (from the 'to' field).
          - Creating edges linking:
              • For direct messages: contact → message.
              • For group messages: group → message and contact → group.
          - Extracting identifiers from the text and linking them to the message.
        """
        try:
            db = get_user_db(user_id)
            if not db:
                return {"status": "error", "message": "Failed to connect to database"}
            
            text = message_data.get("text", "")
            sender = message_data.get("from")
            to_identifier = message_data.get("to")
            is_group = message_data.get("is_group", False)
            
            if not text or not text.strip():
                return {"status": "error", "message": "Message payload is empty"}
            if not sender or not to_identifier:
                return {"status": "error", "message": "Missing 'from' or 'to' in message data"}
            
            # Always create a contact vertex for the sender.
            sender_id = self._add_contact(db, whatsapp_number=sender)
            
            # For group messages, create a group vertex using the 'to' field.
            group_id = None
            if is_group:
                group_id = self._add_whatsapp_group(db, group_identifier=to_identifier)
            
            # Insert the simplified WhatsApp message document.
            message_id = self._add_whatsapp_message(db, message_data)
            if not message_id:
                return {"status": "error", "message": "Failed to add message to database"}
            
            # Create edges based on message type.
            if is_group and group_id:
                # Link group to message.
                self._add_edge(db, group_id, message_id, WHATSAPP_GROUP_MESSAGE_EDGE_COLLECTION)
                # Link sender (contact) to group.
                self._add_edge(db, sender_id, group_id, CONTACT_WHATSAPP_GROUP_EDGE_COLLECTION)
            else:
                # For direct messages, link contact to message.
                self._add_edge(db, sender_id, message_id, CONTACT_WHATSAPP_MESSAGE_EDGE_COLLECTION)
            
            # Extract identifiers from the payload and create vertices/edges.
            identifiers = self.extract_identifiers(text)
            identifier_ids = []
            for identifier in identifiers:
                identifier_id = self._add_identifier(db, identifier)
                if identifier_id:
                    identifier_ids.append(identifier_id)
                    self._add_edge(
                        db,
                        identifier_id,
                        message_id,
                        WHATSAPP_IDENTIFIER_MESSAGE_EDGE_COLLECTION
                    )
            
            return {
                "status": "success",
                "message": "Message processed successfully",
                "message_id": message_id,
                "group_id": group_id,
                "contact_id": sender_id,
                "identifiers": identifiers,
                "identifier_ids": identifier_ids
            }
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Error processing message: {str(e)}")
            return {
                "status": "error",
                "message": f"Error processing message: {str(e)}",
                "error": str(e)
            }

# Celery task to process WhatsApp messages
@celery_app.task(name="whatsapp.process_message")
def process_whatsapp_message(user_id: str, message_data: Dict[str, Any]) -> Dict[str, Any]:
    consumer = WhatsAppConsumer()
    return consumer.process_message(user_id, message_data)

# Test code for WhatsAppConsumer
if __name__ == "__main__":
    test_user_id = "1270834"
    test_message = {
        "text": "Hi, I'm working on the dashboard project for Acme Inc. Please contact john.doe@example.com for more details.",
        "from": "14155552671",  # Phone number as a string
        "to": "dashboard-team-group",  # For group messages, this is the group id
        "is_group": True
    }
    
    result = process_whatsapp_message(test_user_id, test_message)
    print(result)