import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key')
    ARANGO_URL = os.environ.get('ARANGO_URL', 'http://localhost:8529')
    ARANGO_DB_NAME = '_system'
    ARANGO_USERNAME = os.environ.get('ARANGO_USERNAME', 'root')
    ARANGO_PASSWORD = os.environ.get('ARANGO_PASSWORD', '')

class TestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    # Use a test database prefix 
    ARANGO_TEST_PREFIX = "test_"
    # Set a fixed SECRET_KEY for testing
    SECRET_KEY = 'test-secret-key'
    # Skip database initialization for faster tests
    SKIP_DB_INIT = True
    
    # Override this method to use test databases
    @property
    def ARANGO_DATABASE(self):
        return f"{self.ARANGO_TEST_PREFIX}common_db"