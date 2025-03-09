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
from arango.database import StandardDatabase

# Initialize Celery app
celery_app = Celery('slack_consumer', broker=os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0'))

# Collection names for our simplified graph
CONTACTS_COLLECTION = "contacts"
CHANNELS_COLLECTION = "slack_channels"
MESSAGES_COLLECTION = "slack_messages"
CONTACT_CHANNEL_EDGE_COLLECTION = "contact_channel"
IDENTIFIERS_COLLECTION = "identifiers"
IDENTIFIER_MESSAGE_EDGE_COLLECTION = "identifier_message"

class SlackConsumer:
    """
    A Celery consumer that processes Slack messages into a simple graph:
    
      • Contacts (identified by slack_username)
      • Channels (a Slack channel)
      • Messages (sent by a contact in a channel)
      • Identifiers extracted from the message text
      
    A contact is linked to a channel via an edge (membership) and each identifier is linked
    to the message from which it was extracted.
    """
    def __init__(self, model_provider: str = "openai", model_name: str = "gpt-4o-mini", temperature: float = 0):
        # Initialize the LLM with structured output to extract identifiers.
        self.llm = LLMManager.get_model(
            provider=model_provider,
            model_name=model_name,
            temperature=temperature
        ).with_structured_output(Identifiers)
    
    def extract_identifiers(self, message_content: str) -> List[str]:
        """
        Use an LLM to extract identifiers from the message content.
        
        Returns:
            A list of identifiers.
        """
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
        response = self.llm.invoke([{"role": "user", "content": prompt}])
        return [identifier.lower() for identifier in response.identifiers]

    def _add_contact(self, db: StandardDatabase, slack_username: str) -> Optional[str]:
        """
        Add or retrieve a contact by slack_username.
        """
        if not db.has_collection(CONTACTS_COLLECTION):
            return None

        aql = f"""
        FOR contact IN {CONTACTS_COLLECTION}
          FILTER contact.slack_username == @slack_username
          RETURN contact._id
        """
        cursor = db.aql.execute(aql, bind_vars={"slack_username": slack_username})
        try:
            contact_id = cursor.next()
        except StopIteration:
            contact_id = None

        if contact_id:
            return contact_id

        contact_doc = {
            "slack_username": slack_username,
            "created_at": datetime.datetime.now().isoformat(),
            "active": True
        }
        result = db.collection(CONTACTS_COLLECTION).insert(contact_doc)
        return result["_id"]

    def _add_channel(self, db: StandardDatabase, channel_name: str) -> Optional[str]:
        """
        Add or retrieve a Slack channel.
        """
        if not db.has_collection(CHANNELS_COLLECTION):
            return None

        aql = f"""
        FOR channel IN {CHANNELS_COLLECTION}
          FILTER channel.name == @channel_name
          RETURN channel._id
        """
        cursor = db.aql.execute(aql, bind_vars={"channel_name": channel_name})
        try:
            channel_id = cursor.next()
        except StopIteration:
            channel_id = None

        if channel_id:
            return channel_id

        channel_doc = {
            "name": channel_name,
            "created_at": datetime.datetime.now().isoformat(),
            "active": True
        }
        result = db.collection(CHANNELS_COLLECTION).insert(channel_doc)
        return result["_id"]

    def _add_message(self, db: StandardDatabase, message_data: Dict[str, Any],
                     contact_id: str, channel_id: str) -> Optional[str]:
        """
        Add a message document that links a contact (sender) to a channel.
        """
        if not db.has_collection(MESSAGES_COLLECTION):
            return None

        message_doc = {
            "content": message_data.get("text", ""),
            "sender_id": contact_id,
            "channel_id": channel_id,
            "timestamp": message_data.get("timestamp", datetime.datetime.now().isoformat()),
            "raw_data": message_data,
            "created_at": datetime.datetime.now().isoformat()
        }
        result = db.collection(MESSAGES_COLLECTION).insert(message_doc)
        return result["_id"]

    def _add_identifier(self, db: StandardDatabase, identifier: str) -> Optional[str]:
        """
        Add or retrieve an identifier.
        """
        if not db.has_collection(IDENTIFIERS_COLLECTION):
            return None

        aql = f"""
        FOR ident IN {IDENTIFIERS_COLLECTION}
          FILTER ident.value == @value
          RETURN ident._id
        """
        cursor = db.aql.execute(aql, bind_vars={"value": identifier})
        try:
            identifier_id = cursor.next()
        except StopIteration:
            identifier_id = None

        if identifier_id:
            return identifier_id

        identifier_doc = {
            "value": identifier,
            "created_at": datetime.datetime.now().isoformat()
        }
        result = db.collection(IDENTIFIERS_COLLECTION).insert(identifier_doc)
        return result["_id"]

    def _add_edge(self, db: StandardDatabase, from_id: str, to_id: str, collection_name: str) -> Optional[str]:
        """
        Add an edge between two vertices if it does not already exist.
        """
        if not db.has_collection(collection_name):
            return None

        aql = f"""
        FOR edge IN {collection_name}
          FILTER edge._from == @from_id AND edge._to == @to_id
          RETURN edge._id
        """
        cursor = db.aql.execute(aql, bind_vars={"from_id": from_id, "to_id": to_id})
        try:
            edge_id = cursor.next()
        except StopIteration:
            edge_id = None

        if edge_id:
            return edge_id

        edge_doc = {
            "_from": from_id,
            "_to": to_id,
            "created_at": datetime.datetime.now().isoformat()
        }
        result = db.collection(collection_name).insert(edge_doc)
        return result["_id"]

    def _add_contact_channel_edge(self, db: StandardDatabase, contact_id: str, channel_id: str) -> Optional[str]:
        """
        Create an edge between a contact and a channel to indicate membership.
        Assumes contact_id and channel_id are fully-qualified (e.g., "contacts/12345").
        If not, the collection prefix will be added.
        """
        if "/" not in contact_id:
            contact_id = f"{CONTACTS_COLLECTION}/{contact_id}"
        if "/" not in channel_id:
            channel_id = f"{CHANNELS_COLLECTION}/{channel_id}"
        return self._add_edge(db, contact_id, channel_id, CONTACT_CHANNEL_EDGE_COLLECTION)

    def process_message(self, user_id: str, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an incoming Slack message:
          1. Retrieve (or add) the contact (sender) and channel.
          2. Create an edge from the contact to the channel.
          3. Insert the message.
          4. Extract identifiers from the message and store/link them.
        """
        try:
            db = get_user_db(user_id)
            if not db:
                return {"status": "error", "message": "Failed to connect to database"}

            content = message_data.get("text", "")
            if not content or not content.strip():
                return {"status": "error", "message": "Message content is empty"}

            slack_username = message_data.get("user")
            channel_name = message_data.get("channel")
            if not slack_username or not slack_username.strip():
                return {"status": "error", "message": "No valid sender found in message data"}
            if not channel_name or not channel_name.strip():
                return {"status": "error", "message": "No valid channel found in message data"}

            # Add or retrieve contact and channel.
            contact_id = self._add_contact(db, slack_username)
            channel_id = self._add_channel(db, channel_name)
            if not contact_id or not channel_id:
                return {"status": "error", "message": "Failed to add contact or channel"}

            # Create membership edge between contact and channel.
            self._add_contact_channel_edge(db, contact_id, channel_id)

            # Insert the Slack message.
            message_id = self._add_message(db, message_data, contact_id, channel_id)
            if not message_id:
                return {"status": "error", "message": "Failed to add message"}

            # Extract identifiers from the message content.
            identifiers = self.extract_identifiers(content)
            identifier_ids = []
            for identifier in identifiers:
                id_id = self._add_identifier(db, identifier)
                if id_id:
                    identifier_ids.append(id_id)
                    # Create an edge from the identifier to the message.
                    self._add_edge(db, id_id, message_id, IDENTIFIER_MESSAGE_EDGE_COLLECTION)

            return {
                "status": "success",
                "message": "Message processed successfully",
                "message_id": message_id,
                "contact_id": contact_id,
                "channel_id": channel_id,
                "identifiers": identifiers,
                "identifier_ids": identifier_ids
            }
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            print(f"Error processing Slack message: {str(e)}")
            print(f"Traceback: {error_traceback}")
            return {"status": "error", "message": f"Error processing message: {str(e)}"}

# Celery task for processing Slack messages
@celery_app.task(name="slack.process_message")
def process_slack_message(user_id: str, message_data: Dict[str, Any]) -> Dict[str, Any]:
    consumer = SlackConsumer()
    return consumer.process_message(user_id, message_data)

# Celery task for processing Slack channel actions (if needed)
@celery_app.task(name="slack.process_channel_action")
def process_slack_channel_action(user_id: str, channel_data: Dict[str, Any]) -> Dict[str, Any]:
    return {"status": "error", "message": "Channel actions not implemented in this simplified version"}

# Sample test code for SlackConsumer
if __name__ == "__main__":
    test_user_id = "1270834"
    test_message = {
        "text": "Hi, I'm working on the dashboard project for Acme Inc. Please contact john.doe@example.com for details.",
        "channel": "general",
        "user": "john_doe",  # The sender's slack_username
        "timestamp": str(datetime.datetime.utcnow())
    }
    
    result = SlackConsumer().process_message(test_user_id, test_message)
    print(result)