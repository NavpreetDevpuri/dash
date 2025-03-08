import unittest
import os
import sys
from unittest.mock import patch, MagicMock

# Adjust the path to import from parent directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.db import create_user_database
from config import TestConfig

class DatabaseTest(unittest.TestCase):
    """Test database operations separately."""
    
    def setUp(self):
        """Set up test environment."""
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
    
    def tearDown(self):
        """Tear down test environment."""
        self.app_context.pop()
    
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
    
    @patch('app.db.ArangoClient')
    def test_setup_user_collections(self, mock_arango_client):
        """Test that setup_user_collections creates the required collections."""
        from app.db import setup_user_collections
        
        # Create mock database
        mock_db = MagicMock()
        mock_db.has_collection.return_value = False
        
        # Mock the collections
        mock_dineout = MagicMock()
        mock_food = MagicMock()
        mock_personal = MagicMock()
        mock_work = MagicMock()
        mock_system = MagicMock()
        
        mock_db.collection.side_effect = {
            "dineout_keywords": mock_dineout,
            "food_keywords": mock_food,
            "personal_contacts": mock_personal,
            "work_contacts": mock_work,
            "_system": mock_system
        }.get
        
        # Call the function
        result = setup_user_collections(mock_db)
        
        # Assertions
        self.assertTrue(result)
        self.assertEqual(mock_db.create_collection.call_count, 4)  # 4 collections
        mock_calls = mock_db.create_collection.call_args_list
        collection_names = [call[1]['name'] for call in mock_calls]
        self.assertIn('dineout_keywords', collection_names)
        self.assertIn('food_keywords', collection_names)
        self.assertIn('personal_contacts', collection_names)
        self.assertIn('work_contacts', collection_names)

if __name__ == '__main__':
    unittest.main() 