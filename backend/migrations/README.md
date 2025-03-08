# Database Migrations

This folder contains scripts for initializing and populating the database. Instead of using an automatic setup function, these scripts allow more control over the database setup process.

## Available Migration Scripts

- **contacts_importer.py**: Import contact data into the database
- **dineout_food_preferences_importer.py**: Import dining preferences data
- **normalize_ratings_and_coordinates.py**: Normalize restaurant ratings and coordinates
- **restaurant_graph_importer.py**: Import restaurant data and build the restaurant graph

## How to Run Migrations

Run each migration script as needed:

```bash
cd backend
python -m migrations.contacts_importer
python -m migrations.dineout_food_preferences_importer
python -m migrations.normalize_ratings_and_coordinates
python -m migrations.restaurant_graph_importer
```

## Migration Order

The suggested order for running migrations is:

1. restaurant_graph_importer.py
2. normalize_ratings_and_coordinates.py
3. contacts_importer.py
4. dineout_food_preferences_importer.py

## User-Specific Databases

The application creates user-specific databases during registration, which are separate from the common data imported by these scripts. The user data is stored in databases named `user_{user_id}` and contains:

- dineout_keywords (Document collection)
- food_keywords (Document collection)
- personal_contacts (Document collection)
- work_contacts (Document collection) 