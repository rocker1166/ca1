#!/usr/bin/env python3
"""
Test script for the Streaming Service functionality
Tests both the streaming service directly and via HTTP endpoints
"""

import os
import sys
import time
import requests
import threading
import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from services.streaming_service import streaming_service
from core.logger import get_logger

# Load environment variables
load_dotenv()

logger = get_logger("test_streaming")

class StreamingTester:
    """Test class for streaming functionality"""
    
    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url
        self.results = []
    
    def test_streaming_service_direct(self):
        """Test the streaming service directly (unit test)"""
        print("\n" + "="*60)
        print("🧪 TESTING STREAMING SERVICE (DIRECT)")
        print("="*60)
        
        try:
            # Test 1: Create stream
            print("\n1️⃣ Testing stream creation...")
            job_id = "test-job-123"
            topic = "Machine Learning Basics"
            username = "test_user"
            
            stream_id = streaming_service.create_stream(job_id, topic, username)
            print(f"✅ Stream created: {stream_id}")
            
            # Test 2: Emit events
            print("\n2️⃣ Testing event emission...")
            test_events = [
                {"type": "job_started", "data": {"message": "Starting PPT generation", "progress": 0}},
                {"type": "analyzing_topic", "data": {"message": "Analyzing topic content", "progress": 10}},
                {"type": "generating_slides", "data": {"message": "Generating slide structure", "progress": 25}},
                {"type": "slide_created", "data": {"slide_number": 1, "title": "Introduction", "progress": 40}},
                {"type": "slide_created", "data": {"slide_number": 2, "title": "Key Concepts", "progress": 60}},
                {"type": "adding_images", "data": {"message": "Adding images to slides", "progress": 80}},
                {"type": "finalizing", "data": {"message": "Finalizing presentation", "progress": 95}},
                {"type": "completed", "data": {"message": "PPT generation completed", "progress": 100, "download_url": "https://example.com/download"}}
            ]
            
            for event in test_events:
                streaming_service.emit_event(job_id, event["type"], event["data"])
                print(f"📡 Emitted: {event['type']}")
                time.sleep(0.2)  # Small delay to simulate real processing
            
            # Test 3: Get events
            print("\n3️⃣ Testing event retrieval...")
            events = streaming_service.get_events(stream_id)
            print(f"✅ Retrieved {len(events)} events")
            
            for i, event in enumerate(events):
                progress = event["data"].get("progress", "N/A")
                print(f"   {i+1}. {event['type']} - Progress: {progress}% - {event['data'].get('message', '')}")
            
            # Test 4: Stream info
            print("\n4️⃣ Testing stream info...")
            info = streaming_service.get_stream_info(stream_id)
            if info:
                print(f"✅ Stream info: Job {info['job_id']}, Topic: {info['topic']}, User: {info['username']}")
            else:
                print("❌ Could not retrieve stream info")
            
            # Test 5: Cleanup
            print("\n5️⃣ Testing cleanup...")
            streaming_service.cleanup_stream(stream_id)
            print("✅ Stream cleaned up")
            
            return True
            
        except Exception as e:
            print(f"❌ Direct streaming test failed: {e}")
            return False
    
    def test_streaming_endpoints(self):
        """Test streaming via HTTP endpoints"""
        print("\n" + "="*60)
        print("🌐 TESTING STREAMING VIA HTTP ENDPOINTS")
        print("="*60)
        
        try:
            # Test 1: Check if server is running
            print("\n1️⃣ Testing server connectivity...")
            try:
                response = requests.get(f"{self.base_url}/health", timeout=5)
                if response.status_code == 200:
                    print("✅ Server is running")
                else:
                    print(f"❌ Server returned status: {response.status_code}")
                    return False
            except requests.exceptions.RequestException as e:
                print(f"❌ Server is not running: {e}")
                print("Please start the server with: python -m uvicorn main:app --reload --host 0.0.0.0 --port 8001")
                return False
            
            # Test 2: Start a real PPT generation job
            print("\n2️⃣ Testing real PPT generation with streaming...")
            job_data = {
                "topic": "Streaming Test - Python Fundamentals",
                "username": "streaming_tester",
                "num_slides": 5,
                "include_images": True,
                "include_diagrams": True,
                "sync": False  # Use async to test streaming
            }
            
            response = requests.post(f"{self.base_url}/generate", json=job_data)
            if response.status_code == 200:
                job_info = response.json()
                job_id = job_info["job_id"]
                print(f"✅ Job started: {job_id}")
                
                # Test 3: Connect to streaming endpoint
                print("\n3️⃣ Testing streaming connection...")
                stream_url = f"{self.base_url}/stream/{job_id}"
                
                def stream_listener():
                    """Listen to the stream in a separate thread"""
                    try:
                        response = requests.get(stream_url, stream=True, timeout=60)
                        if response.status_code == 200:
                            print("✅ Connected to stream")
                            event_count = 0
                            
                            for line in response.iter_lines():
                                if line:
                                    line = line.decode('utf-8')
                                    if line.startswith('data: '):
                                        try:
                                            data = json.loads(line[6:])  # Remove 'data: ' prefix
                                            event_count += 1
                                            
                                            # Print meaningful events
                                            if 'message' in data:
                                                progress = data.get('progress', 'N/A')
                                                print(f"📡 Event {event_count}: {data['message']} (Progress: {progress}%)")
                                            elif 'slide_number' in data:
                                                print(f"📄 Slide {data['slide_number']}: {data.get('title', 'Untitled')}")
                                            elif 'download_url' in data:
                                                print(f"🎉 Completed! Download: {data['download_url']}")
                                                break
                                                
                                        except json.JSONDecodeError:
                                            pass  # Skip malformed JSON
                            
                            print(f"✅ Stream completed with {event_count} events")
                            return True
                        else:
                            print(f"❌ Stream connection failed: {response.status_code}")
                            return False
                    except Exception as e:
                        print(f"❌ Stream error: {e}")
                        return False
                
                # Start streaming in a separate thread
                stream_thread = threading.Thread(target=stream_listener)
                stream_thread.daemon = True
                stream_thread.start()
                
                # Wait for job completion (check status periodically)
                print("\n4️⃣ Monitoring job status...")
                max_wait = 60  # 60 seconds max
                start_time = time.time()
                
                while time.time() - start_time < max_wait:
                    status_response = requests.get(f"{self.base_url}/status/{job_id}")
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        current_status = status_data["status"]
                        
                        if current_status == "done":
                            online_url = status_data.get("online_url", "No URL")
                            print(f"✅ Job completed! Download URL: {online_url}")
                            break
                        elif current_status == "error":
                            error = status_data.get("error", "Unknown error")
                            print(f"❌ Job failed: {error}")
                            return False
                        else:
                            print(f"⏳ Job status: {current_status}")
                    
                    time.sleep(3)
                else:
                    print("⏰ Job timed out")
                    return False
                
                # Wait for stream thread to complete
                stream_thread.join(timeout=5)
                return True
                
            else:
                print(f"❌ Failed to start job: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ HTTP streaming test failed: {e}")
            return False
    
    def test_multiple_streams(self):
        """Test multiple concurrent streams"""
        print("\n" + "="*60)
        print("🔀 TESTING MULTIPLE CONCURRENT STREAMS")
        print("="*60)
        
        try:
            # Create multiple streams for different jobs
            streams = []
            for i in range(3):
                job_id = f"multi-job-{i+1}"
                topic = f"Test Topic {i+1}"
                username = f"user_{i+1}"
                
                stream_id = streaming_service.create_stream(job_id, topic, username)
                streams.append({"stream_id": stream_id, "job_id": job_id})
                print(f"✅ Created stream {i+1}: {stream_id}")
            
            # Emit events to different jobs
            for i, stream in enumerate(streams):
                job_id = stream["job_id"]
                streaming_service.emit_event(job_id, "job_started", {
                    "message": f"Job {i+1} started",
                    "progress": 0
                })
                streaming_service.emit_event(job_id, "slide_created", {
                    "slide_number": 1,
                    "title": f"Slide from Job {i+1}",
                    "progress": 50
                })
            
            # Check that each stream gets only its own events
            for i, stream in enumerate(streams):
                events = streaming_service.get_events(stream["stream_id"])
                print(f"✅ Stream {i+1} received {len(events)} events (expected: 2)")
                
                if len(events) != 2:
                    print(f"❌ Stream {i+1} received wrong number of events")
                    return False
            
            # Cleanup all streams
            for stream in streams:
                streaming_service.cleanup_stream(stream["stream_id"])
            
            print("✅ Multiple streams test passed")
            return True
            
        except Exception as e:
            print(f"❌ Multiple streams test failed: {e}")
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 STARTING STREAMING SERVICE COMPREHENSIVE TESTS")
        print("=" * 70)
        
        tests = [
            ("Direct Service Test", self.test_streaming_service_direct),
            ("HTTP Endpoints Test", self.test_streaming_endpoints),
            ("Multiple Streams Test", self.test_multiple_streams)
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
                print(f"❌ {test_name}: ERROR - {e}")
                results[test_name] = False
        
        # Final summary
        print("\n" + "="*70)
        print("📊 TEST RESULTS SUMMARY")
        print("="*70)
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test_name:.<50} {status}")
        
        print(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED! Streaming service is working correctly.")
        else:
            print("⚠️ Some tests failed. Check the output above for details.")
        
        return passed == total

def main():
    """Main test function"""
    print("🔧 PPT Generator - Streaming Service Test Suite")
    print("=" * 70)
    
    # Allow custom base URL
    base_url = "http://localhost:8001"
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
        print(f"Using custom base URL: {base_url}")
    
    tester = StreamingTester(base_url)
    success = tester.run_all_tests()
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
