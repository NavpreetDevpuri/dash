"""
Base class for setting up graph schemas in ArangoDB.
This provides a reusable framework for defining and creating graph schemas.
"""

import os
import sys
from arango import ArangoClient

class GraphSchemaBase:
    """Base utility class to set up graph schemas in ArangoDB."""
    
    def __init__(self, graph_name, vertex_collections=None, edge_definitions=None):
        """
        Initialize the GraphSchemaBase.
        
        Args:
            graph_name: Name of the graph to create
            vertex_collections: Dictionary mapping collection names to their attributes 
                                (or None if no special attributes)
            edge_definitions: List of edge definitions following ArangoDB format
        """
        self.db = None
        self.graph = None
        self.graph_name = graph_name
        
        # Store collections and indices
        self.vertex_collections = vertex_collections or {}
        self.edge_definitions = edge_definitions or []
        
        # Extract all vertex collection names for convenience
        self.orphan_collections = list(self.vertex_collections.keys())
        
        # Store indices to be created
        self.indices = {}
    
    def add_index(self, collection_name, field, index_type="hash", unique=False):
        """
        Add an index to be created during setup.
        
        Args:
            collection_name: Name of the collection to add index to
            field: Field to index
            index_type: Type of index (hash, skiplist, etc.)
            unique: Whether the index should enforce uniqueness
        """
        if collection_name not in self.indices:
            self.indices[collection_name] = []
            
        self.indices[collection_name].append({
            "field": field,
            "type": index_type,
            "unique": unique
        })
    
    def setup_db(self, db_name: str, host: str, username: str, password: str):
        """
        Connect to the user's database and set up the graph.
        
        Args:
            host: Host to connect to
            username: Username to connect with
            password: Password to connect with
        """
        self.db = ArangoClient(database=db_name, host=host, username=username, password=password)
        if not self.db:
            raise Exception(f"Failed to connect to database")

        if not self.db.has_graph(self.graph_name):
            self.graph = self.db.create_graph(
                self.graph_name,
                edge_definitions=self.edge_definitions,
                orphan_collections=self.orphan_collections
            )
            print(f"Graph '{self.graph_name}' created successfully.")
        else:
            self.graph = self.db.graph(self.graph_name)
            print(f"Graph '{self.graph_name}' already exists.")
            
            # Update existing graph with any new edge definitions or collections
            for edge_def in self.edge_definitions:
                edge_collection = edge_def["edge_collection"]
                if not self.graph.has_edge_definition(edge_collection):
                    self.graph.create_edge_definition(
                        edge_collection=edge_collection,
                        from_vertex_collections=edge_def["from_vertex_collections"],
                        to_vertex_collections=edge_def["to_vertex_collections"]
                    )
                    print(f"Added new edge definition: {edge_collection}")
            
            # Ensure all orphan collections exist
            for collection in self.orphan_collections:
                if not self.db.has_collection(collection):
                    self.db.create_collection(collection)
                    self.graph.add_vertex_collection(collection)
                    print(f"Added new vertex collection: {collection}")
    
    def create_indices(self):
        """Create indices on collections for faster queries."""
        for collection_name, indices in self.indices.items():
            if self.db.has_collection(collection_name):
                collection = self.db.collection(collection_name)
                for idx in indices:
                    field = idx["field"]
                    unique = idx["unique"]
                    idx_type = idx["type"]
                    
                    # Check if index already exists
                    if not any(existing_idx["fields"] == [field] for existing_idx in collection.indexes()):
                        if idx_type == "hash":
                            collection.add_hash_index(fields=[field], unique=unique)
                        elif idx_type == "skiplist":
                            collection.add_skiplist_index(fields=[field], unique=unique)
                        # Add other index types as needed
                        
                        print(f"Added {idx_type} index on {collection_name}.{field}")
    
    def run(self, host: str, username: str, password: str):
        """
        Set up the database and graph schema for a specific user.
        
        Args:
            host: Host to connect to
            username: Username to connect with
            password: Password to connect with
        """
        self.setup_db(host, username, password)
        self.create_indices()
        print(f"{self.graph_name} graph schema setup complete.") 