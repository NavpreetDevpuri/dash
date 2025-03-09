import datetime
from typing import Dict, Any, List, Optional, Union, Tuple
from arango import ArangoClient
from arango.database import StandardDatabase

class BaseGraphConsumer:
    """
    Base class for graph database consumers that provides common functionality
    for managing nodes and edges in an ArangoDB graph database.
    """
    
    def __init__(self):
        """
        Initialize the BaseGraphConsumer.
        """
        self.db = None
        self.graph = None
        
    def setup_graph(self, db: StandardDatabase, graph_name: str, edge_definitions: List[Dict[str, Any]], 
                   orphan_collections: List[str]) -> None:
        """
        Set up the graph in the provided database connection.
        
        Args:
            db: Database connection from get_user_db
            graph_name: Name of the graph
            edge_definitions: List of edge definitions for the graph
            orphan_collections: List of vertex collections not connected to edges
        """
        self.db = db
        
        # Create collections if they don't exist
        for edge_def in edge_definitions:
            # Create edge collection
            edge_collection = edge_def["edge_collection"]
            if not self.db.has_collection(edge_collection):
                self.db.create_collection(edge_collection, edge=True)
                print(f"Edge collection '{edge_collection}' created.")
            
            # Create vertex collections
            for collection in edge_def["from_vertex_collections"] + edge_def["to_vertex_collections"]:
                if not self.db.has_collection(collection):
                    self.db.create_collection(collection)
                    print(f"Vertex collection '{collection}' created.")
        
        # Create orphan collections if they don't exist
        for collection in orphan_collections:
            if not self.db.has_collection(collection):
                self.db.create_collection(collection)
                print(f"Orphan collection '{collection}' created.")
        
        # Create graph if it doesn't exist
        if not self.db.has_graph(graph_name):
            self.graph = self.db.create_graph(graph_name,
                                             edge_definitions=edge_definitions,
                                             orphan_collections=orphan_collections)
            print(f"Graph '{graph_name}' created successfully.")
        else:
            self.graph = self.db.graph(graph_name)
            print(f"Graph '{graph_name}' already exists.")
    def add_node(self, collection_name: str, data: Dict[str, Any], 
                unique_key: Optional[str] = None, unique_value: Optional[str] = None) -> str:
        """
        Add a node to a collection if it doesn't already exist.
        
        Args:
            collection_name: The name of the collection
            data: The data to store in the node
            unique_key: Optional key to check for uniqueness (e.g., 'email')
            unique_value: Optional value to check for uniqueness
            
        Returns:
            The ID of the node
        """
        # Ensure collection exists
        if not self.db.has_collection(collection_name):
            self.db.create_collection(collection_name)
            
        collection = self.db.collection(collection_name)
        
        # Add timestamp if not provided
        if "created_at" not in data:
            data["created_at"] = str(datetime.datetime.utcnow())
        
        # Perform upsert operation - update if exists, insert if not
        if unique_key and unique_value:
            # Check if document exists and update it, or insert if not found
            query = f"""
            UPSERT {{ {unique_key}: @value }}
            INSERT @data
            UPDATE @data
            IN {collection_name}
            RETURN NEW
            """
            cursor = self.db.aql.execute(
                query,
                bind_vars={"value": unique_value, "data": data}
            )
            result = next(cursor)
            return result["_id"]
        else:
            # No uniqueness check, just insert
            result = collection.insert(data)
            return result["_id"]
    
    def add_edge(self, edge_collection: str, from_id: str, to_id: str, 
                data: Optional[Dict[str, Any]] = None) -> str:
        """
        Add an edge between two nodes in the database.
        
        Args:
            edge_collection: The name of the edge collection
            from_id: The ID of the source node
            to_id: The ID of the target node
            data: Optional additional data for the edge
            
        Returns:
            The ID of the created edge
        """
        # Ensure edge collection exists
        if not self.db.has_collection(edge_collection):
            self.db.create_collection(edge_collection, edge=True)
            
        edges = self.db.collection(edge_collection)
        
        # Prepare edge data
        edge_data = data or {}
        edge_data.update({
            "_from": from_id,
            "_to": to_id,
            "created_at": str(datetime.datetime.utcnow())
        })
        
        # Create the edge
        result = edges.insert(edge_data)
        return result["_id"]
    
    def get_node_by_id(self, node_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a node by its ID.
        
        Args:
            node_id: The ID of the node
            
        Returns:
            The node data or None if not found
        """
        try:
            collection_name = node_id.split('/')[0]
            collection = self.db.collection(collection_name)
            return collection.get(node_id)
        except Exception:
            return None
    
    def query(self, aql_query: str, bind_vars: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute an AQL query.
        
        Args:
            aql_query: The AQL query to execute
            bind_vars: Optional variables to bind to the query
            
        Returns:
            List of query results
        """
        cursor = self.db.aql.execute(aql_query, bind_vars=bind_vars or {})
        return list(cursor)
    
    def bulk_import(self, collection_name: str, docs: List[Dict[str, Any]], 
                   on_duplicate: Optional[str] = None) -> Dict[str, Any]:
        """
        Bulk import documents into a collection.
        
        Args:
            collection_name: The name of the collection
            docs: List of documents to import
            on_duplicate: Action to take on duplicate documents
            
        Returns:
            Result of the bulk import
        """
        # Ensure collection exists
        if not self.db.has_collection(collection_name):
            self.db.create_collection(collection_name)
            
        collection = self.db.collection(collection_name)
        
        # Add timestamps if not provided
        for doc in docs:
            if "created_at" not in doc:
                doc["created_at"] = str(datetime.datetime.utcnow())
        
        # Import documents
        return collection.import_bulk(
            docs, 
            on_duplicate=on_duplicate or "error"
        )
    
    @staticmethod
    def deduplicate_edges(edge_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Deduplicate edges based on _from and _to fields.
        
        Args:
            edge_list: List of edge documents
            
        Returns:
            Deduplicated list of edge documents
        """
        seen = set()
        deduplicated = []
        
        for edge in edge_list:
            key = f"{edge['_from']}_{edge['_to']}"
            if key not in seen:
                seen.add(key)
                deduplicated.append(edge)
                
        return deduplicated 