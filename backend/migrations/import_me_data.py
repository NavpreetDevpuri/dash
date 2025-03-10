"""
Simple script to import personal information from me.json file.
If the data already exists in the database, it does nothing.
"""

import os
import json
from arango import ArangoClient


class ImportMeData:
    """Class to import personal information from me.json file."""
    
    def __init__(self, db_name="user_1270834", host="http://localhost:8529", 
                 username="root", password="zxcv"):
        """
        Initialize the ImportMeData.
        
        Args:
            db_name: Database name to import data for
            host: ArangoDB host URL
            username: ArangoDB username
            password: ArangoDB password
        """
        self.db_name = db_name
        self.host = host
        self.username = username
        self.password = password
        self.me_collection = "me"
        
        # Path to the me.json file
        current_dir = os.path.dirname(__file__)
        self.me_data_path = os.path.join(current_dir, "data", "me.json")
        
        # Connect to DB
        self.db = self.connect_to_db()
    
    def connect_to_db(self):
        """Connect to the user's database."""
        client = ArangoClient(hosts=self.host)
        db = client.db(self.db_name, username=self.username, password=self.password, verify=True)
        print(f"Connected to database '{self.db_name}'.")
        return db
    
    def create_collection_if_not_exists(self):
        """Create me collection if it doesn't exist."""
        if not self.db.has_collection(self.me_collection):
            self.db.create_collection(self.me_collection)
            print(f"Created collection '{self.me_collection}'.")
    
    def import_data(self):
        """Import data from me.json if it doesn't already exist."""
        self.create_collection_if_not_exists()
        
        # Check if me document already exists
        me_collection = self.db.collection(self.me_collection)
        if me_collection.has("me"):
            print("The 'me' document already exists. No action needed.")
            return
        
        # Load the me.json file
        with open(self.me_data_path, "r") as f:
            me_data = json.load(f)
        
        print(f"Loaded personal data from {self.me_data_path}.")
        
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
    
    def run(self):
        """Run the import process."""
        self.import_data()
        print("Import process completed.")


if __name__ == "__main__":
    importer = ImportMeData()
    importer.run() 