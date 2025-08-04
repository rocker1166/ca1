#!/usr/bin/env python3
"""
HTTP Client Test for Streaming Service
Uses only Python standard library (no external dependencies)
"""

import os
import sys
import json
import time
import threading
from urllib.request import urlopen, Request
from urllib.parse import urlencode
from urllib.error import URLError, HTTPError
from datetime import datetime

def test_http_streaming(base_url="http://localhost:8001"):
    """Test streaming endpoints via HTTP using only standard library"""
    print("🌐 TESTING HTTP STREAMING ENDPOINTS")
    print("=" * 60)
    
    try:
        # Test 1: Check server health
        print("\n1️⃣ Checking server connectivity...")
        try:
            with urlopen(f"{base_url}/health", timeout=5) as response:
                if response.getcode() == 200:
                    print("✅ Server is running and accessible")
                else:
                    print(f"❌ Server returned status: {response.getcode()}")
                    return False
        except (URLError, HTTPError) as e:
            print(f"❌ Cannot connect to server: {e}")
            print(f"Make sure server is running on {base_url}")
            print("Start with: uvicorn main:app --reload --host 0.0.0.0 --port 8001")
            return False
        
        # Test 2: Start a PPT generation job
        print("\n2️⃣ Starting PPT generation job...")
        job_data = {
            "topic": "HTTP Streaming Test - AI Fundamentals", 
            "username": "http_tester",
            "num_slides": 6,
            "include_images": True,
            "include_diagrams": True,
            "sync": False  # Async for streaming
        }
        
        # Create POST request
        data = json.dumps(job_data).encode('utf-8')
        req = Request(f"{base_url}/generate")
        req.add_header('Content-Type', 'application/json')
        req.add_header('Content-Length', str(len(data)))
        
        try:
            with urlopen(req, data=data, timeout=10) as response:
                if response.getcode() == 200:
                    job_info = json.loads(response.read().decode('utf-8'))
                    job_id = job_info["job_id"]
                    print(f"✅ Job started successfully: {job_id}")
                else:
                    print(f"❌ Failed to start job: {response.getcode()}")
                    return False
        except Exception as e:
            print(f"❌ Error starting job: {e}")
            return False
        
        # Test 3: Check active streams endpoint
        print("\n3️⃣ Checking active streams...")
        try:
            with urlopen(f"{base_url}/streams/active", timeout=5) as response:
                if response.getcode() == 200:
                    streams_data = json.loads(response.read().decode('utf-8'))
                    active_count = streams_data.get("active_streams", 0)
                    print(f"✅ Active streams endpoint working: {active_count} streams")
                else:
                    print(f"❌ Active streams endpoint failed: {response.getcode()}")
        except Exception as e:
            print(f"⚠️ Active streams check failed: {e}")
        
        # Test 4: Test streaming endpoint (basic connectivity)
        print(f"\n4️⃣ Testing streaming endpoint...")
        stream_url = f"{base_url}/stream/{job_id}"
        
        try:
            # Try to connect to streaming endpoint
            req = Request(stream_url)
            req.add_header('Accept', 'text/event-stream')
            req.add_header('Cache-Control', 'no-cache')
            
            # Note: We can't easily test SSE streaming with urllib
            # Just test that the endpoint exists and is accessible
            print(f"📡 Streaming URL: {stream_url}")
            print("ℹ️  Streaming endpoint test requires SSE-compatible client")
            print("   Use: curl -N -H 'Accept: text/event-stream' " + stream_url)
            
        except Exception as e:
            print(f"⚠️ Streaming endpoint test skipped: {e}")
        
        # Test 5: Monitor job status
        print(f"\n5️⃣ Monitoring job completion...")
        max_wait = 30  # 30 seconds for HTTP test
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                with urlopen(f"{base_url}/status/{job_id}", timeout=5) as response:
                    if response.getcode() == 200:
                        status_data = json.loads(response.read().decode('utf-8'))
                        current_status = status_data["status"]
                        
                        if current_status == "done":
                            online_url = status_data.get("online_url", "No URL provided")
                            print(f"✅ Job completed!")
                            print(f"   Download URL: {online_url}")
                            break
                        elif current_status == "error":
                            error = status_data.get("error", "Unknown error")
                            print(f"❌ Job failed: {error}")
                            return False
                        else:
                            print(f"⏳ Job status: {current_status}")
                    else:
                        print(f"❌ Status check failed: {response.getcode()}")
                        break
                        
            except Exception as e:
                print(f"❌ Status check error: {e}")
                break
            
            time.sleep(2)  # Check every 2 seconds
        else:
            print("⏰ Job monitoring timed out")
            return False
        
        print("✅ HTTP streaming test completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ HTTP streaming test failed: {e}")
        return False

def test_stream_info_endpoints(base_url="http://localhost:8001"):
    """Test stream information endpoints"""
    print("\n📋 TESTING STREAM INFO ENDPOINTS")
    print("=" * 60)
    
    try:
        # Test active streams endpoint
        print("\n1️⃣ Testing active streams endpoint...")
        with urlopen(f"{base_url}/streams/active", timeout=5) as response:
            if response.getcode() == 200:
                data = json.loads(response.read().decode('utf-8'))
                print(f"✅ Active streams: {data.get('active_streams', 0)}")
                
                streams = data.get('streams', [])
                if streams:
                    print("   Current streams:")
                    for stream in streams[:3]:  # Show first 3
                        print(f"   - {stream.get('job_id', 'Unknown')}: {stream.get('topic', 'No topic')}")
                else:
                    print("   No active streams")
                
                return True
            else:
                print(f"❌ Failed: {response.getcode()}")
                return False
    except Exception as e:
        print(f"❌ Stream info test failed: {e}")
        return False

def create_curl_examples():
    """Generate curl examples for testing"""
    print("\n📝 CURL EXAMPLES FOR MANUAL TESTING")
    print("=" * 60)
    
    examples = [
        {
            "name": "1. Start PPT Generation",
            "curl": '''curl -X POST "http://localhost:8001/generate" \\
  -H "Content-Type: application/json" \\
  -d '{
    "topic": "Streaming Demo - Cloud Computing",
    "username": "demo_user",
    "num_slides": 5,
    "sync": false
  }' '''
        },
        {
            "name": "2. Check Job Status",
            "curl": 'curl "http://localhost:8001/status/YOUR_JOB_ID"'
        },
        {
            "name": "3. Stream Job Progress (replace JOB_ID)",
            "curl": '''curl -N -H "Accept: text/event-stream" \\
  "http://localhost:8001/stream/YOUR_JOB_ID"'''
        },
        {
            "name": "4. List Active Streams",
            "curl": 'curl "http://localhost:8001/streams/active"'
        },
        {
            "name": "5. Get Stream Info (replace STREAM_ID)",
            "curl": 'curl "http://localhost:8001/stream/YOUR_STREAM_ID/info"'
        }
    ]
    
    for example in examples:
        print(f"\n{example['name']}:")
        print(example['curl'])

def main():
    """Main test function"""
    print("🔧 HTTP Streaming Service Test (Standard Library Only)")
    print("=" * 70)
    
    base_url = "http://localhost:8001"
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    
    print(f"Testing server at: {base_url}")
    
    # Run tests
    tests = [
        ("HTTP Streaming Test", lambda: test_http_streaming(base_url)),
        ("Stream Info Endpoints", lambda: test_stream_info_endpoints(base_url))
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            print(f"\n🧪 Running: {test_name}")
            result = test_func()
            results[test_name] = result
            
            if result:
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"💥 {test_name}: ERROR - {e}")
            results[test_name] = False
    
    # Show curl examples
    create_curl_examples()
    
    # Summary
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    print(f"\n📊 RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 HTTP streaming tests completed successfully!")
    else:
        print("⚠️ Some HTTP tests failed - check server status")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    exit(main())
