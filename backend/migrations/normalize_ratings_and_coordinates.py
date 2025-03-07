import json
import os

def update_restaurant_ratings(ratings_obj):
    """
    Update ratings to include 'popularity' = rating * reviewCount.
    Treat missing or null values as 0.
    """
    for key in ["dining", "delivery"]:
        if key in ratings_obj:
            r_val = ratings_obj[key].get("rating", 0) or 0  # Ensure None is converted to 0
            review_count = ratings_obj[key].get("reviewCount", 0) or 0
            ratings_obj[key]["popularity"] = float(r_val) * float(review_count)
    return ratings_obj

def update_dish_rating(dish_rating):
    """
    Update dish rating by computing 'popularity' = rating * votes.
    Treat missing or null values as 0.
    """
    if isinstance(dish_rating, dict):
        rating_value = dish_rating.get("rating", 0) or 0
        votes = dish_rating.get("votes", 0) or 0
        dish_rating["popularity"] = float(rating_value) * float(votes)
    return dish_rating

def convert_lat_long(address):
    """
    Convert latitude and longitude fields in the address to float.
    If missing or invalid, set to 0.
    """
    if isinstance(address, dict):
        try:
            address["latitude"] = float(address.get("latitude", 0) or 0)
        except ValueError:
            address["latitude"] = 0
        try:
            address["longitude"] = float(address.get("longitude", 0) or 0)
        except ValueError:
            address["longitude"] = 0
    return address

def update_json_file(json_path):
    """
    Load the JSON file, update its contents, and write back the updated data.
    """
    with open(json_path, "r") as file:
        data = json.load(file)

    for restaurant in data:
        # Update restaurant ratings for popularity
        if "ratings" in restaurant:
            restaurant["ratings"] = update_restaurant_ratings(restaurant["ratings"])

        # Convert latitude and longitude to float (or set to 0)
        if "address" in restaurant:
            restaurant["address"] = convert_lat_long(restaurant["address"])

        # Update menu dishes
        if "menu" in restaurant and "menus" in restaurant["menu"]:
            for menu in restaurant["menu"]["menus"]:
                if "categories" in menu:
                    for category in menu["categories"]:
                        if "dishes" in category:
                            for dish in category["dishes"]:
                                if "rating" in dish:
                                    dish["rating"] = update_dish_rating(dish["rating"])

    # Write updated JSON back to the file
    updated_json_path = json_path.replace(".json", "_updated.json")
    with open(updated_json_path, "w") as file:
        json.dump(data, file, indent=4)

    print(f"Updated JSON saved to: {updated_json_path}")

if __name__ == "__main__":
    current_dir = os.path.dirname(__file__)
    
    # Update both online order and dineout JSON files
    online_order_json_path = os.path.join(current_dir, "data/online_order_restaurants.json")
    dineout_json_path = os.path.join(current_dir, "data/dineout_restaurants.json")

    update_json_file(online_order_json_path)
    update_json_file(dineout_json_path)