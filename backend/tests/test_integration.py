import unittest
import json
import os
import sys
import time
from arango import ArangoClient

# Adjust the path to import from parent directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from config import TestConfig

class IntegrationTest(unittest.TestCase):
    """
    Integration tests that actually call the APIs and verify database operations.
    These tests require a running ArangoDB instance.
    """
    
    @classmethod
    def setUpClass(cls):
        """Set up the test environment once for all tests."""
        # Configure connection to ArangoDB
        cls.arango_client = ArangoClient(hosts=TestConfig.ARANGO_URL)
        
        # Connect to system database with root credentials
        cls.sys_db = cls.arango_client.db(
            '_system',
            username=TestConfig.ARANGO_USERNAME,
            password=TestConfig.ARANGO_PASSWORD
        )
        
        # Ensure test databases don't exist from previous runs
        cls.clean_test_databases()
    
    def setUp(self):
        """Set up before each test."""
        # Create a test app
        self.app = create_app(TestConfig)
        
        # Create a test client
        self.client = self.app.test_client()
        
        # Push an application context
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Create a unique identifier for this test run to avoid conflicts
        self.test_timestamp = int(time.time())
        
        # Generate unique test user credentials
        self.test_username = f"testuser_{self.test_timestamp}"
        self.test_email = f"test_{self.test_timestamp}@example.com"
        self.test_password = "Test123!"
    
    def tearDown(self):
        """Clean up after each test."""
        self.app_context.pop()
        
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests in this class."""
        cls.clean_test_databases()
    
    @classmethod
    def clean_test_databases(cls):
        """Remove test databases created during tests."""
        for db_name in cls.sys_db.databases():
            if db_name.startswith("user_test_"):
                try:
                    cls.sys_db.delete_database(db_name)
                    print(f"Deleted test database: {db_name}")
                except Exception as e:
                    print(f"Error deleting database {db_name}: {str(e)}")
    
    def test_signup_login_and_database_creation(self):
        """
        Test the complete user flow:
        1. Register a new user
        2. Log in with the user
        3. Verify user database was created with correct collections
        4. Log out
        """
        # Step 1: Register a new user
        signup_response = self.client.post(
            '/auth/signup',
            data=json.dumps({
                'username': self.test_username,
                'email': self.test_email,
                'password': self.test_password
            }),
            content_type='application/json'
        )
        
        # Check if signup was successful
        self.assertEqual(signup_response.status_code, 201)
        signup_data = json.loads(signup_response.data)
        self.assertIn('message', signup_data)
        self.assertIn('created', signup_data['message'].lower())
        
        # Step 2: Log in with the new user
        signin_response = self.client.post(
            '/auth/signin',
            data=json.dumps({
                'email': self.test_email,
                'password': self.test_password
            }),
            content_type='application/json'
        )
        
        # Check if login was successful
        self.assertEqual(signin_response.status_code, 200)
        signin_data = json.loads(signin_response.data)
        self.assertIn('message', signin_data)
        self.assertIn('successful', signin_data['message'].lower())
        self.assertIn('user', signin_data)
        self.assertIn('id', signin_data['user'])
        
        # Get the user ID from the response
        user_id = signin_data['user']['id']
        
        # Step 3: Verify the user database was created with correct collections
        # Connect to system database
        try:
            # Check if user database exists
            db_name = f"user_{user_id}"
            self.assertTrue(self.sys_db.has_database(db_name))
            
            # Connect to user database
            admin_password = TestConfig.ARANGO_PASSWORD
            user_db = self.arango_client.db(db_name, username=TestConfig.ARANGO_USERNAME, password=admin_password)
            
            # Verify that the expected collections exist
            expected_collections = [
                'dineout_keywords',
                'food_keywords',
                'personal_contacts',
                'work_contacts'
            ]
            
            for collection_name in expected_collections:
                self.assertTrue(
                    user_db.has_collection(collection_name), 
                    f"Collection {collection_name} was not created in user database"
                )
            
            # Step 4: Log out
            logout_response = self.client.get('/auth/logout')
            self.assertEqual(logout_response.status_code, 200)
            logout_data = json.loads(logout_response.data)
            self.assertIn('message', logout_data)
            self.assertIn('logout', logout_data['message'].lower())
        
        except Exception as e:
            self.fail(f"Exception during database verification: {str(e)}")
    
    def test_signup_with_existing_username(self):
        """Test signup with an existing username."""
        # First, create a user
        self.client.post(
            '/auth/signup',
            data=json.dumps({
                'username': self.test_username,
                'email': self.test_email,
                'password': self.test_password
            }),
            content_type='application/json'
        )
        
        # Try to create another user with the same username
        response = self.client.post(
            '/auth/signup',
            data=json.dumps({
                'username': self.test_username,
                'email': f"another_{self.test_timestamp}@example.com",
                'password': self.test_password
            }),
            content_type='application/json'
        )
        
        # Check response
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('username', data['error'].lower())
    
    def test_signin_with_invalid_credentials(self):
        """Test signin with invalid credentials."""
        # First, create a user
        self.client.post(
            '/auth/signup',
            data=json.dumps({
                'username': self.test_username,
                'email': self.test_email,
                'password': self.test_password
            }),
            content_type='application/json'
        )
        
        # Try to sign in with wrong password
        response = self.client.post(
            '/auth/signin',
            data=json.dumps({
                'email': self.test_email,
                'password': 'wrong_password'
            }),
            content_type='application/json'
        )
        
        # Check response
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('invalid', data['error'].lower())

if __name__ == '__main__':
    unittest.main() 