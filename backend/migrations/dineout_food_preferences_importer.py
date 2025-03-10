import os
import json
import re
from arango import ArangoClient
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor

class DineoutFoodPreferencesImporter:
    def __init__(self, db_name="my_database", host="http://localhost:8529",
                 username="root", password="zxcv"):

        current_dir = os.path.dirname(__file__)
        self.data_path = os.path.join(current_dir, "data", "dineout_and_food_preferences.json")
        self.db_name = db_name
        self.host = host
        self.username = username
        self.password = password

        # Define vertex collections for preferences.
        self.vertex_collections = ["dineout_keywords", "food_keywords"]

        # Containers for processed vertices.
        self.dineout_vertices = []
        self.food_vertices = []

        self.setup_db()

    @staticmethod
    def sanitize(text):
        """Sanitize text to create a document key (lowercase, underscores for spaces)."""
        text = text.strip().lower()
        text = re.sub(r"\s+", "_", text)
        allowed = set("abcdefghijklmnopqrstuvwxyz0123456789_-")
        sanitized = "".join(c for c in text if c in allowed)
        return sanitized if sanitized else "unnamed"

    def load_data(self):
        with open(self.data_path, "r") as f:
            self.data = json.load(f)
        print("Data loaded successfully.")

    def process_data(self):
        # Process dineout places preferences.
        dineout = self.data.get("dineout_places", {})
        for like in dineout.get("likes", []):
            key = self.sanitize(like)
            self.dineout_vertices.append({
                "_key": key,
                "keyword": like,
                "type": "like",
                "domain": "dineout"
            })
        for dislike in dineout.get("dislikes", []):
            key = self.sanitize(dislike)
            self.dineout_vertices.append({
                "_key": key,
                "keyword": dislike,
                "type": "dislike",
                "domain": "dineout"
            })

        # Process food preferences.
        food = self.data.get("food", {})
        for like in food.get("likes", []):
            key = self.sanitize(like)
            self.food_vertices.append({
                "_key": key,
                "keyword": like,
                "type": "like",
                "domain": "food"
            })
        for dislike in food.get("dislikes", []):
            key = self.sanitize(dislike)
            self.food_vertices.append({
                "_key": key,
                "keyword": dislike,
                "type": "dislike",
                "domain": "food"
            })

    def setup_db(self):
        """Establish connection and create database/graph if necessary."""
        client = ArangoClient(hosts=self.host)
        sys_db = client.db(username=self.username, password=self.password, verify=True)
        if not sys_db.has_database(self.db_name):
            sys_db.create_database(self.db_name)
            print(f"Database '{self.db_name}' created successfully.")
        else:
            print(f"Database '{self.db_name}' already exists.")
        self.db = client.db(self.db_name, username=self.username, password=self.password, verify=True)

        # Create vertex collections if they don't exist.
        for coll in self.vertex_collections:
            if not self.db.has_collection(coll):
                self.db.create_collection(coll)
                print(f"Collection '{coll}' created successfully.")
            else:
                print(f"Collection '{coll}' already exists.")

    def bulk_import(self, collection_name, docs, on_duplicate="update"):
        """Bulk import documents into a vertex collection."""
        collection = self.db.collection(collection_name)
        # Using insert_many with on_duplicate behavior.
        created = 0
        errors = 0
        for doc in docs:
            try:
                collection.insert(doc, overwrite=on_duplicate=="update")
                created += 1
            except Exception as e:
                errors += 1
        print(f"Imported {collection_name}: created {created} docs, errors {errors}")

    def bulk_import_all(self):
        """Bulk import all vertices."""
        print("Starting bulk import...")
        self.bulk_import("dineout_keywords", self.dineout_vertices)
        self.bulk_import("food_keywords", self.food_vertices)
        print("Bulk import completed successfully.")

    def run(self):
        """Execute the complete process."""
        self.load_data()
        self.process_data()
        self.bulk_import_all()

if __name__ == "__main__":
    current_dir = os.path.dirname(__file__)
    importer = DineoutFoodPreferencesImporter(
        db_name="user_12345", # user_id
        host="https://afc3138ddacc.arangodb.cloud",
        username="root",
        password="Jav9ZvTdowF3q66xXEiv"
    )
    importer.run()
