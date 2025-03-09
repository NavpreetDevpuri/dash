"""
Migration file to set up the WhatsApp data graph schema in ArangoDB.
"""

import os
import sys
from arango import ArangoClient

# Add project root to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from app.db import get_system_db, get_user_db

class WhatsAppGraphSchema:
    """Utility class to set up the WhatsApp graph schema in ArangoDB."""
    def __init__(self):
        self.db = None
        self.graph = None

        # Vertex collections
        self.contacts_collection = "contacts"
        self.whatsapp_groups_collection = "whatsapp_groups"  # for groups or conversations
        self.whatsapp_messages_collection = "whatsapp_messages"
        self.identifiers_collection = "identifiers"

        # Edge collections (using updated names)
        self.contact_whatsapp_message_edge_collection = "contact__whatsapp_message"
        self.contact_whatsapp_group_edge_collection = "contact__whatsapp_group"
        self.whatsapp_group_message_edge_collection = "whatsapp_group__message"
        self.whatsapp_identifier_message_edge_collection = "whatsapp_identifier__message"

        # List of vertex collections for the graph
        self.orphan_collections = [
            self.contacts_collection,
            self.whatsapp_groups_collection,
            self.whatsapp_messages_collection,
            self.identifiers_collection
        ]

        # Define edge definitions for the graph, including the new contact__whatsapp_group edge
        self.edge_definitions = [
            {
                "edge_collection": self.contact_whatsapp_message_edge_collection,
                "from_vertex_collections": [self.contacts_collection],
                "to_vertex_collections": [self.whatsapp_messages_collection],
            },
            {
                "edge_collection": self.whatsapp_group_message_edge_collection,
                "from_vertex_collections": [self.whatsapp_groups_collection],
                "to_vertex_collections": [self.whatsapp_messages_collection],
            },
            {
                "edge_collection": self.whatsapp_identifier_message_edge_collection,
                "from_vertex_collections": [self.identifiers_collection],
                "to_vertex_collections": [self.whatsapp_messages_collection],
            },
            {
                "edge_collection": self.contact_whatsapp_group_edge_collection,
                "from_vertex_collections": [self.contacts_collection],
                "to_vertex_collections": [self.whatsapp_groups_collection],
            },
        ]

    def setup_db(self, user_id: str):
        """
        Connect to the user's database and set up the graph.
        """
        self.db = get_user_db(user_id)
        if not self.db:
            raise Exception(f"Failed to connect to database for user {user_id}")

        if not self.db.has_graph("whatsapp_data"):
            self.graph = self.db.create_graph(
                "whatsapp_data",
                edge_definitions=self.edge_definitions,
                orphan_collections=self.orphan_collections
            )
            print("Graph 'whatsapp_data' created successfully.")
        else:
            self.graph = self.db.graph("whatsapp_data")
            print("Graph 'whatsapp_data' already exists.")

    def create_indices(self):
        """Create indices on collections for faster queries."""
        # Create unique index on contacts.whatsapp_number
        if self.db.has_collection(self.contacts_collection):
            contacts = self.db.collection(self.contacts_collection)
            if not any(idx["fields"] == ["whatsapp_number"] for idx in contacts.indexes()):
                contacts.add_hash_index(fields=["whatsapp_number"], unique=True)
                print(f"Added unique hash index on {self.contacts_collection}.whatsapp_number")

        # Create unique index on whatsapp_groups.identifier
        if self.db.has_collection(self.whatsapp_groups_collection):
            groups = self.db.collection(self.whatsapp_groups_collection)
            if not any(idx["fields"] == ["identifier"] for idx in groups.indexes()):
                groups.add_hash_index(fields=["identifier"], unique=True)
                print(f"Added unique hash index on {self.whatsapp_groups_collection}.identifier")

        # Create unique index on identifiers.value
        if self.db.has_collection(self.identifiers_collection):
            identifiers = self.db.collection(self.identifiers_collection)
            if not any(idx["fields"] == ["value"] for idx in identifiers.indexes()):
                identifiers.add_hash_index(fields=["value"], unique=True)
                print(f"Added unique hash index on {self.identifiers_collection}.value")

        # Create skiplist index on whatsapp_messages.created_at
        if self.db.has_collection(self.whatsapp_messages_collection):
            messages = self.db.collection(self.whatsapp_messages_collection)
            if not any(idx["fields"] == ["created_at"] for idx in messages.indexes()):
                messages.add_skiplist_index(fields=["created_at"])
                print(f"Added skiplist index on {self.whatsapp_messages_collection}.created_at")

    def run(self, user_id: str):
        """
        Set up the database and graph schema for a specific user.
        """
        self.setup_db(user_id)
        self.create_indices()
        print(f"WhatsApp graph schema setup complete for user {user_id}.")

if __name__ == "__main__":
    test_user_id = "1270834"
    schema = WhatsAppGraphSchema()
    schema.run(test_user_id)