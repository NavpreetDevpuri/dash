import os
import sys
import logging
import datetime
from typing import Dict, Any, List

# Add the project root to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from app.db import get_system_db

class SlackCollectionsMigration:
    """
    Migration script to create the necessary collections for the Slack consumer agent.
    This creates document collections for slack messages and identifiers,
    as well as edge collections to connect them to contacts and each other.
    """
    def __init__(self):
        self.db = get_system_db()
        self.logger = logging.getLogger(__name__)
    
    def create_document_collections(self) -> None:
        """Create the required document collections if they don't exist."""
        collections = [
            {
                "name": "slack_messages",
                "description": "Collection for storing slack messages"
            },
            {
                "name": "identifiers",
                "description": "Collection for storing identifiers extracted from various sources"
            }
        ]
        
        for collection_info in collections:
            name = collection_info["name"]
            if not self.db.has_collection(name):
                self.db.create_collection(
                    name=name,
                    edge=False,
                    user_keys=True
                )
                self.logger.info(f"Created document collection: {name}")
                
                # Add creation timestamp in collection metadata if possible
                try:
                    meta = {
                        "created_at": str(datetime.datetime.utcnow()),
                        "description": collection_info.get("description", "")
                    }
                    self.db.collection(name).properties(meta)
                except Exception as e:
                    self.logger.warning(f"Failed to set metadata for {name}: {str(e)}")
            else:
                self.logger.info(f"Document collection already exists: {name}")
    
    def create_edge_collections(self) -> None:
        """Create the required edge collections if they don't exist."""
        edge_collections = [
            {
                "name": "contact_message",
                "description": "Edges connecting contacts to messages"
            },
            {
                "name": "identifier_message",
                "description": "Edges connecting identifiers to messages they were extracted from"
            }
        ]
        
        for edge_info in edge_collections:
            name = edge_info["name"]
            if not self.db.has_collection(name):
                self.db.create_collection(
                    name=name,
                    edge=True,
                    user_keys=True
                )
                self.logger.info(f"Created edge collection: {name}")
                
                # Add creation timestamp in collection metadata if possible
                try:
                    meta = {
                        "created_at": str(datetime.datetime.utcnow()),
                        "description": edge_info.get("description", "")
                    }
                    self.db.collection(name).properties(meta)
                except Exception as e:
                    self.logger.warning(f"Failed to set metadata for {name}: {str(e)}")
            else:
                self.logger.info(f"Edge collection already exists: {name}")
    
    def create_indexes(self) -> None:
        """Create useful indexes on the collections."""
        # Index on slack_messages for faster querying
        if self.db.has_collection("slack_messages"):
            messages = self.db.collection("slack_messages")
            
            # Index on channel field
            if not any(idx["fields"] == ["channel"] for idx in messages.indexes()):
                messages.add_hash_index(fields=["channel"], unique=False)
                self.logger.info("Created index on slack_messages.channel")
            
            # Index on sender field
            if not any(idx["fields"] == ["sender"] for idx in messages.indexes()):
                messages.add_hash_index(fields=["sender"], unique=False)
                self.logger.info("Created index on slack_messages.sender")
            
            # Index on timestamp for time-based queries
            if not any(idx["fields"] == ["timestamp"] for idx in messages.indexes()):
                messages.add_skiplist_index(fields=["timestamp"], unique=False)
                self.logger.info("Created index on slack_messages.timestamp")
        
        # Index on identifiers for faster lookups
        if self.db.has_collection("identifiers"):
            identifiers = self.db.collection("identifiers")
            
            # Index on value field
            if not any(idx["fields"] == ["value"] for idx in identifiers.indexes()):
                identifiers.add_hash_index(fields=["value"], unique=True)
                self.logger.info("Created unique index on identifiers.value")
    
    def update_user_collections_schema(self) -> None:
        """
        Update the schema for user collections to include slack and identifier collections.
        This ensures future users get these collections when their database is set up.
        """
        try:
            if self.db.has_collection("_system"):
                system_coll = self.db.collection("_system")
                
                # Get current schema if it exists
                cursor = self.db.aql.execute(
                    "FOR doc IN _system FILTER doc._key == 'user_collections_schema' RETURN doc"
                )
                schema_docs = list(cursor)
                
                if schema_docs:
                    # Update existing schema
                    schema = schema_docs[0]
                    collections = schema.get("collections", [])
                    
                    # Check if our collections are already in the schema
                    existing_names = [c["name"] for c in collections]
                    
                    # Add slack_messages if not already in schema
                    if "slack_messages" not in existing_names:
                        collections.append({
                            "name": "slack_messages",
                            "type": "document",
                            "description": "Slack messages for the user"
                        })
                    
                    # Add identifiers if not already in schema
                    if "identifiers" not in existing_names:
                        collections.append({
                            "name": "identifiers",
                            "type": "document",
                            "description": "Identifiers extracted from various sources"
                        })
                    
                    # Add edge collections if not already in schema
                    if "contact_message" not in existing_names:
                        collections.append({
                            "name": "contact_message",
                            "type": "edge",
                            "description": "Edges connecting contacts to messages"
                        })
                    
                    if "identifier_message" not in existing_names:
                        collections.append({
                            "name": "identifier_message",
                            "type": "edge",
                            "description": "Edges connecting identifiers to messages"
                        })
                    
                    # Update the schema document
                    schema["collections"] = collections
                    schema["updated_at"] = str(datetime.datetime.utcnow())
                    
                    system_coll.update(schema)
                    self.logger.info("Updated user collections schema")
                else:
                    # Create new schema
                    collections = [
                        # Existing collections from db.py setup_user_collections
                        {
                            "name": "dineout_keywords",
                            "type": "document",
                            "description": "Keywords related to dining out preferences"
                        },
                        {
                            "name": "food_keywords",
                            "type": "document",
                            "description": "Keywords related to food preferences"
                        },
                        {
                            "name": "personal_contacts",
                            "type": "document",
                            "description": "User's personal contacts"
                        },
                        {
                            "name": "work_contacts",
                            "type": "document",
                            "description": "User's work-related contacts"
                        },
                        # New collections for Slack integration
                        {
                            "name": "slack_messages",
                            "type": "document",
                            "description": "Slack messages for the user"
                        },
                        {
                            "name": "identifiers",
                            "type": "document",
                            "description": "Identifiers extracted from various sources"
                        },
                        {
                            "name": "contact_message",
                            "type": "edge",
                            "description": "Edges connecting contacts to messages"
                        },
                        {
                            "name": "identifier_message",
                            "type": "edge",
                            "description": "Edges connecting identifiers to messages"
                        }
                    ]
                    
                    system_coll.insert({
                        "_key": "user_collections_schema",
                        "collections": collections,
                        "created_at": str(datetime.datetime.utcnow()),
                        "updated_at": str(datetime.datetime.utcnow())
                    })
                    self.logger.info("Created user collections schema")
        except Exception as e:
            self.logger.error(f"Failed to update user collections schema: {str(e)}")
    
    def run(self) -> None:
        """Execute the migration process."""
        try:
            self.logger.info("Starting Slack collections migration")
            
            # Create document collections
            self.create_document_collections()
            
            # Create edge collections
            self.create_edge_collections()
            
            # Create indexes
            self.create_indexes()
            
            # Update user collections schema
            self.update_user_collections_schema()
            
            self.logger.info("Slack collections migration completed successfully")
        except Exception as e:
            self.logger.error(f"Migration failed: {str(e)}")
            raise

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s'
    )
    
    # Run the migration
    migration = SlackCollectionsMigration()
    migration.run() 