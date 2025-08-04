#!/usr/bin/env python3
"""
Test complete PPT generation with GoFile upload
"""
import requests
import json
import time

def test_complete_workflow():
    """Test the complete PPT generation + GoFile upload workflow"""
    
    print("🧪 TESTING COMPLETE PPT GENERATION + GOFILE UPLOAD")
    print("=" * 60)
    
    # Test data
    data = {
        'topic': 'Machine Learning Fundamentals', 
        'username': 'john_doe',
        'template': 'false',
        'num_slides': 4,
        'include_images': False,
        'include_diagrams': True
    }
    
    print(f"📝 Testing with data: {json.dumps(data, indent=2)}")
    
    try:
        # Make request to generate endpoint
        print("\n1️⃣ Starting PPT generation...")
        response = requests.post('http://localhost:8000/generate', json=data)
        
        if response.status_code == 200:
            result = response.json()
            job_id = result.get('job_id')
            print(f"✅ Job started successfully: {job_id}")
            
            # Poll status
            print("\n2️⃣ Monitoring job status...")
            max_attempts = 30
            for attempt in range(max_attempts):
                status_response = requests.get(f'http://localhost:8000/status/{job_id}')
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    print(f"📊 Status: {status_data.get('status')} (attempt {attempt + 1})")
                    
                    if status_data.get('status') == 'completed':
                        print("✅ Job completed successfully!")
                        print(f"📁 Local URL: {status_data.get('local_url', 'N/A')}")
                        print(f"🌐 Online URL: {status_data.get('online_url', 'N/A')}")
                        print(f"📝 Filename: {status_data.get('filename', 'N/A')}")
                        return True
                    elif status_data.get('status') == 'failed':
                        print(f"❌ Job failed: {status_data.get('error', 'Unknown error')}")
                        return False
                    else:
                        time.sleep(2)  # Wait 2 seconds before next check
                else:
                    print(f"⚠️ Status check failed: {status_response.status_code}")
                    
            print("⏰ Job did not complete within expected time")
            return False
            
        else:
            print(f"❌ Generation request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

if __name__ == "__main__":
    success = test_complete_workflow()
    if success:
        print("\n🎉 COMPLETE WORKFLOW TEST PASSED!")
    else:
        print("\n💥 COMPLETE WORKFLOW TEST FAILED!")
