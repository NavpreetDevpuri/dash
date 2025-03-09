"""
Migration script to import Slack messages with identifiers from slack_messages.json.
"""

import os
import sys
import json
import datetime
from arango import ArangoClient

# Add project root to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from app.db import get_system_db, get_user_db


class SlackMessagesImporter:
    """Class to import Slack messages with identifiers from JSON file."""
    
    def __init__(self, user_id, contacts_path, messages_path, host="http://localhost:8529", 
                 username="root", password="zxcv"):
        """
        Initialize the SlackMessagesImporter.
        
        Args:
            user_id: User ID to import data for
            contacts_path: Path to contacts.json file
            messages_path: Path to slack_messages.json file
            host: ArangoDB host URL
            username: ArangoDB username
            password: ArangoDB password
        """
        self.user_id = user_id
        self.contacts_path = contacts_path
        self.messages_path = messages_path
        self.host = host
        self.username = username
        self.password = password
        
        # Collection names
        self.contacts_collection = "contacts"
        self.slack_channels_collection = "slack_channels"
        self.slack_messages_collection = "slack_messages"
        self.identifiers_collection = "identifiers"
        
        # Edge collection names
        self.contact_message_edge = "contact__slack_message"
        self.identifier_message_edge = "identifier__slack_message"
        self.channel_message_edge = "channel__slack_message"
        
        # Connect to DB
        self.setup_db()
    
    def setup_db(self):
        """Connect to the user's database."""
        client = ArangoClient(hosts=self.host)
        sys_db = client.db("_system", username=self.username, password=self.password, verify=True)
        
        db_name = f"user_{self.user_id}"
        if not sys_db.has_database(db_name):
            raise Exception(f"Database '{db_name}' does not exist.")
        
        self.db = client.db(db_name, username=self.username, password=self.password, verify=True)
        print(f"Connected to database '{db_name}'.")
    
    def load_contacts(self):
        """Load contacts data from JSON file."""
        with open(self.contacts_path, "r") as f:
            contacts_data = json.load(f)
        
        # Filter only work contacts with slack usernames
        self.work_contacts = []
        for contact in contacts_data.get("work_contacts", []):
            if "slack_username" in contact:
                self.work_contacts.append(contact)
        
        print(f"Loaded {len(self.work_contacts)} work contacts with Slack usernames.")
    
    def load_messages(self):
        """Load messages data from JSON file."""
        with open(self.messages_path, "r") as f:
            messages_data = json.load(f)
        
        self.messages = messages_data.get("messages", [])
        print(f"Loaded {len(self.messages)} Slack messages.")
    
    def ensure_project_x_channel(self):
        """Ensure the ProjectX channel exists."""
        channels_collection = self.db.collection(self.slack_channels_collection)
        
        # Check if channel already exists
        try:
            channels_collection.get("project_x")
            print("ProjectX channel already exists.")
            return
        except:
            # Create channel
            channel = {
                "_key": "project_x",
                "name": "project-x",
                "description": "Channel for ProjectX development and updates",
                "created_at": datetime.datetime.now().isoformat(),
                "is_private": False
            }
            
            channels_collection.insert(channel)
            print("Created ProjectX channel.")
    
    def find_contact_by_username(self, username):
        """Find a contact document by Slack username."""
        contacts = self.db.collection(self.contacts_collection)
        cursor = contacts.find({"slack_username": username})
        results = [doc for doc in cursor]
        
        if results:
            return results[0]
        return None
    
    def import_messages(self):
        """Import the Slack messages and their identifiers."""
        messages_collection = self.db.collection(self.slack_messages_collection)
        contact_edge = self.db.collection(self.contact_message_edge)
        identifier_edge = self.db.collection(self.identifier_message_edge)
        channel_edge = self.db.collection(self.channel_message_edge)
        identifiers_collection = self.db.collection(self.identifiers_collection)
        
        for i, message_data in enumerate(self.messages):
            from_username = message_data["from"]
            to_channel = message_data["to"]
            is_channel = message_data["is_channel"]
            text = message_data["text"]
            timestamp = message_data["timestamp"]
            
            # Find contact
            contact = self.find_contact_by_username(from_username)
            if not contact:
                print(f"Warning: Could not find contact with username '{from_username}'")
                continue
            
            # Create message
            message_key = f"slack_message_{i+1}"
            message = {
                "_key": message_key,
                "from": from_username,
                "to": to_channel,
                "is_channel": is_channel,
                "text": text,
                "timestamp": timestamp
            }
            
            # Insert message
            try:
                messages_collection.insert(message)
                print(f"Created message {message_key}.")
            except Exception as e:
                print(f"Error creating message: {e}")
                continue
            
            # Create edges
            try:
                # Contact -> Message edge
                contact_edge.insert({
                    "_from": f"{self.contacts_collection}/{contact['_key']}",
                    "_to": f"{self.slack_messages_collection}/{message_key}",
                    "is_author": True
                })
                
                # Channel -> Message edge
                channel_edge.insert({
                    "_from": f"{self.slack_channels_collection}/project_x",
                    "_to": f"{self.slack_messages_collection}/{message_key}"
                })
                
                # Process identifiers
                for identifier_data in message_data.get("identifiers", []):
                    identifier_value = identifier_data["value"]
                    identifier_key = identifier_data["key"]
                    
                    # Create or get identifier
                    try:
                        identifiers_collection.get(identifier_key)
                        print(f"Identifier '{identifier_value}' already exists.")
                    except:
                        # Create identifier with simplified structure
                        identifier = {
                            "_key": identifier_key,
                            "value": identifier_value,
                            "created_at": datetime.datetime.now().isoformat()
                        }
                        
                        identifiers_collection.insert(identifier)
                        print(f"Created identifier for '{identifier_value}'.")
                    
                    # Create identifier -> message edge
                    edge_data = {
                        "_from": f"{self.identifiers_collection}/{identifier_key}",
                        "_to": f"{self.slack_messages_collection}/{message_key}"
                    }
                    
                    # Detect if this is a mention
                    if identifier_value.startswith("@"):
                        edge_data["is_mention"] = True
                        
                    identifier_edge.insert(edge_data)
            except Exception as e:
                print(f"Error creating edges for message {message_key}: {e}")
    
    def run(self):
        """Run the import process."""
        self.load_contacts()
        self.load_messages()
        self.ensure_project_x_channel()
        self.import_messages()
        print("Slack messages import completed.")


if __name__ == "__main__":
    current_dir = os.path.dirname(__file__)
    user_id = "1270834"  # Use the same user_id as in other migrations
    
    importer = SlackMessagesImporter(
        user_id=user_id,
        contacts_path=os.path.join(current_dir, "data", "contacts.json"),
        messages_path=os.path.join(current_dir, "data", "slack_messages.json"),
        host="http://localhost:8529",
        username="root",
        password="zxcv"
    )
    
    importer.run() 