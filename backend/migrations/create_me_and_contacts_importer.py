import os
import json
import re
from arango import ArangoClient

class ContactsImporter:
    def __init__(self, data_path, me_path, db_name="my_database", host="http://localhost:8529",
                 username="root", password="zxcv"):
        self.data_path = data_path
        self.me_path = me_path
        self.db_name = db_name
        self.host = host
        self.username = username
        self.password = password

        # Define vertex collections for contacts and me.
        self.vertex_collections = ["work_contacts", "personal_contacts", "me"]
        
        # Define edge collections for relationships
        self.edge_collections = ["work_relationships", "personal_relationships"]

        # Containers for processed documents.
        self.work_contacts = []
        self.personal_contacts = []
        self.me_data = None
        self.work_relationships = []
        self.personal_relationships = []

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

    def load_data(self):
        """Load contacts data from JSON file."""
        with open(self.data_path, "r") as f:
            self.data = json.load(f)
        
        # Load me data
        with open(self.me_path, "r") as f:
            self.me_data = json.load(f)
            
        print("Data loaded successfully.")

    def process_data(self):
        """Process work and personal contacts from the loaded JSON data."""
        # Process me data
        me_key = "me"
        me_doc = {
            "_key": me_key,
            **self.me_data
        }
        
        # Process work contacts.
        for contact in self.data.get("work_contacts", []):
            key = self.sanitize(contact["Name"])
            doc = {
                "_key": key,
                "name": contact["Name"],
                "phone": contact["Phone Number"],
                "dob": contact["Date of Birth"],
                "marriage_anniversary": contact["Marriage Anniversary"],
                "email": contact["Email"],
                "role": contact["Role"]
            }
            self.work_contacts.append(doc)
            
            # Create work relationship edge
            relationship = {
                "_from": "me/me",
                "_to": f"work_contacts/{key}",
                "type": "work",
                "role": contact["Role"]
            }
            self.work_relationships.append(relationship)
        
        # Process personal contacts.
        for contact in self.data.get("personal_contacts", []):
            key = self.sanitize(contact["Name"])
            doc = {
                "_key": key,
                "name": contact["Name"],
                "phone": contact["Phone Number"],
                "dob": contact["Date of Birth"],
                "marriage_anniversary": contact["Marriage Anniversary"],
                "email": contact["Email"],
                "relationship": contact["Relationship"]
            }
            self.personal_contacts.append(doc)
            
            # Create personal relationship edge
            relationship = {
                "_from": "me/me",
                "_to": f"personal_contacts/{key}",
                "type": "personal",
                "relationship": contact["Relationship"]
            }
            self.personal_relationships.append(relationship)
            
        # Add me document
        self.db.collection("me").insert(me_doc, overwrite=True)
        print("Me document created successfully.")

    def setup_db(self):
        """Establish connection to ArangoDB and create the required collections if not present."""
        client = ArangoClient(hosts=self.host)
        sys_db = client.db("_system", username=self.username, password=self.password, verify=True)
        if not sys_db.has_database(self.db_name):
            sys_db.create_database(self.db_name)
            print(f"Database '{self.db_name}' created successfully.")
        else:
            print(f"Database '{self.db_name}' already exists.")
        self.db = client.db(self.db_name, username=self.username, password=self.password, verify=True)
        
        # Create vertex collections if they do not exist.
        for coll in self.vertex_collections:
            if not self.db.has_collection(coll):
                self.db.create_collection(coll)
                print(f"Collection '{coll}' created successfully.")
            else:
                print(f"Collection '{coll}' already exists.")
                
        # Create edge collections if they do not exist
        for coll in self.edge_collections:
            if not self.db.has_collection(coll):
                self.db.create_collection(coll, edge=True)
                print(f"Edge collection '{coll}' created successfully.")
            else:
                print(f"Edge collection '{coll}' already exists.")
                
        # Create graph if it doesn't exist
        if not self.db.has_graph("contacts_graph"):
            graph = self.db.create_graph("contacts_graph")
            
            # Define edge definitions
            graph.create_edge_definition(
                edge_collection="work_relationships",
                from_vertex_collections=["me"],
                to_vertex_collections=["work_contacts"]
            )
            
            graph.create_edge_definition(
                edge_collection="personal_relationships",
                from_vertex_collections=["me"],
                to_vertex_collections=["personal_contacts"]
            )
            
            print("Graph 'contacts_graph' created successfully.")
        else:
            print("Graph 'contacts_graph' already exists.")

    def bulk_import(self, collection_name, docs, on_duplicate="update"):
        """Bulk import documents into a specified vertex collection."""
        coll = self.db.collection(collection_name)
        created = 0
        errors = 0
        for doc in docs:
            try:
                # Using insert with overwrite enabled if on_duplicate is set to "update"
                coll.insert(doc, overwrite=(on_duplicate == "update"))
                created += 1
            except Exception as e:
                errors += 1
        print(f"Imported {collection_name}: created {created} docs, errors {errors}")

    def bulk_import_all(self):
        """Import all processed documents into their respective collections."""
        print("Starting bulk import...")
        self.bulk_import("work_contacts", self.work_contacts)
        self.bulk_import("personal_contacts", self.personal_contacts)
        self.bulk_import("work_relationships", self.work_relationships)
        self.bulk_import("personal_relationships", self.personal_relationships)
        print("Bulk import completed successfully.")

    def run(self):
        """Execute the complete process: load, process, and bulk import the contacts."""
        self.load_data()
        self.process_data()
        self.bulk_import_all()

if __name__ == "__main__":
    current_dir = os.path.dirname(__file__)
    importer = ContactsImporter(
        data_path=os.path.join(current_dir, "data", "contacts.json"),
        me_path=os.path.join(current_dir, "data", "me.json"),
        db_name="user_1235", # user_id
        host="http://localhost:8529",
        username="root",
        password="zxcv"
    )
    importer.run()