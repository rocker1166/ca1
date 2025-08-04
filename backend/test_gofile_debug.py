#!/usr/bin/env python3
"""
Debug script to test GoFile upload with detailed logging
"""
import os
import sys
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(level=logging.DEBUG)

from services.gofile_service import gofile_service

def test_gofile_debug():
    """Test GoFile upload with debug info"""
    
    # First test connection
    print("=== Testing GoFile Connection ===")
    connection_result = gofile_service.test_connection()
    print(f"Connection result: {connection_result}")
    
    # Create a test file
    test_file = "test_upload.txt"
    with open(test_file, 'w') as f:
        f.write("This is a test file for GoFile upload debugging")
    
    print(f"\n=== Testing File Upload ===")
    print(f"Test file created: {test_file}")
    
    # Test upload
    result = gofile_service.upload_file(test_file, custom_filename="debug_test.txt")
    print(f"Upload result: {result}")
    
    # Clean up
    if os.path.exists(test_file):
        os.remove(test_file)
    
    return result

if __name__ == "__main__":
    result = test_gofile_debug()
    print(f"\nFinal result: {result}")
