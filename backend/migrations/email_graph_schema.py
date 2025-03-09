"""
Migration file to set up the Email data graph schema in ArangoDB.
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
            "email_attachments": None,
            "identifiers": None
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
                "edge_collection": "folder__email_message",
                "from_vertex_collections": ["email_folders"],
                "to_vertex_collections": ["email_messages"],
            },
            {
                "edge_collection": "email_message__attachment",
                "from_vertex_collections": ["email_messages"],
                "to_vertex_collections": ["email_attachments"],
            },
        ]

        # Initialize the base class
        super().__init__("personal_data", vertex_collections, edge_definitions)
        
        # Store collection names for easier reference
        self.CONTACTS_COLLECTION = "contacts"
        self.EMAIL_FOLDERS_COLLECTION = "email_folders"
        self.EMAIL_MESSAGES_COLLECTION = "email_messages"
        self.EMAIL_ATTACHMENTS_COLLECTION = "email_attachments"
        self.IDENTIFIERS_COLLECTION = "identifiers"
        self.CONTACT_FOLDER_EDGE_COLLECTION = "contact__email_folder"
        self.IDENTIFIER_MESSAGE_EDGE_COLLECTION = "identifier__email_message"
        self.CONTACT_MESSAGE_EDGE_COLLECTION = "contact__email_message"
        self.FOLDER_MESSAGE_EDGE_COLLECTION = "folder__email_message"
        self.MESSAGE_ATTACHMENT_EDGE_COLLECTION = "email_message__attachment"
        
        # Set up indices
        self.add_index(self.CONTACTS_COLLECTION, "email", "hash", unique=True)
        self.add_index(self.EMAIL_FOLDERS_COLLECTION, "name", "hash", unique=True)
        self.add_index(self.IDENTIFIERS_COLLECTION, "value", "hash", unique=True)
        self.add_index(self.EMAIL_MESSAGES_COLLECTION, "timestamp", "skiplist", unique=False)
        self.add_index(self.EMAIL_MESSAGES_COLLECTION, "subject", "hash", unique=False)


if __name__ == "__main__":
    test_user_id = "1270834"
    schema = EmailGraphSchema()
    schema.run(test_user_id) 