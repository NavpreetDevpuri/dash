"""
Simple script to import personal information from me.json file.
If the data already exists in the database, it does nothing.
"""

import os
import json
from arango import ArangoClient

# Database connection settings
DB_NAME = "user_1270834"
HOST = "http://localhost:8529"
USERNAME = "root"
PASSWORD = "zxcv"
ME_COLLECTION = "me"

# Connect to the database
client = ArangoClient(hosts=HOST)
db = client.db(DB_NAME, username=USERNAME, password=PASSWORD, verify=True)
print(f"Connected to database '{DB_NAME}'.")

# Create me collection if it doesn't exist
if not db.has_collection(ME_COLLECTION):
    db.create_collection(ME_COLLECTION)
    print(f"Created collection '{ME_COLLECTION}'.")

# Check if me document already exists
me_collection = db.collection(ME_COLLECTION)
if me_collection.has("me"):
    print("The 'me' document already exists. No action needed.")
else:
    # Load the me.json file
    current_dir = os.path.dirname(__file__)
    me_data_path = os.path.join(current_dir, "data", "me.json")
    
    with open(me_data_path, "r") as f:
        me_data = json.load(f)
    
    print(f"Loaded personal data from {me_data_path}.")
    
    # Prepare document
    doc = {
        "_key": "me",
        **me_data  # Import all fields directly from the JSON
    }
    
    # Import the data
    try:
        me_collection.insert(doc)
        print("Successfully imported personal information.")
    except Exception as e:
        print(f"Error importing personal information: {e}")

print("Import process completed.") 