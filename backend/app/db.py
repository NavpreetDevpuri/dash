from arango import ArangoClient
from config import Config
from flask import g, session, current_app
import functools
import os
import datetime
import logging
import traceback
from flask_login import current_user

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

def get_db(user_id=None):
    """
    Get a database connection.
    
    Args:
        user_id: Optional user ID to get a user-specific database
        
    Returns:
        ArangoDB database connection
    """
    if not hasattr(g, 'arango_client'):
        g.arango_client = ArangoClient(hosts=Config.ARANGO_URL)
    
    # If user_id is provided, get user-specific database
    if user_id:
        return get_current_user_db(user_id)
    
    # If authenticated, use the current user's database
    if current_user and current_user.is_authenticated:
        return get_current_user_db(current_user.id)
    
    # Otherwise connect to system database with admin credentials
    if not hasattr(g, 'arango_system_db'):
        g.arango_system_db = g.arango_client.db(
            '_system', 
            username=Config.ARANGO_USERNAME, 
            password=Config.ARANGO_PASSWORD
        )
    return g.arango_system_db

def get_current_user_db(user_id=None):
    """
    Get the current user's database connection.
    
    Args:
        user_id: User ID (if not provided, uses current user)
        
    Returns:
        ArangoDB database connection for the user
    """
    if not user_id:
        # If no user_id is provided but we're authenticated, try to get from current_user
        if current_user and current_user.is_authenticated:
            user_id = current_user.id
        else:
            # No user ID available
            current_app.logger.warning("No user ID provided or available in context")
            return None
    
    # Initialize ArangoDB client if needed
    if not hasattr(g, 'arango_client'):
        g.arango_client = ArangoClient(hosts=Config.ARANGO_URL)
    
    # Get the database name for this user
    db_name = f"user_{user_id}"
    
    # Try to connect using the admin credentials
    try:
        # Connect to the _system database
        sys_db = g.arango_client.db(
            '_system', 
            username=Config.ARANGO_USERNAME, 
            password=Config.ARANGO_PASSWORD
        )
        
        # Check if the user database exists
        if not sys_db.has_database(db_name):
            current_app.logger.error(f"Database {db_name} does not exist")
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
                    return g.arango_client.db(
                        db_name,
                        username=user_db_doc['username'],
                        password=user_db_doc['password']  # Use the stored hashed password
                    )
                except Exception as e:
                    current_app.logger.error(f"Error connecting with user credentials: {str(e)}")
        
        # Fall back to admin credentials
        return g.arango_client.db(
            db_name,
            username=Config.ARANGO_USERNAME,
            password=Config.ARANGO_PASSWORD
        )
    except Exception as e:
        current_app.logger.error(f"Error connecting to user database: {str(e)}")
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
        
        # Add metadata to indicate collections are set up
        try:
            if not db.has_collection("_system"):
                db.create_collection("_system")
            
            system = db.collection("_system")
            system.insert({
                "_key": "collections_setup",
                "status": "complete",
                "collections": [c["name"] for c in collections],
                "timestamp": datetime.datetime.utcnow().isoformat()
            }, overwrite=True)
        except Exception as e:
            current_app.logger.warning(f"Could not create metadata: {str(e)}")
        
        return True
        
    except Exception as e:
        current_app.logger.error(f"Error setting up user collections: {str(e)}")
        return False

def create_user_database(user_id, username, password):
    """
    Create a user-specific database and an ArangoDB user with access to that database.
    
    Args:
        user_id: User ID from the application
        username: Username for the ArangoDB user
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
                    "username": username,
                    "password": password,
                    "active": True
                }]
            )
            
            # Create ArangoDB user if it doesn't exist
            if not sys_db.has_user(username):
                sys_db.create_user(
                    username=username,
                    password=password,
                    active=True
                )
                
            # Grant permissions to the user for their database
            sys_db.update_permission(
                username=username,
                permission='rw',
                database=db_name
            )
            
            # Set up the collections in the user database
            db = client.db(db_name, username=username, password=password)
            setup_user_collections(db)
            
            # Store the database info in _system.user_databases
            if not sys_db.has_collection('user_databases'):
                sys_db.create_collection('user_databases')
                
            sys_db.collection('user_databases').insert({
                "user_id": user_id,
                "db_name": db_name,
                "username": username,
                "password": password,  # Store the hashed user password
                "created_at": datetime.datetime.utcnow().isoformat()
            })
            
            return True
        return False
    except Exception as e:
        current_app.logger.error(f"Error creating user database: {str(e)}")
        return False