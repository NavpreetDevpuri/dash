import time
from celery import Celery
from arango import ArangoClient

# ArangoDB Credentials
ARANGO_URL = "http://localhost:8529"
ARANGO_USER = "root"
ARANGO_PASSWORD = "zxcv"
ARANGO_DB_NAME = "celery_results"
ARANGO_COLLECTION_NAME = "celery_taskmeta"

# Initialize ArangoDB connection
client = ArangoClient()
sys_db = client.db("_system", username=ARANGO_USER, password=ARANGO_PASSWORD)

# Ensure the database exists
if not sys_db.has_database(ARANGO_DB_NAME):
    sys_db.create_database(ARANGO_DB_NAME)
    print(f"✅ Created database: {ARANGO_DB_NAME}")

# Connect to the newly created/existing database
db = client.db(ARANGO_DB_NAME, username=ARANGO_USER, password=ARANGO_PASSWORD)

# Ensure the collection exists
if not db.has_collection(ARANGO_COLLECTION_NAME):
    db.create_collection(ARANGO_COLLECTION_NAME)
    print(f"✅ Created collection: {ARANGO_COLLECTION_NAME}")

# Celery Configuration with ArangoDB authentication
app = Celery(
    "celery_arangodb",
    broker="redis://localhost:6379/0",  # Redis for task queue
    backend=f"arangodb://{ARANGO_USER}:{ARANGO_PASSWORD}@localhost:8529/{ARANGO_DB_NAME}/{ARANGO_COLLECTION_NAME}"  # ArangoDB as result backend
)

@app.task(name="tasks.add")
def add(x, y):
    """Simple task to add two numbers."""
    return x + y

@app.task(name="tasks.multiply")
def multiply(x):
    """Task that multiplies the result of add() by 2."""
    return x * 2

@app.task(name="tasks.notify")
def notify(message):
    """Task that prints a notification."""
    print(f"📢 Notification: {message}")

# celery -A celery_arangodb worker --loglevel=info