"""
Migration file to set up the simplified Slack data graph schema in ArangoDB.
"""
import os
import sys
from arango import ArangoClient

# Add project root to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from app.db import get_system_db, get_user_db
from migrations.utils.graph_schema_base import GraphSchemaBase


class SlackGraphSchema(GraphSchemaBase):
    """Utility class to set up the Slack graph schema in ArangoDB."""

    def __init__(self):
        """
        Initialize the SlackGraphSchema.
        """
        # Define vertex collections
        vertex_collections = {
            "contacts": None,
            "slack_channels": None,
            "slack_messages": None,
            "identifiers": None,
            "analysis": None
        }
        
        # Define edge definitions for the graph
        edge_definitions = [
            {
                "edge_collection": "contact__slack_channel",
                "from_vertex_collections": ["contacts"],
                "to_vertex_collections": ["slack_channels"],
            },
            {
                "edge_collection": "identifier__slack_message",
                "from_vertex_collections": ["identifiers"],
                "to_vertex_collections": ["slack_messages"],
            },
            {
                "edge_collection": "contact__slack_message",
                "from_vertex_collections": ["contacts"],
                "to_vertex_collections": ["slack_messages"],
            },
            {
                "edge_collection": "slack_message__analysis",
                "from_vertex_collections": ["slack_messages"],
                "to_vertex_collections": ["analysis"],
            },
            {
                "edge_collection": "channel__slack_message",
                "from_vertex_collections": ["slack_channels"],
                "to_vertex_collections": ["slack_messages"],
            },
        ]

        # Initialize the base class
        super().__init__("personal_data", vertex_collections, edge_definitions)
        
        # Store collection names for easier reference
        self.contacts_collection = "contacts"
        self.slack_channels_collection = "slack_channels"
        self.slack_messages_collection = "slack_messages"
        self.identifiers_collection = "identifiers"
        self.analysis_collection = "analysis"
        
        # Set up indices
        self.add_index(self.identifiers_collection, "value", "hash", unique=True)
        self.add_index(self.slack_messages_collection, "timestamp", "skiplist", unique=False)


if __name__ == "__main__":
    schema = SlackGraphSchema()
    schema.run(db_name="user_1270834", host="http://127.0.0.1:8529", username="root", password="zxcv")
