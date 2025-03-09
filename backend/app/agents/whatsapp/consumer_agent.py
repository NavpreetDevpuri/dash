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

# Vertex collections
CONTACTS_COLLECTION = "contacts"
WHATSAPP_GROUPS_COLLECTION = "whatsapp_groups"  # formerly whatsapp_conversations
WHATSAPP_MESSAGES_COLLECTION = "whatsapp_messages"
IDENTIFIERS_COLLECTION = "identifiers"

# Edge collections (all include the 'whatsapp' keyword)
CONTACT_WHATSAPP_MESSAGE_EDGE_COLLECTION = "contact_whatsapp_message"  # For direct messages
WHATSAPP_GROUP_MESSAGE_EDGE_COLLECTION = "whatsapp_group_message"      # For group messages
WHATSAPP_IDENTIFIER_MESSAGE_EDGE_COLLECTION = "whatsapp_identifier_message"

class WhatsAppConsumer(BaseGraphConsumer):
    """
    A Celery consumer that processes WhatsApp messages, extracts identifiers,
    and stores them in the database.

    Vertex Collections:
      • contacts: stores contact details.
      • whatsapp_groups: stores conversations/groups.
      • whatsapp_messages: stores messages.
      • identifiers: stores extracted identifiers.
      
    Edge Collections:
      • contact_whatsapp_message: links a contact to a message (for direct messages).
      • whatsapp_group_message: links a group to a message (for group messages).
      • whatsapp_identifier_message: links an identifier to a message.
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
    
    def _add_contact(self, db, username: str, display_name: str = None, phone_number: str = None) -> str:
        if not db.has_collection(CONTACTS_COLLECTION):
            return None
        
        aql = f"""
        FOR contact IN {CONTACTS_COLLECTION}
          FILTER contact.whatsapp_number == "{phone_number}"
          RETURN contact._id
        """
        cursor = db.aql.execute(aql)
        contact_ids = list(cursor)
        
        if contact_ids:
            return contact_ids[0]
        
        contact_doc = {
            "display_name": display_name or username,
            "whatsapp_number": phone_number,
            "created_at": datetime.datetime.now().isoformat(),
            "active": True
        }
        result = db.collection(CONTACTS_COLLECTION).insert(contact_doc)
        return result["_id"]
    
    def _add_whatsapp_group(self, db, username: str, is_group: bool = False, name: str = None) -> str:
        if not db.has_collection(WHATSAPP_GROUPS_COLLECTION):
            return None
        
        aql = f"""
        FOR group IN {WHATSAPP_GROUPS_COLLECTION}
          FILTER group.username == "{username}"
          RETURN group._id
        """
        cursor = db.aql.execute(aql)
        group_ids = list(cursor)
        
        if group_ids:
            return group_ids[0]
        
        group_doc = {
            "username": username,
            "display_name": name or username,
            "is_group": is_group,
            "created_at": datetime.datetime.now().isoformat(),
            "active": True
        }
        result = db.collection(WHATSAPP_GROUPS_COLLECTION).insert(group_doc)
        return result["_id"]
    
    def _add_whatsapp_message(self, db, message_data: Dict[str, Any], group_id: str) -> str:
        if not db.has_collection(WHATSAPP_MESSAGES_COLLECTION):
            return None
        
        message_doc = {
            "content": message_data.get("content", ""),
            "sender": message_data.get("sender", "unknown"),
            "timestamp": message_data.get("timestamp", datetime.datetime.now().isoformat()),
            "raw_data": message_data,
            "created_at": datetime.datetime.now().isoformat()
        }
        result = db.collection(WHATSAPP_MESSAGES_COLLECTION).insert(message_doc)
        return result["_id"]
        
    def _add_identifier(self, db, identifier: str) -> str:
        if not db.has_collection(IDENTIFIERS_COLLECTION):
            return None
        
        aql = f"""
        FOR ident IN {IDENTIFIERS_COLLECTION}
          FILTER ident.value == "{identifier}"
          RETURN ident._id
        """
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
    
    def _add_edge(self, db, from_id: str, to_id: str, collection_name: str, data: Dict[str, Any] = None) -> str:
        if not db.has_collection(collection_name):
            return None

        aql = f"""
        FOR edge IN {collection_name}
        FILTER edge._from == "{from_id}" AND edge._to == "{to_id}"
        RETURN edge._id
        """
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
        Process a WhatsApp message by extracting identifiers and storing it in the database.

        Expects:
          - "content": The message text.
          - "group_id" (or "conversation_id"): The identifier for the WhatsApp group/conversation.
          - "sender": The sender's username.
          - Optionally, "sender_phone" and "sender_name".
        """
        try:
            db = get_user_db(user_id)
            if not db:
                return {"status": "error", "message": "Failed to connect to database"}
            
            content = message_data.get("content", "")
            if not content or not content.strip():
                return {"status": "error", "message": "Message content is empty"}
            
            # Use group_id (or fallback to conversation_id) as the group identifier.
            group_identifier = message_data.get("group_id") or message_data.get("conversation_id")
            if not group_identifier:
                return {"status": "error", "message": "No group identifier found in message data"}
                
            # Add or retrieve the sender contact.
            sender_username = message_data.get("sender")
            sender_id = None
            sender_phone = message_data.get("sender_phone")
            if sender_username:
                sender_id = self._add_contact(
                    db, 
                    username=sender_username,
                    display_name=message_data.get("sender_name", sender_username),
                    phone_number=sender_phone
                )
            
            # Determine if this is a group message based on the presence of "group_id".
            is_group = bool(message_data.get("group_id"))
            group_id = self._add_whatsapp_group(
                db, 
                username=group_identifier,
                is_group=is_group,
                name=message_data.get("group_name", group_identifier) if is_group else message_data.get("contact_name", group_identifier)
            )
            if not group_id:
                return {"status": "error", "message": "Failed to add group to database"}
                
            # Insert the WhatsApp message.
            message_id = self._add_whatsapp_message(db, message_data, group_id)
            if not message_id:
                return {"status": "error", "message": "Failed to add message to database"}
            
            # Create an edge linking the message:
            if is_group:
                # For group messages, link the group to the message.
                self._add_edge(
                    db, 
                    group_id, 
                    message_id,
                    WHATSAPP_GROUP_MESSAGE_EDGE_COLLECTION
                )
            else:
                # For direct (non-group) messages, link the sender contact directly to the message.
                if sender_id:
                    self._add_edge(
                        db,
                        f"{CONTACTS_COLLECTION}/{sender_id}",
                        f"{WHATSAPP_MESSAGES_COLLECTION}/{message_id}",
                        CONTACT_WHATSAPP_MESSAGE_EDGE_COLLECTION
                    )
            
            # Extract identifiers from the message content.
            identifiers = self.extract_identifiers(content)
            
            # Add identifiers to the database and create edges linking each identifier to the message.
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
        "content": "Hi, I'm working on the dashboard project for Acme Inc. Please contact john.doe@example.com for more details.",
        "group_id": "dashboard-team-group",
        "sender": "john_doe",
        "sender_name": "John Doe",
        "sender_phone": "+14155552671",
        "timestamp": datetime.datetime.utcnow().isoformat()
    }
    
    result = process_whatsapp_message(test_user_id, test_message)
    print(result)