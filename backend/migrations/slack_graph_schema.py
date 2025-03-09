"""
Migration file to set up the Slack data graph schema in ArangoDB.
"""
import os
import sys
from arango import ArangoClient

# Add project root to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from app.db import get_system_db, get_user_db


class SlackGraphSchema:
    """Utility class to set up the Slack graph schema in ArangoDB."""

    def __init__(self):
        """
        Initialize the SlackGraphSchema.
        """
        self.db = None
        self.graph = None

        # Define orphan (vertex) collections
        self.orphan_collections = [
            "work_contacts", "slack_messages", "identifiers"
        ]

        # Define edge collections
        self.edge_definitions = [
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
        # Create index on work_contacts.email
        if self.db.has_collection("work_contacts"):
            work_contacts = self.db.collection("work_contacts")
            if not any(idx["fields"] == ["email"] for idx in work_contacts.indexes()):
                work_contacts.add_hash_index(fields=["email"], unique=True)
                print("Added unique hash index on work_contacts.email")
                
        # Create index on identifiers.value
        if self.db.has_collection("identifiers"):
            identifiers = self.db.collection("identifiers")
            if not any(idx["fields"] == ["value"] for idx in identifiers.indexes()):
                identifiers.add_hash_index(fields=["value"], unique=True)
                print("Added unique hash index on identifiers.value")
                
        # Create timestamp index on slack_messages
        if self.db.has_collection("slack_messages"):
            messages = self.db.collection("slack_messages")
            if not any(idx["fields"] == ["timestamp"] for idx in messages.indexes()):
                messages.add_skiplist_index(fields=["timestamp"])
                print("Added skiplist index on slack_messages.timestamp")
                
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
    test_user_id = "test_user"
    schema = SlackGraphSchema()
    schema.run(test_user_id) 