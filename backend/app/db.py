from arango import ArangoClient
from config import Config

client = ArangoClient(hosts=Config.ARANGO_URL)
# Connect to the specified database using credentials from Config.
db = client.db(Config.ARANGO_DB_NAME, username=Config.ARANGO_USERNAME, password=Config.ARANGO_PASSWORD)

def get_db():
    return db