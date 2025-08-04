#!/usr/bin/env python3
"""
Test script to verify that the PPTX builder no longer stores files locally
and only uploads to GoFile
"""

import os
import sys
import json
import requests
from io import BytesIO

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_no_local_files():
    """Test that no local files are created"""
    print("🔍 Testing that no local PPTX files are created...")
    
    # Check if tmp directory exists and is empty initially
    tmp_dir = os.path.join(os.path.dirname(__file__), 'tmp')
    if os.path.exists(tmp_dir):
        initial_files = os.listdir(tmp_dir)
        pptx_files_before = [f for f in initial_files if f.endswith('.pptx')]
        print(f"Initial PPTX files in tmp: {len(pptx_files_before)}")
    else:
        pptx_files_before = []
        print("tmp directory doesn't exist yet")
    
    # Test the sync endpoint
    payload = {
        "topic": "Test Presentation - No Local Storage",
        "username": "test_user",
        "sync": True,
        "num_slides": 3,
        "use_template": True
    }
    
    try:
        print("📤 Sending sync request...")
        response = requests.post(
            "http://localhost:8001/generate",
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Sync request successful!")
            print(f"Response keys: {list(result.keys())}")
            
            # Verify no local URL is returned
            if "url" in result:
                print(f"❌ ERROR: Local 'url' field should not be present in response: {result['url']}")
                return False
            else:
                print("✅ No local 'url' field in response - good!")
            
            # Verify online URL is present
            if "online_url" in result:
                print(f"✅ Online URL present: {result['online_url']}")
            else:
                print("❌ ERROR: 'online_url' field missing from response")
                return False
            
            # Check that no new local PPTX files were created
            if os.path.exists(tmp_dir):
                final_files = os.listdir(tmp_dir)
                pptx_files_after = [f for f in final_files if f.endswith('.pptx')]
                print(f"Final PPTX files in tmp: {len(pptx_files_after)}")
                
                if len(pptx_files_after) == len(pptx_files_before):
                    print("✅ No new local PPTX files created - good!")
                    return True
                else:
                    print(f"❌ ERROR: New PPTX files created locally: {set(pptx_files_after) - set(pptx_files_before)}")
                    return False
            else:
                print("✅ tmp directory still doesn't exist - no local files created!")
                return True
                
        else:
            print(f"❌ Sync request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_download_endpoint_removed():
    """Test that the local download endpoint is no longer available"""
    print("\n🔍 Testing that local download endpoint is removed...")
    
    try:
        response = requests.get("http://localhost:8001/download/test.pptx")
        if response.status_code == 404:
            print("✅ Download endpoint properly returns 404 - good!")
            return True
        else:
            print(f"❌ ERROR: Download endpoint still working with status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Could not connect to server. Is it running?")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def main():
    print("🚀 Testing No Local Storage Implementation")
    print("=" * 50)
    
    # Test server is running
    try:
        response = requests.get("http://localhost:8001/")
        print("✅ Server is running")
    except:
        print("❌ Server is not running on http://localhost:8001")
        print("Please start the server with: python main.py")
        return
    
    # Run tests
    test1_passed = test_no_local_files()
    test2_passed = test_download_endpoint_removed()
    
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS:")
    print(f"No Local Files Test: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Download Endpoint Test: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 ALL TESTS PASSED! Local storage has been successfully removed.")
    else:
        print("\n❌ SOME TESTS FAILED! Please check the implementation.")

if __name__ == "__main__":
    main()
