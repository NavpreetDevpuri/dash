import os
import json
import re
from arango import ArangoClient
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

class RestaurantGraphImporter:
    def __init__(self,
                 db_name="my_database", host="http://localhost:8529",
                 username="root", password="zxcv"):
        
        current_dir = os.path.dirname(__file__)
        self.online_data_path = os.path.join(current_dir, "data/online_order_restaurants.json")
        self.dineout_data_path = os.path.join(current_dir, "data/dineout_restaurants.json")
        self.db_name = db_name
        self.host = host
        self.username = username
        self.password = password

        # Define orphan (vertex) collections.
        self.orphan_collections = [
            "restaurants", "dishes", "tags", "menus", "categories", "cuisines", "dineout_highlights"
        ]

        # Define edge collections.
        self.edge_definitions = [
            {
                "edge_collection": "restaurant_dish",
                "from_vertex_collections": ["restaurants"],
                "to_vertex_collections": ["dishes"],
            },
            {
                "edge_collection": "dish_menu",
                "from_vertex_collections": ["dishes"],
                "to_vertex_collections": ["menus"],
            },
            {
                "edge_collection": "dish_category",
                "from_vertex_collections": ["dishes"],
                "to_vertex_collections": ["categories"],
            },
            {
                "edge_collection": "dish_tag",
                "from_vertex_collections": ["dishes"],
                "to_vertex_collections": ["tags"],
            },
            {
                "edge_collection": "category_restaurant",
                "from_vertex_collections": ["categories"],
                "to_vertex_collections": ["restaurants"],
            },
            {
                "edge_collection": "menu_restaurant",
                "from_vertex_collections": ["menus"],
                "to_vertex_collections": ["restaurants"],
            },
            {
                "edge_collection": "restaurant_cuisine",
                "from_vertex_collections": ["restaurants"],
                "to_vertex_collections": ["cuisines"],
            },
            {
                "edge_collection": "restaurant_dineout_highlight",
                "from_vertex_collections": ["restaurants"],
                "to_vertex_collections": ["dineout_highlights"],
            },
        ]

        # Containers for processed vertices and edges.
        self.all_restaurant_docs = []
        self.all_menu_docs = []
        self.all_category_docs = []
        self.all_dish_docs = []
        self.all_tag_docs = {}   # Global tags.
        self.all_cuisine_docs = {}
        self.all_restaurant_dish_edges = []
        self.all_dish_menu_edges = []
        self.all_dish_category_edges = []
        self.all_dish_tag_edges = []
        self.all_menu_restaurant_edges = []
        self.all_category_restaurant_edges = []
        self.all_restaurant_cuisine_edges = []

        self.all_dineout_restaurant_docs = []
        self.all_dineout_cuisine_docs = {}
        self.all_dineout_restaurant_cuisine_edges = []
        self.all_dineout_highlight_docs = {}
        self.all_restaurant_dineout_highlight_edges = []

        self.online_data = None
        self.dineout_data = None

        self.global_tags_lock = Lock()
        self.setup_db()

    @staticmethod
    def sanitize(text):
        """Sanitize text for use as a document key."""
        text = str(text).strip()
        text = re.sub(r"\s+", "_", text)
        allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-." + "@()+,=;$!*'%:")
        sanitized = "".join(c for c in text if c in allowed)
        return sanitized if sanitized else "unnamed"

    @staticmethod
    def get_unique_key_local(name, existing):
        """Generate a unique key using a thread–local dictionary."""
        base = RestaurantGraphImporter.sanitize(name)
        if base in existing:
            existing[base] += 1
            return f"{base}_{existing[base]}"
        else:
            existing[base] = 0
            return base

    @staticmethod
    def deduplicate_edges(edge_list):
        """
        Deduplicate edges based on _from and _to.
        Also assign a deterministic _key for each edge.
        """
        seen = set()
        deduped = []
        for edge in edge_list:
            edge_key = RestaurantGraphImporter.sanitize(f"{edge['_from']}_{edge['_to']}")
            edge["_key"] = edge_key
            if edge_key not in seen:
                deduped.append(edge)
                seen.add(edge_key)
        return deduped

    def process_online_restaurant(self, restaurant, index):
        """Process an online restaurant record without any rating calculations."""
        r_key = self.sanitize(restaurant['name'])
        # Use ratings as-is from JSON
        restaurant_doc = {
            "_key": r_key,
            "name": restaurant["name"],
            "opening_hours": restaurant["opening_hours"],
            "ratings": restaurant.get("ratings", {}),
            "address": restaurant["address"],
            "contact": restaurant["contact"],
            "restaurant_images": restaurant["restaurant_images"],
            "is_dineout_available": False
        }

        # Process cuisines.
        cuisine_nodes = []
        restaurant_cuisine_edges = []
        cuisine_keys = set()
        if "cuisine_string" in restaurant:
            for cuisine in restaurant["cuisine_string"]:
                c_key = self.sanitize(cuisine)
                if c_key not in cuisine_keys:
                    cuisine_nodes.append({"_key": c_key, "name": cuisine})
                    cuisine_keys.add(c_key)
                restaurant_cuisine_edges.append({
                    "_from": f"restaurants/{r_key}",
                    "_to": f"cuisines/{c_key}"
                })

        # Process menus, categories, dishes, and tags.
        menus_docs = []
        menu_keys = set()
        categories_docs = []
        category_keys = set()
        dishes_docs = []
        tags_docs = {}
        restaurant_dish_edges = []
        dish_menu_edges = []
        dish_category_edges = []
        dish_tag_edges = []
        menu_restaurant_edges = []
        category_restaurant_edges = []
        local_dish_keys = {}

        if "menu" in restaurant and "menus" in restaurant["menu"]:
            for menu in restaurant["menu"]["menus"]:
                m_key = self.sanitize(menu['menu_name'])
                if m_key not in menu_keys:
                    menus_docs.append({"_key": m_key, "menu_name": menu["menu_name"]})
                    menu_keys.add(m_key)
                menu_restaurant_edges.append({
                    "_from": f"menus/{m_key}",
                    "_to": f"restaurants/{r_key}"
                })
                if "categories" in menu:
                    for category in menu["categories"]:
                        c_key_cat = self.sanitize(category['category_name'])
                        if c_key_cat not in category_keys:
                            categories_docs.append({
                                "_key": c_key_cat,
                                "category_name": category["category_name"]
                            })
                            category_keys.add(c_key_cat)
                        category_restaurant_edges.append({
                            "_from": f"categories/{c_key_cat}",
                            "_to": f"restaurants/{r_key}"
                        })
                        if "dishes" in category:
                            for dish in category["dishes"]:
                                d_key = self.get_unique_key_local(dish['name'], local_dish_keys)
                                # Use dish rating as provided in the JSON
                                dishes_docs.append({
                                    "_key": d_key,
                                    "name": dish["name"],
                                    "desc": dish.get("desc"),
                                    "rating": dish.get("rating", {}),
                                    "price": dish.get("price"),
                                    "item_image_filename": dish.get("item_image_filename"),
                                })
                                restaurant_dish_edges.append({
                                    "_from": f"restaurants/{r_key}",
                                    "_to": f"dishes/{d_key}"
                                })
                                dish_menu_edges.append({
                                    "_from": f"dishes/{d_key}",
                                    "_to": f"menus/{m_key}"
                                })
                                dish_category_edges.append({
                                    "_from": f"dishes/{d_key}",
                                    "_to": f"categories/{c_key_cat}"
                                })
                                if "tags" in dish:
                                    for tag in dish["tags"]:
                                        t_key = self.sanitize(tag)
                                        if t_key not in tags_docs:
                                            tags_docs[t_key] = {"_key": t_key, "name": tag}
                                        dish_tag_edges.append({
                                            "_from": f"dishes/{d_key}",
                                            "_to": f"tags/{t_key}"
                                        })

        return {
            "restaurant": restaurant_doc,
            "menus": menus_docs,
            "categories": categories_docs,
            "dishes": dishes_docs,
            "tags": tags_docs,
            "cuisines": cuisine_nodes,
            "restaurant_cuisine_edges": restaurant_cuisine_edges,
            "restaurant_dish_edges": restaurant_dish_edges,
            "dish_menu_edges": dish_menu_edges,
            "dish_category_edges": dish_category_edges,
            "dish_tag_edges": dish_tag_edges,
            "menu_restaurant_edges": menu_restaurant_edges,
            "category_restaurant_edges": category_restaurant_edges,
        }

    def process_dineout_restaurant(self, restaurant, index):
        """Process a dine-out restaurant record without any rating calculations."""
        r_key = self.sanitize(restaurant['name'])
        restaurant_doc = {
            "_key": r_key,
            "name": restaurant["name"],
            "knownFor": restaurant["knownFor"],
            "opening_hours": restaurant["opening_hours"],
            "ratings": restaurant.get("ratings", {}),
            "address": restaurant["address"],
            "contact": restaurant["contact"],
            "restaurant_images": restaurant["restaurant_images"],
            "is_fully_booked": restaurant.get("is_fully_booked", False),
            "people_liked": restaurant["people_liked"],
            "average_cost_for_two_details": restaurant["average_cost_for_two_details"],
            "is_dineout_available": True
        }

        # Process cuisines.
        cuisine_nodes = []
        restaurant_cuisine_edges = []
        cuisine_keys = set()
        if "cuisine_string" in restaurant:
            for cuisine in restaurant["cuisine_string"]:
                c_key = self.sanitize(cuisine)
                if c_key not in cuisine_keys:
                    cuisine_nodes.append({"_key": c_key, "name": cuisine})
                    cuisine_keys.add(c_key)
                restaurant_cuisine_edges.append({
                    "_from": f"restaurants/{r_key}",
                    "_to": f"cuisines/{c_key}"
                })

        # Process dineout highlights.
        dineout_highlight_nodes = []
        restaurant_dineout_highlight_edges = []
        for highlight in restaurant.get("dineout_highlights", []):
            key_candidate = self.sanitize(f"{highlight['type']}_{highlight['text']}")
            dineout_highlight_nodes.append({
                "_key": key_candidate,
                "type": highlight["type"],
                "text": highlight["text"]
            })
            restaurant_dineout_highlight_edges.append({
                "_from": f"restaurants/{r_key}",
                "_to": f"dineout_highlights/{key_candidate}"
            })

        return {
            "restaurant": restaurant_doc,
            "cuisines": cuisine_nodes,
            "restaurant_cuisine_edges": restaurant_cuisine_edges,
            "dineout_highlights": dineout_highlight_nodes,
            "restaurant_dineout_highlight_edges": restaurant_dineout_highlight_edges,
        }

    def setup_db(self):
        """Establish connection, create database/graph if necessary."""
        client = ArangoClient(hosts=self.host)
        sys_db = client.db("_system", username=self.username, password=self.password, verify=True)
        if not sys_db.has_database(self.db_name):
            sys_db.create_database(self.db_name)
            print(f"Database '{self.db_name}' created successfully.")
        else:
            print(f"Database '{self.db_name}' already exists.")
        self.db = client.db(self.db_name, username=self.username, password=self.password, verify=True)

        if not self.db.has_graph("restaurants"):
            self.graph = self.db.create_graph("restaurants",
                                              edge_definitions=self.edge_definitions,
                                              orphan_collections=self.orphan_collections)
            print("Graph 'restaurants' created successfully.")
        else:
            self.graph = self.db.graph("restaurants")
            print("Graph 'restaurants' already exists.")

    def load_data(self):
        """Load JSON data from the specified files."""
        with open(self.online_data_path, "r") as f:
            self.online_data = json.load(f)
        with open(self.dineout_data_path, "r") as f:
            self.dineout_data = json.load(f)
        print("Data loaded successfully.")

    def process_data(self):
        """Process both online and dineout data using ThreadPoolExecutor."""
        # Process online restaurants.
        with ThreadPoolExecutor() as executor:
            futures = []
            for idx, restaurant in enumerate(self.online_data):
                futures.append(executor.submit(self.process_online_restaurant, restaurant, idx))
            for future in tqdm(as_completed(futures), total=len(futures), desc="Processing online restaurants"):
                result = future.result()
                self.all_restaurant_docs.append(result["restaurant"])
                self.all_menu_docs.extend(result["menus"])
                self.all_category_docs.extend(result["categories"])
                self.all_dish_docs.extend(result["dishes"])
                for t_key, t_doc in result["tags"].items():
                    if t_key not in self.all_tag_docs:
                        self.all_tag_docs[t_key] = t_doc
                for cuisine in result["cuisines"]:
                    key = cuisine["_key"]
                    self.all_cuisine_docs[key] = cuisine
                self.all_restaurant_dish_edges.extend(result["restaurant_dish_edges"])
                self.all_dish_menu_edges.extend(result["dish_menu_edges"])
                self.all_dish_category_edges.extend(result["dish_category_edges"])
                self.all_dish_tag_edges.extend(result["dish_tag_edges"])
                self.all_menu_restaurant_edges.extend(result["menu_restaurant_edges"])
                self.all_category_restaurant_edges.extend(result["category_restaurant_edges"])
                self.all_restaurant_cuisine_edges.extend(result["restaurant_cuisine_edges"])

        # Process dineout restaurants.
        with ThreadPoolExecutor() as executor:
            futures = []
            for idx, restaurant in enumerate(self.dineout_data):
                futures.append(executor.submit(self.process_dineout_restaurant, restaurant, idx))
            for future in tqdm(as_completed(futures), total=len(futures), desc="Processing dineout restaurants"):
                result = future.result()
                self.all_dineout_restaurant_docs.append(result["restaurant"])
                for cuisine in result["cuisines"]:
                    key = cuisine["_key"]
                    self.all_dineout_cuisine_docs[key] = cuisine
                self.all_dineout_restaurant_cuisine_edges.extend(result["restaurant_cuisine_edges"])
                for dh in result["dineout_highlights"]:
                    key = dh["_key"]
                    self.all_dineout_highlight_docs[key] = dh
                self.all_restaurant_dineout_highlight_edges.extend(result["restaurant_dineout_highlight_edges"])

        # Merge cuisines from both sources.
        self.all_cuisine_docs.update(self.all_dineout_cuisine_docs)
        self.all_restaurant_cuisine_edges.extend(self.all_dineout_restaurant_cuisine_edges)

        # Merge restaurant vertices; dineout docs update the online ones if duplicates exist.
        self.all_restaurant_docs = self.all_restaurant_docs + self.all_dineout_restaurant_docs

    def bulk_import(self, collection_name, docs, on_duplicate=None):
        """
        Bulk import documents.
        For vertices, default on_duplicate is "update"; for edges, "ignore".
        """
        if collection_name in self.orphan_collections:
            if on_duplicate is None:
                on_duplicate = "update"
            result = self.graph.vertex_collection(collection_name).import_bulk(docs, on_duplicate=on_duplicate)
        else:
            if on_duplicate is None:
                on_duplicate = "ignore"
            result = self.graph.edge_collection(collection_name).import_bulk(docs, on_duplicate=on_duplicate)
        return (collection_name, result)

    def bulk_import_all(self):
        """Bulk import all vertices and edges."""
        print("Starting bulk import...")

        # Bulk import vertices.
        vertex_imports = {
            "restaurants": self.all_restaurant_docs,
            "menus": self.all_menu_docs,
            "categories": self.all_category_docs,
            "dishes": self.all_dish_docs,
            "tags": list(self.all_tag_docs.values()),
            "cuisines": list(self.all_cuisine_docs.values()),
            "dineout_highlights": list(self.all_dineout_highlight_docs.values()),
        }
        with ThreadPoolExecutor() as executor:
            vertex_futures = {executor.submit(self.bulk_import, coll, docs): coll
                              for coll, docs in vertex_imports.items()}
            for future in as_completed(vertex_futures):
                coll_name, result = future.result()
                created = result.get("created", 0)
                errors = result.get("errors", 0)
                print(f"Imported {coll_name}: {created} documents created, {errors} errors.")

        # Deduplicate and bulk import edges.
        edge_imports = {
            "restaurant_dish": self.deduplicate_edges(self.all_restaurant_dish_edges),
            "dish_menu": self.deduplicate_edges(self.all_dish_menu_edges),
            "dish_category": self.deduplicate_edges(self.all_dish_category_edges),
            "dish_tag": self.deduplicate_edges(self.all_dish_tag_edges),
            "category_restaurant": self.deduplicate_edges(self.all_category_restaurant_edges),
            "menu_restaurant": self.deduplicate_edges(self.all_menu_restaurant_edges),
            "restaurant_cuisine": self.deduplicate_edges(self.all_restaurant_cuisine_edges),
            "restaurant_dineout_highlight": self.deduplicate_edges(self.all_restaurant_dineout_highlight_edges),
        }
        with ThreadPoolExecutor() as executor:
            edge_futures = {executor.submit(self.bulk_import, coll, docs): coll
                            for coll, docs in edge_imports.items()}
            for future in as_completed(edge_futures):
                coll_name, result = future.result()
                created = result.get("created", 0)
                errors = result.get("errors", 0)
                print(f"Imported edges in {coll_name}: {created} documents created, {errors} errors.")

        print("Bulk import completed successfully.")

    def run(self):
        """Execute the complete process."""
        self.load_data()
        self.process_data()
        self.bulk_import_all()

if __name__ == "__main__":
    importer = RestaurantGraphImporter(
        db_name="common_db", 
        host="http://localhost:8529",
        username="root",
        password="zxcv"
    )
    importer.run()