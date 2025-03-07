from flask import Flask
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_socketio import SocketIO
from config import Config

bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'auth.signin'
login_manager.login_message_category = 'info'
socketio = SocketIO()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    bcrypt.init_app(app)
    login_manager.init_app(app)
    socketio.init_app(app)

    # Register Blueprints
    from app.routes.auth import auth
    from app.routes.chat import chat
    app.register_blueprint(auth)
    app.register_blueprint(chat)

    # Initialize ArangoDB collections if they don't exist
    from app.db import get_db
    db = get_db()
    if not db.has_collection('users'):
        db.create_collection('users')
    if not db.has_collection('chat_messages'):
        db.create_collection('chat_messages')
    if not db.has_collection('threads'):
        db.create_collection('threads')

    # Register SocketIO event handlers
    from app.socketio_events import register_socketio_events
    register_socketio_events(socketio)

    return app