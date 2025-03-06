#!/usr/bin/env python3
"""
Script to update the Mollie API key in the system settings using GraphQL API.
"""
import requests
import json

# GraphQL endpoint URL
GRAPHQL_URL = "http://localhost:8000/d/graphql/"

# Test Mollie API key for development
# In a real environment, you would get a real test key from Mollie
TEST_API_KEY = "test_stMBnq9xJQhVCJhNUGCJN24zxW2TkD"

# GraphQL mutation to update the system setting
MUTATION = """
mutation UpdateMollieApiKey($value: String!) {
  updateSystemSetting(input: {
    setting: "integration_mollie_api_key",
    value: $value
  }) {
    systemSetting {
      setting
      value
    }
  }
}
"""

def update_mollie_api_key():
    """
    Update the Mollie API key using GraphQL mutation
    """
    # Variables for the GraphQL mutation
    variables = {
        "value": TEST_API_KEY
    }
    
    # Headers for the GraphQL request
    headers = {
        "Content-Type": "application/json",
    }
    
    # Prepare the request payload
    payload = {
        "query": MUTATION,
        "variables": variables
    }
    
    try:
        # Send the GraphQL request
        response = requests.post(
            GRAPHQL_URL,
            headers=headers,
            data=json.dumps(payload)
        )
        
        # Check if the request was successful
        if response.status_code == 200:
            result = response.json()
            if "errors" in result:
                print(f"GraphQL Error: {result['errors']}")
            else:
                print("Mollie API key updated successfully!")
                print(f"Setting: {result['data']['updateSystemSetting']['systemSetting']['setting']}")
                print(f"Value: {result['data']['updateSystemSetting']['systemSetting']['value']}")
        else:
            print(f"HTTP Error: {response.status_code}")
            print(response.text)
    
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    print(f"Updating Mollie API key to: {TEST_API_KEY}")
    update_mollie_api_key()
