import unittest
import json
import os
import sys
from unittest.mock import patch, MagicMock, call
import tempfile
import shutil

# Adjust the path to import from parent directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.models import User
from app.db import create_user_database
from config import TestConfig

class AuthDatabaseTest(unittest.TestCase):
    """Test the database functions separately from the routes."""
    def setUp(self):
        """Set up test environment."""
        # Create the test app with TestConfig
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Apply patches before creating the test client
        self.setup_patches()
        
        # Create test client
        self.client = self.app.test_client()
        
        # Create a temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
    
    def setup_patches(self):
        """Set up all the required patches for testing."""
        # Patch Flask-Login current_user to be anonymous for all tests
        self.patch_current_user = patch('flask_login.utils._get_user', return_value=None)
        self.mock_current_user = self.patch_current_user.start()
        
        # Patch User model methods
        self.patch_find_by_email = patch('app.models.User.find_by_email')
        self.mock_find_by_email = self.patch_find_by_email.start()
        
        self.patch_find_by_username = patch('app.models.User.find_by_username')
        self.mock_find_by_username = self.patch_find_by_username.start()
        
        self.patch_user_create = patch('app.models.User.create')
        self.mock_user_create = self.patch_user_create.start()
        
        # Patch password hashing
        self.patch_bcrypt = patch('app.bcrypt.generate_password_hash')
        self.mock_hash = self.patch_bcrypt.start()
        self.mock_hash.return_value = b'hashed_password'
        
        self.patch_check_hash = patch('app.bcrypt.check_password_hash')
        self.mock_check_hash = self.patch_check_hash.start()
        
        # Patch database operations
        self.patch_create_db = patch('app.routes.auth.create_user_database')
        self.mock_create_db = self.patch_create_db.start()
        self.mock_create_db.return_value = True
        
        # Patch login functions
        self.patch_login_user = patch('app.routes.auth.login_user')
        self.mock_login_user = self.patch_login_user.start()
        
        self.patch_logout_user = patch('app.routes.auth.logout_user')
        self.mock_logout_user = self.patch_logout_user.start()
    
    def tearDown(self):
        """Tear down test environment."""
        # Stop all patches
        patch.stopall()
        
        # Remove temporary directory
        shutil.rmtree(self.temp_dir)
        
        # Pop app context
        self.app_context.pop()
    
    def test_signup_success(self):
        """Test successful user signup."""
        # Mock behavior
        self.mock_find_by_username.return_value = None
        self.mock_find_by_email.return_value = None
        
        # Create a mock user object
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = 'testuser'
        mock_user.email = 'test@example.com'
        mock_user.password = 'hashed_password'
        self.mock_user_create.return_value = mock_user
        
        # Test the signup route
        response = self.client.post(
            '/auth/signup',
            data=json.dumps({
                'username': 'testuser',
                'email': 'test@example.com',
                'password': 'password123'
            }),
            content_type='application/json'
        )
        
        # Assertions
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'Your account has been created! You can now log in.')
        
        # Check that the user was created
        self.mock_user_create.assert_called_once_with(
            username='testuser', 
            email='test@example.com', 
            password_hash='hashed_password'
        )
        
        # Check that the database was created
        self.mock_create_db.assert_called_once_with(1, 'testuser', 'hashed_password')
        
    def test_signup_existing_username(self):
        """Test signup with an existing username."""
        # Mock behavior - username exists
        self.mock_find_by_username.return_value = MagicMock()
        
        # Test the signup route
        response = self.client.post(
            '/auth/signup',
            data=json.dumps({
                'username': 'existinguser',
                'email': 'new@example.com',
                'password': 'password123'
            }),
            content_type='application/json'
        )
        
        # Assertions
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Username already taken')
        
    def test_signup_existing_email(self):
        """Test signup with an existing email."""
        # Mock behavior - username doesn't exist but email does
        self.mock_find_by_username.return_value = None
        self.mock_find_by_email.return_value = MagicMock()
        
        # Test the signup route
        response = self.client.post(
            '/auth/signup',
            data=json.dumps({
                'username': 'newuser',
                'email': 'existing@example.com',
                'password': 'password123'
            }),
            content_type='application/json'
        )
        
        # Assertions
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Email already registered')
        
    def test_signup_missing_fields(self):
        """Test signup with missing required fields."""
        # Test the signup route with missing username
        response = self.client.post(
            '/auth/signup',
            data=json.dumps({
                'email': 'test@example.com',
                'password': 'password123'
            }),
            content_type='application/json'
        )
        
        # Assertions
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Missing required fields')
        
    def test_signin_success(self):
        """Test successful user signin."""
        # Create a mock user
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = 'testuser'
        mock_user.email = 'test@example.com'
        mock_user.password = 'hashed_password'
        mock_user.is_active = True
        
        # Mock behavior
        self.mock_find_by_email.return_value = mock_user
        self.mock_check_hash.return_value = True
        self.mock_login_user.return_value = True
        
        # Test the signin route
        response = self.client.post(
            '/auth/signin',
            data=json.dumps({
                'email': 'test@example.com',
                'password': 'password123'
            }),
            content_type='application/json'
        )
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'Login successful')
        self.assertEqual(data['user']['id'], 1)
        self.assertEqual(data['user']['username'], 'testuser')
        self.assertEqual(data['user']['email'], 'test@example.com')
        self.mock_login_user.assert_called_once_with(mock_user)
            
    def test_signin_invalid_credentials(self):
        """Test signin with invalid credentials."""
        # Create a mock user
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = 'testuser'
        mock_user.email = 'test@example.com'
        mock_user.password = 'hashed_password'
        
        # Mock behavior - user exists but wrong password
        self.mock_find_by_email.return_value = mock_user
        self.mock_check_hash.return_value = False
        
        # Test the signin route
        response = self.client.post(
            '/auth/signin',
            data=json.dumps({
                'email': 'test@example.com',
                'password': 'wrongpassword'
            }),
            content_type='application/json'
        )
        
        # Assertions
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Invalid email or password')
        
    def test_signin_missing_fields(self):
        """Test signin with missing required fields."""
        # Test the signin route with missing password
        response = self.client.post(
            '/auth/signin',
            data=json.dumps({
                'email': 'test@example.com'
            }),
            content_type='application/json'
        )
        
        # Assertions
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Missing email or password')
        
    def test_logout(self):
        """Test user logout."""
        # Mock behavior
        self.mock_logout_user.return_value = None
        
        # Test the logout route
        response = self.client.get('/auth/logout')
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'Successfully logged out')
        self.mock_logout_user.assert_called_once()
    
    @patch('app.db.ArangoClient')
    @patch('app.db.setup_user_collections')
    def test_create_user_database(self, mock_setup_collections, mock_arango_client):
        """Test the create_user_database function directly."""
        # Mock the ArangoDB client
        mock_client = mock_arango_client.return_value
        
        # Mock the system database
        mock_sys_db = MagicMock()
        mock_client.db.return_value = mock_sys_db
        mock_sys_db.has_database.return_value = False
        mock_sys_db.has_user.return_value = False
        mock_sys_db.has_collection.return_value = False
        
        # Mock the collection
        mock_collection = MagicMock()
        mock_sys_db.collection.return_value = mock_collection
        
        # Call the function
        result = create_user_database(1, 'testuser', 'hashed_password')
        
        # Assertions
        self.assertTrue(result)
        mock_sys_db.create_database.assert_called_once()
        mock_sys_db.create_user.assert_called_once()
        mock_sys_db.update_permission.assert_called_once()
        mock_setup_collections.assert_called_once()
        mock_collection.insert.assert_called_once()

if __name__ == '__main__':
    unittest.main()