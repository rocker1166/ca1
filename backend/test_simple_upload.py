#!/usr/bin/env python3
"""
Simple test script to test GoFile upload without folder ID
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from services.gofile_service import gofile_service

# Load environment variables
load_dotenv()

def test_simple_upload():
    """Test GoFile upload without folder ID"""
    
    print("🧪 Testing GoFile Upload Without Folder ID")
    print("=" * 50)
    
    # Create a test file
    test_file = "simple_test.txt"
    with open(test_file, 'w') as f:
        f.write("Simple test file for GoFile upload without folder ID")
    
    print(f"📄 Created test file: {test_file}")
    
    # Test upload without folder ID (should work with or without token)
    result = gofile_service.upload_file(test_file, folder_id=None, custom_filename="simple_test_upload.txt")
    
    print(f"📤 Upload result: {result}")
    
    # Clean up
    if os.path.exists(test_file):
        os.remove(test_file)
        print(f"🧹 Cleaned up test file")
    
    return result

if __name__ == "__main__":
    test_simple_upload()
