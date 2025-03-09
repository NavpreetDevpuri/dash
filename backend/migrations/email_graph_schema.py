"""
Migration file to set up the Email data graph schema in ArangoDB.
"""
import os
import sys
from arango import ArangoClient

# Add project root to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from app.db import get_system_db, get_user_db


class EmailGraphSchema:
    """Utility class to set up the Email graph schema in ArangoDB."""

    def __init__(self):
        """
        Initialize the EmailGraphSchema.
        """
        self.db = None
        self.graph = None

        # Define orphan (vertex) collections
        self.orphan_collections = [
            "work_contacts", "emails", "identifiers", "attachments"
        ]

        # Define edge collections
        self.edge_definitions = [
            {
                "edge_collection": "contact_email",
                "from_vertex_collections": ["work_contacts"],
                "to_vertex_collections": ["emails"],
            },
            {
                "edge_collection": "identifier_email",
                "from_vertex_collections": ["identifiers"],
                "to_vertex_collections": ["emails"],
            },
            {
                "edge_collection": "email_attachment",
                "from_vertex_collections": ["emails"],
                "to_vertex_collections": ["attachments"],
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

        if not self.db.has_graph("email_data"):
            self.graph = self.db.create_graph("email_data",
                                              edge_definitions=self.edge_definitions,
                                              orphan_collections=self.orphan_collections)
            print("Graph 'email_data' created successfully.")
        else:
            self.graph = self.db.graph("email_data")
            print("Graph 'email_data' already exists.")
            
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
                
        # Create timestamp index on emails
        if self.db.has_collection("emails"):
            emails = self.db.collection("emails")
            if not any(idx["fields"] == ["timestamp"] for idx in emails.indexes()):
                emails.add_skiplist_index(fields=["timestamp"])
                print("Added skiplist index on emails.timestamp")
                
        # Create index on sender
        if self.db.has_collection("emails"):
            emails = self.db.collection("emails")
            if not any(idx["fields"] == ["sender"] for idx in emails.indexes()):
                emails.add_hash_index(fields=["sender"])
                print("Added hash index on emails.sender")
                
        # Create index on attachments file hash
        if self.db.has_collection("attachments"):
            attachments = self.db.collection("attachments")
            if not any(idx["fields"] == ["content_hash"] for idx in attachments.indexes()):
                attachments.add_hash_index(fields=["content_hash"])
                print("Added hash index on attachments.content_hash")
                
    def run(self, user_id: str):
        """
        Set up the database and graph schema for a specific user.
        
        Args:
            user_id: User ID to set up schema for
        """
        self.setup_db(user_id)
        self.create_indices()
        print(f"Email graph schema setup complete for user {user_id}.")


if __name__ == "__main__":
    # Set up for a test user - in production you'd iterate through all users
    test_user_id = "test_user"
    schema = EmailGraphSchema()
    schema.run(test_user_id) 