"""
Migration script to import Email data including folders, messages, and identifiers.
"""

import os
import sys
import json
import datetime
from arango import ArangoClient

# Add project root to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from app.db import get_system_db, get_user_db


class EmailDataImporter:
    """Class to import Email data including folders, messages, and identifiers."""
    
    def __init__(self, db_name, host="https://afc3138ddacc.arangodb.cloud", 
                 username="root", password="Jav9ZvTdowF3q66xXEiv"):
        """
        Initialize the EmailDataImporter.
        
        Args:
            db_name: Database name to import data for
            contacts_path: Path to contacts.json file
            messages_path: Path to email_messages.json file
            host: ArangoDB host URL
            username: ArangoDB username
            password: ArangoDB password
        """
        self.db_name = db_name
        current_dir = os.path.dirname(__file__)
        self.contacts_path = os.path.join(current_dir, "data", "contacts.json")
        self.messages_path = os.path.join(current_dir, "data", "email_messages.json")
        self.host = host
        self.username = username
        self.password = password
        
        # Collection names
        self.CONTACTS_COLLECTION = "contacts"
        self.EMAIL_FOLDERS_COLLECTION = "email_folders"
        self.EMAIL_MESSAGES_COLLECTION = "email_messages"
        self.EMAIL_ATTACHMENTS_COLLECTION = "email_attachments"
        self.IDENTIFIERS_COLLECTION = "identifiers"
        
        # Edge collection names
        self.CONTACT_FOLDER_EDGE_COLLECTION = "contact__email_folder"
        self.IDENTIFIER_MESSAGE_EDGE_COLLECTION = "identifier__email_message"
        self.CONTACT_MESSAGE_EDGE_COLLECTION = "contact__email_message"
        self.FOLDER_MESSAGE_EDGE_COLLECTION = "folder__email_message"
        self.MESSAGE_ATTACHMENT_EDGE_COLLECTION = "email_message__attachment"
        
        # Default folders to create
        self.folders = [
            {"name": "Inbox", "description": "Default inbox folder"},
            {"name": "Sent", "description": "Sent emails folder"},
            {"name": "Drafts", "description": "Drafts folder"},
            {"name": "ProjectX", "description": "Project X emails folder"}
        ]
        
        # Connect to DB
        self.setup_db()
    
    def setup_db(self):
        """Connect to the user's database."""
        client = ArangoClient(hosts=self.host)
        sys_db = client.db("_system", username=self.username, password=self.password, verify=True)
        
        if not sys_db.has_database(self.db_name):
            raise Exception(f"Database '{self.db_name}' does not exist.")
        
        self.db = client.db(self.db_name, username=self.username, password=self.password, verify=True)
        print(f"Connected to database '{self.db_name}'.")
    
    def load_contacts(self):
        """Load contacts data from JSON file."""
        with open(self.contacts_path, "r") as f:
            contacts_data = json.load(f)
        
        # Get all work contacts with emails
        self.work_contacts = []
        for contact in contacts_data.get("work_contacts", []):
            if "email" in contact:
                self.work_contacts.append(contact)
        
        print(f"Loaded {len(self.work_contacts)} work contacts with email addresses.")
    
    def load_messages(self):
        """Load messages data from JSON file."""
        with open(self.messages_path, "r") as f:
            messages_data = json.load(f)
        
        self.messages = messages_data.get("messages", [])
        print(f"Loaded {len(self.messages)} email messages.")
    
    def create_folders(self):
        """Create email folders."""
        folders_collection = self.db.collection(self.EMAIL_FOLDERS_COLLECTION)
        
        for folder in self.folders:
            folder_key = folder["name"].lower().replace(" ", "_")
            
            # Check if folder already exists
            try:
                folders_collection.get(folder_key)
                print(f"Folder '{folder['name']}' already exists.")
                continue
            except:
                # Create folder
                folder_doc = {
                    "_key": folder_key,
                    "name": folder["name"],
                    "description": folder["description"],
                    "created_at": datetime.datetime.now().isoformat()
                }
                
                folders_collection.insert(folder_doc)
                print(f"Created folder '{folder['name']}'.")
    
    def find_contact_by_email(self, email):
        """Find a contact document by email address."""
        contacts = self.db.collection(self.CONTACTS_COLLECTION)
        cursor = contacts.find({"email": email})
        results = [doc for doc in cursor]
        
        if results:
            return results[0]
        return None
    
    def import_messages(self):
        """Import email messages and their identifiers."""
        messages_collection = self.db.collection(self.EMAIL_MESSAGES_COLLECTION)
        contact_edge = self.db.collection(self.CONTACT_MESSAGE_EDGE_COLLECTION)
        identifier_edge = self.db.collection(self.IDENTIFIER_MESSAGE_EDGE_COLLECTION)
        folder_edge = self.db.collection(self.FOLDER_MESSAGE_EDGE_COLLECTION)
        identifiers_collection = self.db.collection(self.IDENTIFIERS_COLLECTION)
        
        for i, email_data in enumerate(self.messages):
            from_email = email_data["from"]
            to_folder = email_data["to"]
            is_channel = email_data["is_channel"]
            subject = email_data["subject"]
            body = email_data["body"]
            recipients = email_data["recipients"]
            cc_emails = email_data.get("cc", [])
            timestamp = email_data["timestamp"]
            
            # Find sender contact
            sender = self.find_contact_by_email(from_email)
            if not sender:
                print(f"Warning: Could not find contact with email '{from_email}'")
                continue
            
            # Create message
            message_key = f"email_message_{i+1}"
            message = {
                "_key": message_key,
                "from": from_email,
                "to": to_folder,
                "is_channel": is_channel,
                "subject": subject,
                "body": body,
                "recipients": recipients,
                "cc": cc_emails,
                "timestamp": timestamp,
                "text": body  # Add text field for consistency with other message types
            }
            
            # Insert message
            try:
                messages_collection.insert(message)
                print(f"Created email message {message_key}.")
            except Exception as e:
                print(f"Error creating message: {e}")
                continue
            
            # Create edges
            try:
                # Sender Contact -> Message edge
                contact_edge.insert({
                    "_from": f"{self.CONTACTS_COLLECTION}/{sender['_key']}",
                    "_to": f"{self.EMAIL_MESSAGES_COLLECTION}/{message_key}",
                    "is_sender": True
                })
                
                # Folder -> Message edge (put in ProjectX folder)
                folder_edge.insert({
                    "_from": f"{self.EMAIL_FOLDERS_COLLECTION}/projectx",
                    "_to": f"{self.EMAIL_MESSAGES_COLLECTION}/{message_key}"
                })
                
                # Also put in Sent folder for the sender
                folder_edge.insert({
                    "_from": f"{self.EMAIL_FOLDERS_COLLECTION}/sent",
                    "_to": f"{self.EMAIL_MESSAGES_COLLECTION}/{message_key}"
                })
                
                # Process identifiers
                for identifier_data in email_data.get("identifiers", []):
                    identifier_value = identifier_data["value"]
                    identifier_key = identifier_data["key"]
                    
                    # Create or get identifier
                    try:
                        identifiers_collection.get(identifier_key)
                        print(f"Identifier '{identifier_value}' already exists.")
                    except:
                        # Create identifier with simplified structure
                        identifier = {
                            "_key": identifier_key,
                            "value": identifier_value,
                            "created_at": datetime.datetime.now().isoformat()
                        }
                        
                        identifiers_collection.insert(identifier)
                        print(f"Created identifier for '{identifier_value}'.")
                    
                    # Create edges between identifiers and messages
                    edge_data = {
                        "_from": f"{self.IDENTIFIERS_COLLECTION}/{identifier_key}",
                        "_to": f"{self.EMAIL_MESSAGES_COLLECTION}/{message_key}"
                    }
                    
                    # Determine relationship type based on the identifier value
                    if identifier_value == from_email:
                        edge_data["is_sender"] = True
                    elif identifier_value in recipients:
                        edge_data["is_recipient"] = True
                    elif identifier_value in cc_emails:
                        edge_data["is_cc"] = True
                    
                    identifier_edge.insert(edge_data)
                
                # Create edges for recipients
                for recipient_email in recipients:
                    recipient = self.find_contact_by_email(recipient_email)
                    if recipient:
                        # Recipient Contact -> Message edge
                        contact_edge.insert({
                            "_from": f"{self.CONTACTS_COLLECTION}/{recipient['_key']}",
                            "_to": f"{self.EMAIL_MESSAGES_COLLECTION}/{message_key}",
                            "is_recipient": True
                        })
                        
                        # Put in Inbox folder for recipients
                        folder_edge.insert({
                            "_from": f"{self.EMAIL_FOLDERS_COLLECTION}/inbox",
                            "_to": f"{self.EMAIL_MESSAGES_COLLECTION}/{message_key}"
                        })
                
                # Add CC recipients
                for cc_email in cc_emails:
                    cc_contact = self.find_contact_by_email(cc_email)
                    if cc_contact:
                        # CC Contact -> Message edge
                        contact_edge.insert({
                            "_from": f"{self.CONTACTS_COLLECTION}/{cc_contact['_key']}",
                            "_to": f"{self.EMAIL_MESSAGES_COLLECTION}/{message_key}",
                            "is_cc": True
                        })
                
            except Exception as e:
                print(f"Error creating edges for message {message_key}: {e}")
    
    def run(self):
        """Run the import process."""
        self.load_contacts()
        self.load_messages()
        self.create_folders()
        self.import_messages()
        print("Email data import completed.")


if __name__ == "__main__":
    db_name = "user_1270834"  # Use the same user_id as in other migrations
    
    importer = EmailDataImporter(
        db_name=db_name,
        host="https://afc3138ddacc.arangodb.cloud",
        username="root",
        password="Jav9ZvTdowF3q66xXEiv"
    )
    
    importer.run() 