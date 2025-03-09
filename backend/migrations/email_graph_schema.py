"""
Migration file to set up the email data graph schema in ArangoDB.
"""
import os
import sys
from arango import ArangoClient

# Add project root to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from app.db import get_system_db, get_user_db
from migrations.utils.graph_schema_base import GraphSchemaBase


class EmailGraphSchema(GraphSchemaBase):
    """Utility class to set up the Email graph schema in ArangoDB."""

    def __init__(self):
        """
        Initialize the EmailGraphSchema.
        """
        # Define vertex collections
        vertex_collections = {
            "contacts": None,
            "email_folders": None,
            "email_messages": None,
            "identifiers": None,
            "analysis": None
        }
        
        # Define edge definitions for the graph
        edge_definitions = [
            {
                "edge_collection": "contact__email_folder",
                "from_vertex_collections": ["contacts"],
                "to_vertex_collections": ["email_folders"],
            },
            {
                "edge_collection": "identifier__email_message",
                "from_vertex_collections": ["identifiers"],
                "to_vertex_collections": ["email_messages"],
            },
            {
                "edge_collection": "contact__email_message",
                "from_vertex_collections": ["contacts"],
                "to_vertex_collections": ["email_messages"],
            },
            {
                "edge_collection": "email_message__analysis",
                "from_vertex_collections": ["email_messages"],
                "to_vertex_collections": ["analysis"],
            },
            {
                "edge_collection": "folder__email_message",
                "from_vertex_collections": ["email_folders"],
                "to_vertex_collections": ["email_messages"],
            },
        ]

        # Initialize the base class
        super().__init__("personal_data", vertex_collections, edge_definitions)
        
        # Store collection names for easier reference
        self.contacts_collection = "contacts"
        self.email_folders_collection = "email_folders"
        self.email_messages_collection = "email_messages"
        self.identifiers_collection = "identifiers"
        self.analysis_collection = "analysis"
        
        # Set up indices
        self.add_index(self.contacts_collection, "email_address", "hash", unique=True)
        self.add_index(self.email_folders_collection, "name", "hash", unique=True)
        self.add_index(self.identifiers_collection, "value", "hash", unique=True)
        self.add_index(self.email_messages_collection, "timestamp", "skiplist", unique=False)
        self.add_index(self.email_messages_collection, "subject", "hash", unique=False)


if __name__ == "__main__":
    test_user_id = "1270834"
    schema = EmailGraphSchema()
    schema.run(test_user_id) 