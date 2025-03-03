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