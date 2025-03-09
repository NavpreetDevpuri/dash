"""
Migration file to set up the simplified Slack data graph schema in ArangoDB.
"""
import os
import sys
from arango import ArangoClient

# Add project root to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from app.db import get_system_db, get_user_db


class SlackGraphSchema:
    """Utility class to set up the Slack graph schema in ArangoDB."""

    def __init__(self):
        """
        Initialize the SlackGraphSchema.
        """
        self.db = None
        self.graph = None

        # Define vertex (orphan) collections
        self.contacts_collection = "contacts"
        self.slack_channels_collection = "slack_channels"
        self.slack_messages_collection = "slack_messages"
        self.identifiers_collection = "identifiers"
        
        # Define edge collections
        self.contact_slack_channel_edge_collection = "contact_slack_channel"
        self.identifier_slack_message_edge_collection = "identifier_slack_message"

        # List of vertex collections for the graph
        self.orphan_collections = [
            self.contacts_collection,
            self.slack_channels_collection,
            self.slack_messages_collection,
            self.identifiers_collection
        ]

        # Define edge definitions for the graph
        self.edge_definitions = [
            {
                "edge_collection": self.contact_slack_channel_edge_collection,
                "from_vertex_collections": [self.contacts_collection],
                "to_vertex_collections": [self.slack_channels_collection],
            },
            {
                "edge_collection": self.identifier_slack_message_edge_collection,
                "from_vertex_collections": [self.identifiers_collection],
                "to_vertex_collections": [self.slack_messages_collection],
            },
        ]

    def setup_db(self, user_id: str):
        """
        Connect to the user's database and set up the graph.
        
        Args:
            user_id: User ID to get database connection for
        """
        self.db = get_user_db(user_id)
        if not self.db:
            raise Exception(f"Failed to connect to database for user {user_id}")

        if not self.db.has_graph("slack_data"):
            self.graph = self.db.create_graph("slack_data",
                                              edge_definitions=self.edge_definitions,
                                              orphan_collections=self.orphan_collections)
            print("Graph 'slack_data' created successfully.")
        else:
            self.graph = self.db.graph("slack_data")
            print("Graph 'slack_data' already exists.")
            
    def create_indices(self):
        """Create indices on collections for faster queries."""
        # Create a unique hash index on contacts.slack_username
        if self.db.has_collection(self.contacts_collection):
            contacts = self.db.collection(self.contacts_collection)
            if not any(idx["fields"] == ["slack_username"] for idx in contacts.indexes()):
                contacts.add_hash_index(fields=["slack_username"], unique=True)
                print(f"Added unique hash index on {self.contacts_collection}.slack_username")
                
        # Create a unique hash index on slack_channels.name
        if self.db.has_collection(self.slack_channels_collection):
            channels = self.db.collection(self.slack_channels_collection)
            if not any(idx["fields"] == ["name"] for idx in channels.indexes()):
                channels.add_hash_index(fields=["name"], unique=True)
                print(f"Added unique hash index on {self.slack_channels_collection}.name")
                
        # Create a unique hash index on identifiers.value
        if self.db.has_collection(self.identifiers_collection):
            identifiers = self.db.collection(self.identifiers_collection)
            if not any(idx["fields"] == ["value"] for idx in identifiers.indexes()):
                identifiers.add_hash_index(fields=["value"], unique=True)
                print(f"Added unique hash index on {self.identifiers_collection}.value")
                
        # Create a skiplist index on slack_messages.timestamp
        if self.db.has_collection(self.slack_messages_collection):
            messages = self.db.collection(self.slack_messages_collection)
            if not any(idx["fields"] == ["timestamp"] for idx in messages.indexes()):
                messages.add_skiplist_index(fields=["timestamp"])
                print(f"Added skiplist index on {self.slack_messages_collection}.timestamp")
                
    def run(self, user_id: str):
        """
        Set up the database and graph schema for a specific user.
        
        Args:
            user_id: User ID to set up schema for
        """
        self.setup_db(user_id)
        self.create_indices()
        print(f"Slack graph schema setup complete for user {user_id}.")


if __name__ == "__main__":
    # Set up for a test user - in production you'd iterate through all users
    test_user_id = "1270834"
    schema = SlackGraphSchema()
    schema.run(test_user_id)