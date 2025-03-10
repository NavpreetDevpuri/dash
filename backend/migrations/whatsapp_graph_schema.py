"""
Migration file to set up the WhatsApp data graph schema in ArangoDB.
"""

import os
import sys
from arango import ArangoClient

# Add project root to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from app.db import get_system_db, get_user_db
from migrations.utils.graph_schema_base import GraphSchemaBase

class WhatsAppGraphSchema(GraphSchemaBase):
    """Utility class to set up the WhatsApp graph schema in ArangoDB."""
    def __init__(self):
        # Define vertex collections 
        vertex_collections = {
            "contacts": None,
            "whatsapp_groups": None,  # for groups or conversations
            "whatsapp_messages": None,
            "identifiers": None
        }

        # Define edge definitions for the graph
        edge_definitions = [
            {
                "edge_collection": "contact__whatsapp_message",
                "from_vertex_collections": ["contacts"],
                "to_vertex_collections": ["whatsapp_messages"],
            },
            {
                "edge_collection": "whatsapp_group__message",
                "from_vertex_collections": ["whatsapp_groups"],
                "to_vertex_collections": ["whatsapp_messages"],
            },
            {
                "edge_collection": "whatsapp_identifier__message",
                "from_vertex_collections": ["identifiers"],
                "to_vertex_collections": ["whatsapp_messages"],
            },
            {
                "edge_collection": "contact__whatsapp_group",
                "from_vertex_collections": ["contacts"],
                "to_vertex_collections": ["whatsapp_groups"],
            },
        ]

        # Initialize the base class
        super().__init__("personal_data", vertex_collections, edge_definitions)
        
        # Store collection names for easier reference
        self.contacts_collection = "contacts"
        self.whatsapp_groups_collection = "whatsapp_groups"
        self.whatsapp_messages_collection = "whatsapp_messages"
        self.identifiers_collection = "identifiers"
        
        # Set up indices
        self.add_index(self.whatsapp_messages_collection, "created_at", "skiplist", unique=False)


if __name__ == "__main__":
    schema = WhatsAppGraphSchema()
    schema.run(db_name="user_1270834", host="http://127.0.0.1:8529", username="root", password="zxcv")
