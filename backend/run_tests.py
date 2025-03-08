import os
import sys
import unittest

# Add the backend directory to the path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import the tests
from tests.test_db import DatabaseTest
from tests.test_integration import IntegrationTest

if __name__ == '__main__':
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Run tests for the backend')
    parser.add_argument('--db-only', action='store_true', help='Run only database tests (no integration tests)')
    parser.add_argument('--integration-only', action='store_true', help='Run only integration tests')
    args = parser.parse_args()
    
    # Create a test suite
    test_suite = unittest.TestSuite()
    
    # Add tests to the suite based on arguments
    if args.integration_only:
        print("Running integration tests only...")
        test_suite.addTest(unittest.makeSuite(IntegrationTest))
    elif args.db_only:
        print("Running database tests only...")
        test_suite.addTest(unittest.makeSuite(DatabaseTest))
    else:
        # Run all tests by default
        print("Running all tests...")
        test_suite.addTest(unittest.makeSuite(DatabaseTest))
        test_suite.addTest(unittest.makeSuite(IntegrationTest))
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Exit with non-zero code if any tests failed
    sys.exit(not result.wasSuccessful()) 