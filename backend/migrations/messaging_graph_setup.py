import os
import sys
from typing import List, Dict, Any, Optional

# Add root directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from arango import ArangoClient
from arango.database import StandardDatabase
from arango.graph import Graph

class MessagingGraphSetup:
    """
    Setup for messaging graph database collections and indexes.
    """
    
    def __init__(self,
                db_name="my_database",
                host="http://localhost:8529",
                username="root",
                password="zxcv"):
        """
        Initialize graph setup with database connection parameters.
        
        Args:
            db_name: ArangoDB database name
            host: ArangoDB host URL
            username: Database username
            password: Database password
        """
        self.db_name = db_name
        self.host = host
        self.username = username
        self.password = password
        
        # Graph and collection names
        self.private_graph_name = "private_graph"
        
        # Define vertex collections for all messaging platforms
        self.vertex_collections = [
            # Slack collections
            "slack_users",
            "slack_channels",
            "slack_messages",
            "slack_files",
            "slack_reactions",
            "slack_status",
            
            # WhatsApp collections
            "whatsapp_contacts",
            "whatsapp_groups",
            "whatsapp_messages",
            "whatsapp_media"
        ]
        
        # Define edge collections for all messaging platforms
        self.edge_collections = [
            # Slack edges
            "slack_member_of",
            
            # WhatsApp edges
            "whatsapp_member_of",
        ]
        
        # Define edge definitions for the private graph
        self.edge_definitions = [
            # Slack edge definitions
            {
                "edge_collection": "slack_member_of",
                "from_vertex_collections": ["slack_users"],
                "to_vertex_collections": ["slack_channels"]
            },
            
            # WhatsApp edge definitions
            {
                "edge_collection": "whatsapp_member_of",
                "from_vertex_collections": ["whatsapp_contacts"],
                "to_vertex_collections": ["whatsapp_groups"]
            },
        ]
        
        # Database connection
        self.client = None
        self.db = None
        self.setup_success = False
        
    def connect_to_db(self):
        """
        Connect to ArangoDB and verify connection.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Connect to ArangoDB
            self.client = ArangoClient(hosts=self.host)
            sys_db = self.client.db('_system', username=self.username, password=self.password)
            
            # Create database if it doesn't exist
            if not sys_db.has_database(self.db_name):
                sys_db.create_database(self.db_name)
                print(f"Created database: {self.db_name}")
            else:
                print(f"Database already exists: {self.db_name}")
            
            # Connect to the database
            self.db = self.client.db(self.db_name, username=self.username, password=self.password)
            print(f"Connected to database: {self.db_name}")
            return True
        
        except Exception as e:
            print(f"Database connection error: {str(e)}")
            return False
    
    def create_collections(self):
        """
        Create all vertex and edge collections if they don't exist.
        
        Returns:
            True if collections created successfully, False otherwise
        """
        try:
            # Create vertex collections
            for collection_name in self.vertex_collections:
                if not self.db.has_collection(collection_name):
                    self.db.create_collection(collection_name)
                    print(f"Created vertex collection: {collection_name}")
                else:
                    print(f"Vertex collection already exists: {collection_name}")
            
            # Create edge collections
            for collection_name in self.edge_collections:
                if not self.db.has_collection(collection_name):
                    self.db.create_collection(collection_name, edge=True)
                    print(f"Created edge collection: {collection_name}")
                else:
                    print(f"Edge collection already exists: {collection_name}")
            
            return True
        
        except Exception as e:
            print(f"Error creating collections: {str(e)}")
            return False
    
    def create_indexes(self):
        """
        Create indexes for efficient queries.
        
        Returns:
            True if indexes created successfully, False otherwise
        """
        try:
            # Create indexes for Slack collections
            # Users
            slack_users = self.db.collection("slack_users")
            if not any(idx["fields"] == ["username"] for idx in slack_users.indexes()):
                slack_users.add_hash_index(fields=["username"], unique=True)
                print("Created index on slack_users.username")
            
            if not any(idx["fields"] == ["email"] for idx in slack_users.indexes()):
                slack_users.add_hash_index(fields=["email"], unique=True)
                print("Created index on slack_users.email")
                
            # Channels
            slack_channels = self.db.collection("slack_channels")
            if not any(idx["fields"] == ["name"] for idx in slack_channels.indexes()):
                slack_channels.add_hash_index(fields=["name"], unique=True)
                print("Created index on slack_channels.name")
            
            # Messages
            slack_messages = self.db.collection("slack_messages")
            if not any(idx["fields"] == ["timestamp"] for idx in slack_messages.indexes()):
                slack_messages.add_skiplist_index(fields=["timestamp"])
                print("Created index on slack_messages.timestamp")
            
            if not any(idx["fields"] == ["content"] for idx in slack_messages.indexes()):
                slack_messages.add_fulltext_index(fields=["content"])
                print("Created fulltext index on slack_messages.content")
            
            # Create indexes for WhatsApp collections
            # Contacts
            whatsapp_contacts = self.db.collection("whatsapp_contacts")
            if not any(idx["fields"] == ["phone_number"] for idx in whatsapp_contacts.indexes()):
                whatsapp_contacts.add_hash_index(fields=["phone_number"], unique=True)
                print("Created index on whatsapp_contacts.phone_number")
            
            if not any(idx["fields"] == ["name"] for idx in whatsapp_contacts.indexes()):
                whatsapp_contacts.add_hash_index(fields=["name"])
                print("Created index on whatsapp_contacts.name")
            
            # Groups
            whatsapp_groups = self.db.collection("whatsapp_groups")
            if not any(idx["fields"] == ["name"] for idx in whatsapp_groups.indexes()):
                whatsapp_groups.add_hash_index(fields=["name"], unique=True)
                print("Created index on whatsapp_groups.name")
            
            # Messages
            whatsapp_messages = self.db.collection("whatsapp_messages")
            if not any(idx["fields"] == ["timestamp"] for idx in whatsapp_messages.indexes()):
                whatsapp_messages.add_skiplist_index(fields=["timestamp"])
                print("Created index on whatsapp_messages.timestamp")
            
            if not any(idx["fields"] == ["content"] for idx in whatsapp_messages.indexes()):
                whatsapp_messages.add_fulltext_index(fields=["content"])
                print("Created fulltext index on whatsapp_messages.content")
            
            return True
        
        except Exception as e:
            print(f"Error creating indexes: {str(e)}")
            return False
    
    def create_graphs(self):
        """
        Create graph with edge definitions if they don't exist.
        
        Returns:
            True if graph created successfully, False otherwise
        """
        try:
            # Create private graph
            private_graph = None
            if not self.db.has_graph(self.private_graph_name):
                private_graph = self.db.create_graph(self.private_graph_name)
                print(f"Created graph: {self.private_graph_name}")
            else:
                print(f"Graph already exists: {self.private_graph_name}")
                private_graph = self.db.graph(self.private_graph_name)
            
            # Add edge definitions to private graph
            for edge_definition in self.edge_definitions:
                edge_collection = edge_definition["edge_collection"]
                from_collections = edge_definition["from_vertex_collections"]
                to_collections = edge_definition["to_vertex_collections"]
                
                # Check if edge definition already exists
                try:
                    private_graph.edge_collection(edge_collection)
                    print(f"Edge definition for {edge_collection} already exists in {self.private_graph_name}")
                except Exception:
                    try:
                        # Create the edge definition
                        private_graph.create_edge_definition(
                            edge_collection=edge_collection,
                            from_vertex_collections=from_collections,
                            to_vertex_collections=to_collections
                        )
                        print(f"Added edge definition for {edge_collection} to {self.private_graph_name}")
                    except Exception as e:
                        print(f"Error adding edge definition for {edge_collection}: {str(e)}")
                        if "duplicate edge collection" in str(e).lower():
                            print("Skipping duplicate edge collection error and continuing...")
                            continue
            
            return True
        
        except Exception as e:
            print(f"Error creating graph: {str(e)}")
            return False
    
    def run(self):
        """
        Run the complete setup process.
        
        Returns:
            True if setup completed successfully, False otherwise
        """
        # Connect to database
        if not self.connect_to_db():
            return False
        
        # Create collections
        if not self.create_collections():
            return False
        
        # Create indexes
        if not self.create_indexes():
            return False
        
        # Create graph
        if not self.create_graphs():
            return False
        
        self.setup_success = True
        print("Database setup completed successfully!")
        return True

if __name__ == "__main__":
    # Create and run the setup
    setup = MessagingGraphSetup()
    setup.run() 