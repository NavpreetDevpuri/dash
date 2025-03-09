import os
import sys
import argparse
from typing import List, Dict, Any
from arango import ArangoClient
import traceback

# Add project root to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))


class MessagingGraphSetup:
    """
    A migration script to set up the graph database structure for messaging systems (Slack and WhatsApp).
    This creates the necessary collections, edge definitions, and indexes for efficient queries.
    """
    
    def __init__(self,
                db_name="my_database",
                host="http://localhost:8529",
                username="root",
                password="zxcv"):
        """
        Initialize the MessagingGraphSetup.
        
        Args:
            db_name: The name of the database
            host: The ArangoDB host URL
            username: The ArangoDB username
            password: The ArangoDB password
        """
        self.db_name = db_name
        self.host = host
        self.username = username
        self.password = password
        self.client = None
        self.db = None
        
        # Slack graph definition
        self.slack_graph_name = "slack_data"
        self.slack_edge_definitions = [
            {
                "edge_collection": "slack_contact_message",
                "from_vertex_collections": ["work_contacts"],
                "to_vertex_collections": ["slack_messages"],
            },
            {
                "edge_collection": "slack_identifier_message",
                "from_vertex_collections": ["identifiers"],
                "to_vertex_collections": ["slack_messages"],
            },
            {
                "edge_collection": "slack_message_analysis",
                "from_vertex_collections": ["analyzer_identifiers"],
                "to_vertex_collections": ["slack_messages"],
            }
        ]
        self.slack_orphan_collections = []
        
        # WhatsApp graph definition
        self.whatsapp_graph_name = "whatsapp_data"
        self.whatsapp_edge_definitions = [
            {
                "edge_collection": "whatsapp_contact_message",
                "from_vertex_collections": ["work_contacts"],
                "to_vertex_collections": ["whatsapp_messages"],
            },
            {
                "edge_collection": "whatsapp_identifier_message",
                "from_vertex_collections": ["identifiers"],
                "to_vertex_collections": ["whatsapp_messages"],
            },
            {
                "edge_collection": "whatsapp_message_analysis",
                "from_vertex_collections": ["analyzer_identifiers"],
                "to_vertex_collections": ["whatsapp_messages"],
            }
        ]
        self.whatsapp_orphan_collections = []
        
        # Common collections across both graphs
        self.common_vertex_collections = [
            "work_contacts",
            "identifiers",
            "analyzer_identifiers"
        ]
        
        # Slack-specific collections
        self.slack_vertex_collections = [
            "slack_messages"
        ]
        
        # WhatsApp-specific collections
        self.whatsapp_vertex_collections = [
            "whatsapp_messages"
        ]
        
        # Edge collections
        self.edge_collections = [
            "slack_contact_message",
            "slack_identifier_message",
            "slack_message_analysis",
            "whatsapp_contact_message",
            "whatsapp_identifier_message",
            "whatsapp_message_analysis"
        ]
    
    def connect_to_db(self):
        """
        Connect to the ArangoDB database.
        """
        # Initialize the client
        self.client = ArangoClient(hosts=self.host)
        
        # Connect to the system database
        sys_db = self.client.db("_system", username=self.username, password=self.password)
        
        # Create the database if it doesn't exist
        if not sys_db.has_database(self.db_name):
            sys_db.create_database(self.db_name)
        
        # Connect to the application database
        self.db = self.client.db(self.db_name, username=self.username, password=self.password)
        
        print(f"Connected to database: {self.db_name}")
    
    def create_collections(self):
        """
        Create all necessary vertex and edge collections if they don't exist.
        """
        # Create common vertex collections
        for collection_name in self.common_vertex_collections:
            if not self.db.has_collection(collection_name):
                self.db.create_collection(collection_name)
                print(f"Created vertex collection: {collection_name}")
            else:
                print(f"Vertex collection already exists: {collection_name}")
        
        # Create Slack-specific vertex collections
        for collection_name in self.slack_vertex_collections:
            if not self.db.has_collection(collection_name):
                self.db.create_collection(collection_name)
                print(f"Created vertex collection: {collection_name}")
            else:
                print(f"Vertex collection already exists: {collection_name}")
        
        # Create WhatsApp-specific vertex collections
        for collection_name in self.whatsapp_vertex_collections:
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
    
    def create_indexes(self):
        """
        Create indexes for efficient querying.
        """
        # Index for work_contacts
        if self.db.has_collection("work_contacts"):
            collection = self.db.collection("work_contacts")
            
            # Create email index if not exists
            if not any(idx["fields"] == ["email"] for idx in collection.indexes()):
                collection.add_hash_index(fields=["email"], unique=True, sparse=True)
                print("Created hash index on work_contacts.email")
            else:
                print("Index on work_contacts.email already exists")
            
            # Create phone_number index if not exists
            if not any(idx["fields"] == ["phone_number"] for idx in collection.indexes()):
                collection.add_hash_index(fields=["phone_number"], unique=True, sparse=True)
                print("Created hash index on work_contacts.phone_number")
            else:
                print("Index on work_contacts.phone_number already exists")
        
        # Index for identifiers
        if self.db.has_collection("identifiers"):
            collection = self.db.collection("identifiers")
            
            # Create value index if not exists
            if not any(idx["fields"] == ["value"] for idx in collection.indexes()):
                collection.add_hash_index(fields=["value"], unique=True)
                print("Created hash index on identifiers.value")
            else:
                print("Index on identifiers.value already exists")
        
        # Index for analyzer_identifiers
        if self.db.has_collection("analyzer_identifiers"):
            collection = self.db.collection("analyzer_identifiers")
            
            # Create type index if not exists
            if not any(idx["fields"] == ["type"] for idx in collection.indexes()):
                collection.add_hash_index(fields=["type"])
                print("Created hash index on analyzer_identifiers.type")
            else:
                print("Index on analyzer_identifiers.type already exists")
        
        # Indexes for slack_messages
        if self.db.has_collection("slack_messages"):
            collection = self.db.collection("slack_messages")
            
            # Create timestamp index if not exists
            if not any(idx["fields"] == ["timestamp"] for idx in collection.indexes()):
                collection.add_skiplist_index(fields=["timestamp"])
                print("Created skiplist index on slack_messages.timestamp")
            else:
                print("Index on slack_messages.timestamp already exists")
            
            # Create channel index if not exists
            if not any(idx["fields"] == ["channel"] for idx in collection.indexes()):
                collection.add_hash_index(fields=["channel"])
                print("Created hash index on slack_messages.channel")
            else:
                print("Index on slack_messages.channel already exists")
        
        # Indexes for whatsapp_messages
        if self.db.has_collection("whatsapp_messages"):
            collection = self.db.collection("whatsapp_messages")
            
            # Create timestamp index if not exists
            if not any(idx["fields"] == ["timestamp"] for idx in collection.indexes()):
                collection.add_skiplist_index(fields=["timestamp"])
                print("Created skiplist index on whatsapp_messages.timestamp")
            else:
                print("Index on whatsapp_messages.timestamp already exists")
            
            # Create group_id index if not exists
            if not any(idx["fields"] == ["group_id"] for idx in collection.indexes()):
                collection.add_hash_index(fields=["group_id"], sparse=True)
                print("Created hash index on whatsapp_messages.group_id")
            else:
                print("Index on whatsapp_messages.group_id already exists")
        
        # Create indexes for analysis edge collections
        for edge_collection in ["slack_message_analysis", "whatsapp_message_analysis"]:
            if self.db.has_collection(edge_collection):
                collection = self.db.collection(edge_collection)
                
                # Create analysis_type index if not exists
                if not any(idx["fields"] == ["analysis_type"] for idx in collection.indexes()):
                    collection.add_hash_index(fields=["analysis_type"])
                    print(f"Created hash index on {edge_collection}.analysis_type")
                else:
                    print(f"Index on {edge_collection}.analysis_type already exists")
    
    def create_graphs(self):
        """
        Create the graph structures for Slack and WhatsApp if they don't exist.
        """
        # Create Slack graph
        slack_graph = None
        if not self.db.has_graph(self.slack_graph_name):
            slack_graph = self.db.create_graph(self.slack_graph_name)
            print(f"Created graph: {self.slack_graph_name}")
        else:
            print(f"Graph already exists: {self.slack_graph_name}")
            slack_graph = self.db.graph(self.slack_graph_name)
            
        # Add edge definitions to Slack graph
        for edge_definition in self.slack_edge_definitions:
            edge_collection = edge_definition["edge_collection"]
            from_collections = edge_definition["from_vertex_collections"]
            to_collections = edge_definition["to_vertex_collections"]
            
            # Check if edge definition already exists
            try:
                slack_graph.edge_collection(edge_collection)
                print(f"Edge definition for {edge_collection} already exists in {self.slack_graph_name}")
            except Exception:
                try:
                    # Create the edge definition
                    slack_graph.create_edge_definition(
                        edge_collection=edge_collection,
                        from_vertex_collections=from_collections,
                        to_vertex_collections=to_collections
                    )
                    print(f"Added edge definition for {edge_collection} to {self.slack_graph_name}")
                except Exception as e:
                    print(f"Error adding edge definition for {edge_collection}: {str(e)}")
                    if "duplicate edge collection" in str(e).lower():
                        print("Skipping duplicate edge collection error and continuing...")
                        continue
        
        # Create WhatsApp graph
        whatsapp_graph = None
        if not self.db.has_graph(self.whatsapp_graph_name):
            whatsapp_graph = self.db.create_graph(self.whatsapp_graph_name)
            print(f"Created graph: {self.whatsapp_graph_name}")
        else:
            print(f"Graph already exists: {self.whatsapp_graph_name}")
            whatsapp_graph = self.db.graph(self.whatsapp_graph_name)
            
        # Add edge definitions to WhatsApp graph
        for edge_definition in self.whatsapp_edge_definitions:
            edge_collection = edge_definition["edge_collection"]
            from_collections = edge_definition["from_vertex_collections"]
            to_collections = edge_definition["to_vertex_collections"]
            
            # Check if edge definition already exists
            try:
                whatsapp_graph.edge_collection(edge_collection)
                print(f"Edge definition for {edge_collection} already exists in {self.whatsapp_graph_name}")
            except Exception:
                try:
                    # Create the edge definition
                    whatsapp_graph.create_edge_definition(
                        edge_collection=edge_collection,
                        from_vertex_collections=from_collections,
                        to_vertex_collections=to_collections
                    )
                    print(f"Added edge definition for {edge_collection} to {self.whatsapp_graph_name}")
                except Exception as e:
                    print(f"Error adding edge definition for {edge_collection}: {str(e)}")
                    if "duplicate edge collection" in str(e).lower():
                        print("Skipping duplicate edge collection error and continuing...")
                        continue
    
    def run(self):
        """
        Run the full migration: connect to the database, create collections, 
        create indexes, and set up the graph structure.
        """
        try:
            # Step 1: Connect to the database
            self.connect_to_db()
            
            # Step 2: Create all collections
            self.create_collections()
            
            # Step 3: Create indexes
            self.create_indexes()
            
            # Step 4: Create graph structures
            self.create_graphs()
            
            print("Migration completed successfully!")
            return True
        
        except Exception as e:
            print(f"Error during migration: {str(e)}")
            traceback.print_exc()
            return False


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Set up messaging graph database structure")
    parser.add_argument("--host", default="http://localhost:8529", help="ArangoDB host URL")
    parser.add_argument("--db", default="my_database", help="Database name")
    parser.add_argument("--username", default="root", help="ArangoDB username")
    parser.add_argument("--password", default="zxcv", help="ArangoDB password")
    
    args = parser.parse_args()
    
    # Run the migration
    setup = MessagingGraphSetup(
        db_name=args.db,
        host=args.host,
        username=args.username,
        password=args.password
    )
    
    success = setup.run()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1) 