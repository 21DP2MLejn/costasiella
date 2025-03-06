#!/usr/bin/env python3
"""
Test script to validate Mollie API key
"""
import sys
import logging
from mollie.api.client import Client
from mollie.api.error import Error as MollieError

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_mollie_api_key(api_key):
    """Test if a Mollie API key is valid by making a simple API call"""
    logger.info(f"Testing Mollie API key: {api_key[:5]}{'*' * (len(api_key) - 9)}{api_key[-4:]}")
    
    try:
        # Initialize the Mollie client
        mollie = Client()
        mollie.set_api_key(api_key)
        
        # Try to list payment methods (simple API call)
        methods = mollie.methods.list()
        
        # If we get here, the API key is valid
        logger.info("API key is valid! Successfully retrieved payment methods.")
        logger.info(f"Available payment methods: {[method['id'] for method in methods]}")
        return True
    except MollieError as e:
        logger.error(f"API key validation failed: {str(e)}")
        return False

if __name__ == "__main__":
    # Get API key from command line argument or use default test key
    api_key = sys.argv[1] if len(sys.argv) > 1 else "test_stMBnq9xJQhVCJhNUGCJN24zxW2TkD"
    
    if test_mollie_api_key(api_key):
        logger.info("Mollie API key validation successful!")
        sys.exit(0)
    else:
        logger.error("Mollie API key validation failed!")
        sys.exit(1)
