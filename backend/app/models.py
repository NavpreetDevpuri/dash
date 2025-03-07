from flask_login import UserMixin
from app.db import get_db
from datetime import datetime

### User model remains unchanged
class User(UserMixin):
    def __init__(self, doc):
        self.doc = doc
        self.id = doc['_key']  # Flask-Login uses this as the unique user ID.
        self.username = doc.get('username')
        self.email = doc.get('email')
        self.password = doc.get('password')

    @staticmethod
    def create(username, email, password_hash):
        db = get_db()
        user_doc = {
            'username': username,
            'email': email,
            'password': password_hash
        }
        result = db.collection('users').insert(user_doc)
        user_doc['_key'] = result['_key']
        return User(user_doc)

    @staticmethod
    def find_by_email(email):
        db = get_db()
        query = "FOR u IN users FILTER u.email == @email RETURN u"
        cursor = db.aql.execute(query, bind_vars={'email': email})
        docs = list(cursor)
        if docs:
            return User(docs[0])
        return None

    @staticmethod
    def get(user_id):
        db = get_db()
        if db.collection('users').has(user_id):
            doc = db.collection('users').get(user_id)
            return User(doc)
        return None

### New: ConversationThread model
class ConversationThread:
    def __init__(self, doc):
        self.doc = doc
        self.id = doc['_key']
        self.creator_id = doc.get('creator_id')
        self.title = doc.get('title')
        self.created_at = doc.get('created_at')

    @staticmethod
    def create(creator_id, title, created_at=None):
        db = get_db()
        if created_at is None:
            created_at = datetime.utcnow().isoformat()
        thread_doc = {
            'creator_id': creator_id,
            'title': title,
            'created_at': created_at
        }
        result = db.collection('threads').insert(thread_doc)
        thread_doc['_key'] = result['_key']
        return ConversationThread(thread_doc)

    @staticmethod
    def get(thread_id):
        db = get_db()
        if db.collection('threads').has(thread_id):
            doc = db.collection('threads').get(thread_id)
            return ConversationThread(doc)
        return None

### Update: ChatMessage now includes thread_id
class ChatMessage:
    def __init__(self, doc):
        self.doc = doc
        self.id = doc['_key']
        self.thread_id = doc.get('thread_id')
        self.user_id = doc.get('user_id')
        self.message_type = doc.get('message_type')
        self.content = doc.get('content')
        self.timestamp = doc.get('timestamp')

    @staticmethod
    def create(thread_id, user_id, message_type, content, timestamp=None):
        db = get_db()
        if timestamp is None:
            timestamp = datetime.utcnow().isoformat()
        chat_doc = {
            'thread_id': thread_id,
            'user_id': user_id,
            'message_type': message_type,
            'content': content,
            'timestamp': timestamp
        }
        result = db.collection('chat_messages').insert(chat_doc)
        chat_doc['_key'] = result['_key']
        return ChatMessage(chat_doc)

# Flask-Login user loader
from app import login_manager

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)