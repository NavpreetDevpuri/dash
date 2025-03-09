from arango import ArangoClient, Optional
from config import Config
from flask import g, session, current_app
import functools
import os
import datetime
import logging
import traceback
from flask_login import current_user
from arango.database import StandardDatabase

# Initialize the ArangoDB client
client = ArangoClient(hosts=Config.ARANGO_URL)

def get_system_db():
    """Get the system database connection with proper error handling"""
    try:
        # Connect to the system database with provided credentials
        sys_db = client.db(
            Config.ARANGO_DB_NAME, 
            username=Config.ARANGO_USERNAME, 
            password=Config.ARANGO_PASSWORD,
            verify=True
        )
        # Test connection
        sys_db.properties()
        return sys_db
    except Exception as e:
        logging.error(f"Database connection error: {str(e)}")
        logging.error(traceback.format_exc())
        logging.error(f"Check your ArangoDB credentials and make sure the server is running at {Config.ARANGO_URL}")
        # Re-raise to let the error handler deal with it
        raise

def get_user_db(user_id=None) -> Optional[StandardDatabase]:
    """
    Get the database connection for a user.
    
    Args:
        user_id: User ID (if not provided, uses current user)
        
    Returns:
        ArangoDB database connection for the user
    """

    # Get the database name for this user
    db_name = f"user_{user_id}"
    
    # Try to connect using the admin credentials
    try:
        # Connect to the _system database
        sys_db = get_system_db()

        # Check if the user database exists
        if not sys_db.has_database(db_name):
            logging.error(f"Database {db_name} does not exist")
            return None
            
        # Check if we have user-specific credentials in the user_databases collection
        if sys_db.has_collection('user_databases'):
            user_db_doc = None
            cursor = sys_db.aql.execute(
                "FOR doc IN user_databases FILTER doc.user_id == @user_id RETURN doc",
                bind_vars={"user_id": user_id}
            )
            user_db_docs = list(cursor)
            if user_db_docs:
                user_db_doc = user_db_docs[0]
                
            # If we have the credentials, connect using those
            if user_db_doc and 'username' in user_db_doc and 'password' in user_db_doc:
                try:
                    return client.db(
                        db_name,
                        username=user_db_doc['username'],
                        password=user_db_doc['password']
                    )
                except Exception as e:
                    logging.error(f"Error connecting with user credentials: {str(e)}")
        
        # Fall back to admin credentials
        return client.db(
            db_name,
            username=Config.ARANGO_USERNAME,
            password=Config.ARANGO_PASSWORD
        )
    except Exception as e:
        logging.error(f"Error connecting to user database: {str(e)}")
        return None

def close_db(e=None):
    """Close database connections."""
    # ArangoDB connections are handled automatically
    pass

def init_app(app):
    """
    Initialize the database with the given app.
    
    Args:
        app: Flask application
    """
    app.teardown_appcontext(close_db)
    
    # Log database connection information
    with app.app_context():
        try:
            # Test database connection on startup
            db = get_system_db()
            logging.info(f"Successfully connected to ArangoDB at {Config.ARANGO_URL}")
            logging.info(f"Using database: {Config.ARANGO_DB_NAME}")
            
            # Ensure system collections exist
            system_collections = ['users', 'user_databases']
            for collection_name in system_collections:
                if not db.has_collection(collection_name):
                    db.create_collection(collection_name)
                    logging.info(f"Created system collection: {collection_name}")
                else:
                    logging.info(f"System collection exists: {collection_name}")
        
        except Exception as e:
            logging.error(f"Failed to connect to database during initialization: {str(e)}")
            # Don't crash the app, but log the error for debugging

def setup_user_collections(db):
    """
    Set up the required collections for a user's personal database.
    
    Args:
        db: ArangoDB database connection
        
    Returns:
        bool: True if successful, False if error occurred
    """
    try:
        # Define the collections to create
        collections = [
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
            {
                "name": "slack_messages",
                "type": "document",
                "description": "Slack messages"
            },
            {
                "name": "identifiers",
                "type": "document",
                "description": "Identifiers extracted from any text content"
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
        
        # Create each collection if it doesn't exist
        for collection_info in collections:
            collection_name = collection_info["name"]
            if not db.has_collection(collection_name):
                db.create_collection(
                    name=collection_name,
                    edge=False,  # These are all document collections
                    user_keys=True  # Allow custom keys
                )
                current_app.logger.info(f"Created collection {collection_name}")
        
        # Create indexes if needed
        # For example, you might want to add indexes on common search fields
        if db.has_collection("personal_contacts"):
            contacts = db.collection("personal_contacts")
            # Add indexes for faster searching if they don't exist
            if not any(idx["fields"] == ["name"] for idx in contacts.indexes()):
                contacts.add_hash_index(fields=["name"], unique=False)
            if not any(idx["fields"] == ["email"] for idx in contacts.indexes()):
                contacts.add_hash_index(fields=["email"], unique=True)
        
        if db.has_collection("work_contacts"):
            contacts = db.collection("work_contacts")
            # Add indexes for faster searching if they don't exist
            if not any(idx["fields"] == ["name"] for idx in contacts.indexes()):
                contacts.add_hash_index(fields=["name"], unique=False)
            if not any(idx["fields"] == ["email"] for idx in contacts.indexes()):
                contacts.add_hash_index(fields=["email"], unique=True)

        return True
        
    except Exception as e:
        # Track the stack trace for better debugging
        import traceback
        stack_trace = traceback.format_exc()
        print(f"Stack trace:\n{stack_trace}")
        current_app.logger.error(f"Stack trace:\n{stack_trace}")
        current_app.logger.error(f"Error setting up user collections: {str(e)}")
        return False

def create_user_database(user_id, email, password):
    """
    Create a user-specific database and an ArangoDB user with access to that database.
    
    Args:
        user_id: User ID from the application
        email: Email address to use as ArangoDB username
        password: The hashed user password to use for ArangoDB authentication
        
    Returns:
        bool: True if successful, False if error occurred
    """
    try:
        # Connect to ArangoDB as root
        client = ArangoClient(hosts=Config.ARANGO_URL)
        sys_db = client.db('_system', username=Config.ARANGO_USERNAME, password=Config.ARANGO_PASSWORD)
        
        # Create user database name
        db_name = f"user_{user_id}"
        
        # Create the database if it doesn't exist
        if not sys_db.has_database(db_name):
            sys_db.create_database(
                name=db_name,
                users=[{
                    "username": email,
                    "password": password,
                    "active": True
                }]
            )
            
            # Create ArangoDB user if it doesn't exist
            if not sys_db.has_user(email):
                sys_db.create_user(
                    username=email,
                    password=password,
                    active=True
                )
                
            # Grant permissions to the user for their database
            sys_db.update_permission(
                username=email,
                permission='rw',
                database=db_name
            )
            
            # Set up the collections in the user database
            db = client.db(db_name, username=email, password=password)
            setup_user_collections(db)
            
            # Store the database info in _system.user_databases
            if not sys_db.has_collection('user_databases'):
                sys_db.create_collection('user_databases')
                
            sys_db.collection('user_databases').insert({
                "user_id": user_id,
                "db_name": db_name,
                "username": email,
                "password": password,  # Store the hashed user password
                "created_at": datetime.datetime.utcnow().isoformat()
            })
            
            return True
        return True
    except Exception as e:
        import traceback
        stack_trace = traceback.format_exc()
        print(f"Stack trace:\n{stack_trace}")
        current_app.logger.error(f"Error creating user database: {str(e)}")
        current_app.logger.error(f"Stack trace:\n{stack_trace}")
        return False