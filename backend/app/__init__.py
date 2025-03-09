from flask import Flask
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_socketio import SocketIO
from config import Config
import os
import logging
import traceback

bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'auth.signin'
login_manager.login_message_category = 'info'
socketio = SocketIO()

def initialize_database(db):
    """
    Initialize the database by creating all necessary collections.
    
    Args:
        db: The ArangoDB database connection
    """
    # List of collections to ensure exist
    collections = [
        'users',          # User information
        'chat_messages',  # Chat messages
        'threads',        # Conversation threads
        'entities',       # Entities from consumer agents
    ]
    
    # Create collections if they don't exist
    for collection_name in collections:
        try:
            if not db.has_collection(collection_name):
                db.create_collection(collection_name)
                print(f"Created collection '{collection_name}'")
            else:
                print(f"Collection '{collection_name}' already exists")
        except Exception as e:
            print(f"Error creating collection '{collection_name}': {str(e)}")

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    bcrypt.init_app(app)
    login_manager.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")

    # Setup database connections
    with app.app_context():
        # Initialize the database
        from app.db import init_app
        init_app(app)
        
        # Skip DB initialization during testing
        if not app.config.get('SKIP_DB_INIT', False):
            try:
                # Note about using migrations instead of setup_common_database
                print("Database setup: Using migrations from /migrations folder for database initialization.")
                print("Run migration scripts manually to set up your database.")
            except Exception as e:
                print(f"Error during app initialization: {e}")
                print("The application may still work, but some functionality may be limited.")

    # Register error handlers
    @app.errorhandler(500)
    def internal_error(error):
        error_traceback = traceback.format_exc()
        logging.error(f"500 Error: {str(error)}")
        logging.error(f"Traceback:\n{error_traceback}")
        return {"error": "Internal server error", "details": str(error)}, 500
    
    @app.errorhandler(404)
    def not_found_error(error):
        logging.error(f"404 Error: {str(error)}")
        return {"error": "Resource not found"}, 404

    # Register blueprints
    from app.routes.auth import auth as auth_blueprint
    
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    # Register Swagger documentation blueprint
    from app.swagger import register_swagger_routes
    register_swagger_routes(app)

    # Add a method to the socketio object to send notifications
    def send_notification(user_id, message, channel_type='system', importance='normal'):
        """
        Send a notification to a specific user via WebSocket.
        
        Args:
            user_id: The ID of the user to notify
            message: The notification message
            channel_type: The type of channel (email, slack, etc.)
            importance: The importance level (normal, high, low)
        """
        from datetime import datetime
        notification_data = {
            'message': message,
            'type': 'notification',
            'channel': channel_type,
            'importance': importance,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Emit to the user's room
        socketio.emit('notification', notification_data, room=str(user_id))
        
        print(f"Notification sent to user {user_id}: {message}")
    
    # Add the method to the socketio object
    socketio.send_notification = send_notification

    # Register SocketIO event handlers
    from app.socketio_events import register_socketio_events
    register_socketio_events(socketio)

    return app