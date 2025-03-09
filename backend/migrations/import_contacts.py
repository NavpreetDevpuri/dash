"""
Migration script to import contacts from contacts.json file.
"""

import os
import sys
import json
import re
from arango import ArangoClient

# Add project root to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from app.db import get_system_db, get_user_db


class ContactsImporter:
    """Class to import contacts from contacts.json file."""
    
    def __init__(self, user_id, contacts_path, host="http://localhost:8529", 
                 username="root", password="zxcv"):
        """
        Initialize the ContactsImporter.
        
        Args:
            user_id: User ID to import data for
            contacts_path: Path to contacts.json file
            host: ArangoDB host URL
            username: ArangoDB username
            password: ArangoDB password
        """
        self.user_id = user_id
        self.contacts_path = contacts_path
        self.host = host
        self.username = username
        self.password = password
        
        # Collection names
        self.contacts_collection = "contacts"
        
        # Connect to DB
        self.setup_db()
    
    @staticmethod
    def sanitize(text):
        """
        Sanitize text to create a document key.
        Converts text to lowercase and replaces spaces with underscores.
        """
        text = text.strip().lower()
        text = re.sub(r"\s+", "_", text)
        allowed = set("abcdefghijklmnopqrstuvwxyz0123456789_-")
        sanitized = "".join(c for c in text if c in allowed)
        return sanitized if sanitized else "unnamed"
    
    def setup_db(self):
        """Connect to the user's database."""
        client = ArangoClient(hosts=self.host)
        sys_db = client.db("_system", username=self.username, password=self.password, verify=True)
        
        db_name = f"user_{self.user_id}"
        if not sys_db.has_database(db_name):
            raise Exception(f"Database '{db_name}' does not exist.")
        
        self.db = client.db(db_name, username=self.username, password=self.password, verify=True)
        print(f"Connected to database '{db_name}'.")
    
    def load_contacts(self):
        """Load contacts data from JSON file."""
        with open(self.contacts_path, "r") as f:
            self.contacts_data = json.load(f)
        
        print(f"Loaded contacts data from {self.contacts_path}.")
    
    def process_work_contacts(self):
        """Process work contacts from the loaded JSON data."""
        work_contacts = self.contacts_data.get("work_contacts", [])
        contacts_collection = self.db.collection(self.contacts_collection)
        
        print(f"Processing {len(work_contacts)} work contacts...")
        
        for contact in work_contacts:
            key = self.sanitize(contact["name"])
            doc = {
                "_key": key,
                "name": contact["name"],
                "email": contact.get("email", ""),
                "phone_number": contact.get("phone_number", ""),
                "date_of_birth": contact.get("date_of_birth", None),
                "marriage_anniversary": contact.get("marriage_anniversary", None),
                "relationship_type": "work",
                "role": contact.get("role", ""),
                "slack_email": contact.get("slack_email", ""),
                "slack_username": contact.get("slack_username", ""),
                "type": "contact"
            }
            
            # Insert contact
            try:
                contacts_collection.insert(doc, overwrite=True)
                print(f"Imported work contact: {contact['name']}")
            except Exception as e:
                print(f"Error importing work contact {contact['name']}: {e}")
    
    def process_personal_contacts(self):
        """Process personal contacts from the loaded JSON data."""
        personal_contacts = self.contacts_data.get("personal_contacts", [])
        contacts_collection = self.db.collection(self.contacts_collection)
        
        print(f"Processing {len(personal_contacts)} personal contacts...")
        
        for contact in personal_contacts:
            key = self.sanitize(contact["name"])
            doc = {
                "_key": key,
                "name": contact["name"],
                "email": contact.get("email", ""),
                "phone_number": contact.get("phone_number", ""),
                "date_of_birth": contact.get("date_of_birth", None),
                "marriage_anniversary": contact.get("marriage_anniversary", None),
                "relationship_type": "personal",
                "relationship": contact.get("relationship", ""),
                "whatsapp_number": contact.get("whatsapp_number", ""),
                "whatsapp_username": contact.get("whatsapp_username", ""),
                "type": "contact"
            }
            
            # Insert contact
            try:
                contacts_collection.insert(doc, overwrite=True)
                print(f"Imported personal contact: {contact['name']}")
            except Exception as e:
                print(f"Error importing personal contact {contact['name']}: {e}")
    
    def run(self):
        """Run the import process."""
        self.load_contacts()
        self.process_work_contacts()
        self.process_personal_contacts()
        print("Contacts import completed.")


if __name__ == "__main__":
    current_dir = os.path.dirname(__file__)
    user_id = "1270834"  # Use the same user_id as in other migrations
    
    importer = ContactsImporter(
        user_id=user_id,
        contacts_path=os.path.join(current_dir, "data", "contacts.json"),
        host="http://localhost:8529",
        username="root",
        password="zxcv"
    )
    
    importer.run() 