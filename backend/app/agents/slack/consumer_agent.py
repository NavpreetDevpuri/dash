import os
import sys
from time import sleep
from typing import List, Dict, Any, Optional
import datetime
from celery import Celery

# Add project root to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from app.agents.slack.analyser_agent import analyze_slack_message

from app.db import get_system_db, get_user_db
from app.agents.slack.schemas import Identifiers
from app.common.llm_manager import LLMManager
from arango.database import StandardDatabase

# Initialize Celery app
celery_app = Celery('slack', broker=os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0'))

# Collection names for our simplified graph
CONTACTS_COLLECTION = "contacts"
CHANNELS_COLLECTION = "slack_channels"
MESSAGES_COLLECTION = "slack_messages"
CONTACT_CHANNEL_EDGE_COLLECTION = "contact_slack_channel"
IDENTIFIERS_COLLECTION = "identifiers"
IDENTIFIER_MESSAGE_EDGE_COLLECTION = "identifier_slack_message"
CONTACT_MESSAGE_EDGE_COLLECTION = "contact_slack_message"
CHANNEL_MESSAGE_EDGE_COLLECTION = "channel_slack_message"

class SlackConsumer:
    """
    A simplified Celery consumer that processes Slack messages differently based on the payload flag:
    
      - If "is_channel" is True: only the channel (from the "to" field) is saved.
      - If "is_channel" is False: only the contact (from the "from" field) is saved.
      
    The message document is then inserted with either a channel_id or sender_id accordingly.
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
          FILTER contact.slack_username == "{slack_username}"
          RETURN contact._id
        """
        cursor = db.aql.execute(aql)
        contact_ids = list(cursor)
        if contact_ids:
            return contact_ids[0]

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
          FILTER channel.name == "{channel_name}"
          RETURN channel._id
        """
        cursor = db.aql.execute(aql)
        channel_ids = list(cursor)
        if channel_ids:
            return channel_ids[0]

        channel_doc = {
            "name": channel_name,
            "created_at": datetime.datetime.now().isoformat(),
            "active": True
        }
        result = db.collection(CHANNELS_COLLECTION).insert(channel_doc)
        return result["_id"]

    def _add_message(self, db: StandardDatabase, message_data: Dict[str, Any],
                     contact_id: Optional[str] = None, channel_id: Optional[str] = None) -> Optional[str]:
        """
        Add a message document that includes either a contact or a channel reference.
        """
        if not db.has_collection(MESSAGES_COLLECTION):
            return None

        message_doc = {
            **message_data,
            "created_at": datetime.datetime.now().isoformat()
        }
        if contact_id is not None:
            message_doc["sender_id"] = contact_id
        if channel_id is not None:
            message_doc["channel_id"] = channel_id

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

    def _add_edge(self, db: StandardDatabase, from_id: str, to_id: str, collection_name: str) -> Optional[str]:
        """
        Add an edge between two vertices if it does not already exist.
        """
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
        result = db.collection(collection_name).insert(edge_doc)
        return result["_id"]

    def process_message(self, user_id: str, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an incoming Slack message using the new payload structure:
        
          - "from": sender username
          - "to": either a channel name (if is_channel is True) or a recipient identifier (if not)
          - "is_channel": if True, process as a channel message; otherwise process as a direct message (contact)
        """
        try:
            db = get_user_db(user_id)
            if not db:
                return {"status": "error", "message": "Failed to connect to database"}

            content = message_data.get("text", "")
            if not content or not content.strip():
                return {"status": "error", "message": "Message content is empty"}

            is_channel = message_data.get("is_channel", False)
            identifier_ids = []
            message_id = None

            if is_channel:
                # For channel messages, save the channel (from the "to" field)
                channel_name = message_data.get("to")
                if not channel_name or not channel_name.strip():
                    return {"status": "error", "message": "No valid channel found in message data"}
                channel_id = self._add_channel(db, channel_name)
                if not channel_id:
                    return {"status": "error", "message": "Failed to add channel"}
                message_id = self._add_message(db, message_data, channel_id=channel_id)
                result_data = {"channel_id": channel_id}
                # Create edge between channel and message
                self._add_edge(db, channel_id, message_id, CHANNEL_MESSAGE_EDGE_COLLECTION)
            else:
                # For direct messages, save the contact (from the "from" field)
                contact_username = message_data.get("from")
                if not contact_username or not contact_username.strip():
                    return {"status": "error", "message": "No valid sender found in message data"}
                contact_id = self._add_contact(db, contact_username)
                if not contact_id:
                    return {"status": "error", "message": "Failed to add contact"}
                message_id = self._add_message(db, message_data, contact_id=contact_id)
                result_data = {"contact_id": contact_id}
                # Create edge between contact and message
                self._add_edge(db, contact_id, message_id, CONTACT_MESSAGE_EDGE_COLLECTION)

            if not message_id:
                return {"status": "error", "message": "Failed to add message"}

            # Extract identifiers from the message content.
            identifiers = self.extract_identifiers(content)
            for identifier in identifiers:
                id_id = self._add_identifier(db, identifier)
                if id_id:
                    identifier_ids.append(id_id)
                    # Create an edge from the identifier to the message.
                    self._add_edge(db, id_id, message_id, IDENTIFIER_MESSAGE_EDGE_COLLECTION)

            result_data.update({
                "status": "success",
                "message": "Message processed successfully",
                "message_id": message_id,
                "identifiers": identifiers,
                "identifier_ids": identifier_ids
            })
            celery_app.send_task('slack.analyze_message', args=[user_id, message_data, identifiers, message_id])
            return result_data

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
    import app.agents.slack.analyser_agent as analyser

    test_user_id = "1270834"
    test_message = {
        "from": "john_doe",
        "to": "general",
        "is_channel": True,
        "text": "Hi, I'm working on the dashboard project for Acme Inc. Please contact john.doe@example.com for details.",
        "timestamp": str(datetime.datetime.utcnow())
    }
    test_message1 = {
        "from": "john_doe",
        "to": "nav",
        "is_channel": False,
        "text": "Hi, I'm working on the dashboard project for Acme Inc. Please contact john.doe@example.com for details.",
        "timestamp": str(datetime.datetime.utcnow())
    }
    
    # For channel message – only channel will be saved.
    result_channel = SlackConsumer().process_message(test_user_id, test_message)
    print("Channel message result:", result_channel)
    
    # For direct message – only contact will be saved.
    result_contact = SlackConsumer().process_message(test_user_id, test_message1)
    print("Direct message result:", result_contact)

    sleep(10)