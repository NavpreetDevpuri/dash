from flask_login import UserMixin
from app.db import get_system_db, get_user_db
from datetime import datetime
import logging
import traceback

### User model with updated create method for user database
class User(UserMixin):
    def __init__(self, doc):
        self.doc = doc
        self.id = doc['_key']  # Flask-Login uses this as the unique user ID.
        self.full_name = doc.get('full_name')
        self.email = doc.get('email')
        self.password = doc.get('password')
        self.is_admin = doc.get('is_admin', False)

    def to_dict(self):
        return {
            'id': self.id,
            'full_name': self.full_name,
            'email': self.email,
            'is_admin': self.is_admin
        }

    @staticmethod
    def create(email, password_hash, full_name=None, is_admin=False):
        try:
            # Use the common database to store users
            db = get_system_db()
            user_doc = {
                'email': email,
                'password': password_hash,
                'full_name': full_name,
                'is_admin': is_admin,
                'created_at': datetime.utcnow().isoformat()
            }
            
            # Store user document in user_databases collection
            result = db.collection('user_databases').insert(user_doc)
            user_doc['_key'] = result['_key']
            
            # Get user ID from inserted document
            user_id = result['_key']
            
            # Create a user-specific database - import here to avoid circular imports
            from app.db import create_user_database
            if create_user_database(user_id, email, password_hash):
                logging.info(f"Created user-specific database for user {user_id}")
            else:
                logging.error(f"Failed to create user-specific database for user {user_id}")
            
            return User(user_doc)
            
        except Exception as e:
            logging.error(f"Error creating user: {str(e)}")
            logging.error(traceback.format_exc())
            raise

    @classmethod
    def find_by_email(cls, email):
        """Find a user by email."""
        try:
            db = get_system_db()
            query = "FOR u IN user_databases FILTER u.email == @email RETURN u"
            cursor = db.aql.execute(query, bind_vars={'email': email})
            user_docs = list(cursor)
            if user_docs:
                return cls(user_docs[0])
            return None
        except Exception as e:
            logging.error(f"Error finding user by email: {str(e)}")
            return None

    @staticmethod
    def get(user_id):
        try:
            db = get_system_db()
            if db.collection('user_databases').has(user_id):
                doc = db.collection('user_databases').get(user_id)
                return User(doc)
            return None
        except Exception as e:
            logging.error(f"Error getting user by ID: {str(e)}")
            return None

### New: ConversationThread model
class ConversationThread:
    def __init__(self, doc):
        self.doc = doc
        self.id = doc['_key']
        self.user_id = doc.get('creator_id')  # For compatibility with existing code
        self.title = doc.get('title')
        self.created_at = doc.get('created_at')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'created_at': self.created_at
        }

    @staticmethod
    def create(title, user_id, created_at=None):
        db = get_system_db()
        if created_at is None:
            created_at = datetime.utcnow().isoformat()
        thread_doc = {
            'creator_id': user_id,
            'title': title,
            'created_at': created_at
        }
        result = db.collection('threads').insert(thread_doc)
        thread_doc['_key'] = result['_key']
        return ConversationThread(thread_doc)

    @staticmethod
    def get_by_id(thread_id):
        db = get_system_db()
        if db.collection('threads').has(thread_id):
            doc = db.collection('threads').get(thread_id)
            return ConversationThread(doc)
        return None

    @staticmethod
    def get_threads_for_user(user_id):
        db = get_system_db()
        query = "FOR t IN threads FILTER t.creator_id == @user_id SORT t.created_at DESC RETURN t"
        cursor = db.aql.execute(query, bind_vars={'user_id': user_id})
        return [ConversationThread(doc) for doc in cursor]

### Update: ChatMessage now includes thread_id
class ChatMessage:
    def __init__(self, doc):
        self.doc = doc
        self.id = doc['_key']
        self.thread_id = doc.get('thread_id')
        self.sender_id = doc.get('user_id')  # For compatibility with frontend
        self.message_type = doc.get('message_type')
        self.content = doc.get('content')
        self.timestamp = doc.get('timestamp')
        if isinstance(self.timestamp, str):
            try:
                self.timestamp = datetime.fromisoformat(self.timestamp)
            except ValueError:
                self.timestamp = datetime.utcnow()

    def to_dict(self):
        return {
            'id': self.id,
            'thread_id': self.thread_id,
            'sender_id': self.sender_id,
            'message_type': self.message_type,
            'content': self.content,
            'timestamp': self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else self.timestamp
        }

    @staticmethod
    def create(thread_id, sender_id=None, content="", message_type="text", timestamp=None):
        db = get_system_db()
        if timestamp is None:
            timestamp = datetime.utcnow().isoformat()
        chat_doc = {
            'thread_id': thread_id,
            'user_id': sender_id,  # Store as user_id for compatibility
            'message_type': message_type,
            'content': content,
            'timestamp': timestamp
        }
        result = db.collection('chat_messages').insert(chat_doc)
        chat_doc['_key'] = result['_key']
        return ChatMessage(chat_doc)

    @staticmethod
    def get_messages_for_thread(thread_id):
        db = get_system_db()
        query = "FOR m IN chat_messages FILTER m.thread_id == @thread_id SORT m.timestamp ASC RETURN m"
        cursor = db.aql.execute(query, bind_vars={'thread_id': thread_id})
        return [ChatMessage(doc) for doc in cursor]

# Flask-Login user loader
from app import login_manager

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)