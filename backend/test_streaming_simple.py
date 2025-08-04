#!/usr/bin/env python3
"""
Simple Python test for the Streaming Service
Tests the streaming service functionality without external dependencies
"""

import os
import sys
import time
from datetime import datetime

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.streaming_service import streaming_service
from core.logger import get_logger

logger = get_logger("test_streaming_simple")

def test_basic_streaming():
    """Test basic streaming functionality"""
    print("🧪 TESTING BASIC STREAMING FUNCTIONALITY")
    print("=" * 60)
    
    try:
        # Test 1: Create a stream
        print("\n1️⃣ Creating a new stream...")
        job_id = "test-job-basic-001"
        topic = "Python Programming Fundamentals"
        username = "test_user"
        
        stream_id = streaming_service.create_stream(job_id, topic, username)
        print(f"✅ Stream created successfully: {stream_id}")
        
        # Test 2: Emit various events to simulate PPT generation
        print("\n2️⃣ Simulating PPT generation with events...")
        
        simulation_events = [
            {
                "type": "job_started",
                "data": {"message": "Starting PPT generation", "progress": 0}
            },
            {
                "type": "analyzing_topic", 
                "data": {"message": "Analyzing topic and structure", "progress": 10}
            },
            {
                "type": "generating_outline",
                "data": {"message": "Creating presentation outline", "progress": 20}
            },
            {
                "type": "slide_created",
                "data": {
                    "slide_number": 1,
                    "title": "Introduction to Python",
                    "content": "Overview of Python programming language",
                    "progress": 30
                }
            },
            {
                "type": "slide_created",
                "data": {
                    "slide_number": 2, 
                    "title": "Python Syntax",
                    "content": "Basic syntax and data types",
                    "progress": 45
                }
            },
            {
                "type": "fetching_images",
                "data": {"message": "Fetching relevant images", "progress": 60}
            },
            {
                "type": "image_added",
                "data": {
                    "slide_number": 1,
                    "image_url": "https://example.com/python-logo.png",
                    "progress": 70
                }
            },
            {
                "type": "creating_diagrams",
                "data": {"message": "Creating flow diagrams", "progress": 80}
            },
            {
                "type": "diagram_added",
                "data": {
                    "slide_number": 3,
                    "diagram_type": "process_flow",
                    "description": "Python execution flow",
                    "progress": 90
                }
            },
            {
                "type": "finalizing",
                "data": {"message": "Finalizing presentation", "progress": 95}
            },
            {
                "type": "completed",
                "data": {
                    "message": "PPT generation completed successfully!",
                    "progress": 100,
                    "download_url": "https://gofile.io/d/abc123",
                    "filename": "test_user_Python_Programming_Fundamentals.pptx"
                }
            }
        ]
        
        # Emit events with small delays to simulate real processing
        for i, event in enumerate(simulation_events):
            streaming_service.emit_event(job_id, event["type"], event["data"])
            
            # Display what we're emitting
            progress = event["data"].get("progress", "N/A")
            message = event["data"].get("message", "")
            slide_num = event["data"].get("slide_number", "")
            title = event["data"].get("title", "")
            
            if slide_num and title:
                print(f"   📄 Slide {slide_num}: {title} ({progress}%)")
            elif message:
                print(f"   📡 {event['type']}: {message} ({progress}%)")
            else:
                print(f"   🔄 {event['type']} ({progress}%)")
            
            time.sleep(0.3)  # Small delay to simulate processing time
        
        # Test 3: Retrieve and verify events
        print(f"\n3️⃣ Retrieving events from stream...")
        events = streaming_service.get_events(stream_id)
        print(f"✅ Retrieved {len(events)} events")
        
        if len(events) != len(simulation_events):
            print(f"❌ Expected {len(simulation_events)} events, got {len(events)}")
            return False
        
        # Test 4: Verify event content
        print("\n4️⃣ Verifying event content...")
        for i, event in enumerate(events):
            expected_type = simulation_events[i]["type"]
            if event["type"] != expected_type:
                print(f"❌ Event {i+1}: Expected type '{expected_type}', got '{event['type']}'")
                return False
        
        print("✅ All events have correct types")
        
        # Test 5: Get stream info
        print("\n5️⃣ Getting stream information...")
        stream_info = streaming_service.get_stream_info(stream_id)
        
        if not stream_info:
            print("❌ Could not retrieve stream info")
            return False
        
        print(f"✅ Stream Info:")
        print(f"   - Job ID: {stream_info['job_id']}")
        print(f"   - Topic: {stream_info['topic']}")
        print(f"   - Username: {stream_info['username']}")
        print(f"   - Status: {stream_info['status']}")
        print(f"   - Created: {stream_info['created_at']}")
        
        # Test 6: Cleanup
        print("\n6️⃣ Cleaning up stream...")
        streaming_service.cleanup_stream(stream_id)
        
        # Verify cleanup
        cleaned_info = streaming_service.get_stream_info(stream_id)
        if cleaned_info is not None:
            print("❌ Stream was not properly cleaned up")
            return False
        
        print("✅ Stream cleaned up successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic streaming test failed: {e}")
        return False

def test_multiple_jobs():
    """Test streaming with multiple concurrent jobs"""
    print("\n🔀 TESTING MULTIPLE CONCURRENT JOBS")
    print("=" * 60)
    
    try:
        # Create multiple streams
        streams = []
        job_configs = [
            {"topic": "Machine Learning Basics", "username": "ml_student"},
            {"topic": "Web Development with FastAPI", "username": "web_dev"},
            {"topic": "Data Science with Python", "username": "data_scientist"}
        ]
        
        print("\n1️⃣ Creating multiple streams...")
        for i, config in enumerate(job_configs):
            job_id = f"multi-job-{i+1}"
            stream_id = streaming_service.create_stream(
                job_id, config["topic"], config["username"]
            )
            streams.append({
                "stream_id": stream_id,
                "job_id": job_id,
                "topic": config["topic"],
                "username": config["username"]
            })
            print(f"   ✅ Stream {i+1}: {config['topic']} for {config['username']}")
        
        # Emit different events to each job
        print("\n2️⃣ Emitting events to different jobs...")
        for i, stream in enumerate(streams):
            job_id = stream["job_id"]
            topic = stream["topic"]
            
            # Emit job-specific events
            streaming_service.emit_event(job_id, "job_started", {
                "message": f"Starting {topic}",
                "progress": 0
            })
            
            streaming_service.emit_event(job_id, "slide_created", {
                "slide_number": 1,
                "title": f"{topic} - Introduction",
                "progress": 50
            })
            
            streaming_service.emit_event(job_id, "completed", {
                "message": f"{topic} completed",
                "progress": 100
            })
            
            print(f"   📡 Job {i+1}: Emitted 3 events")
        
        # Verify each stream gets only its events
        print("\n3️⃣ Verifying event isolation...")
        for i, stream in enumerate(streams):
            events = streaming_service.get_events(stream["stream_id"])
            
            if len(events) != 3:
                print(f"❌ Stream {i+1}: Expected 3 events, got {len(events)}")
                return False
            
            # Check that events are for the correct job
            for event in events:
                if "Starting" in event["data"].get("message", ""):
                    if stream["topic"] not in event["data"]["message"]:
                        print(f"❌ Stream {i+1}: Event contains wrong topic")
                        return False
            
            print(f"   ✅ Stream {i+1}: Received correct events")
        
        # Test active streams
        print("\n4️⃣ Testing active streams listing...")
        active_streams = streaming_service.get_active_streams()
        
        if len(active_streams) != 3:
            print(f"❌ Expected 3 active streams, got {len(active_streams)}")
            return False
        
        print(f"✅ Found {len(active_streams)} active streams")
        
        # Cleanup all streams
        print("\n5️⃣ Cleaning up all streams...")
        for stream in streams:
            streaming_service.cleanup_stream(stream["stream_id"])
        
        # Verify cleanup
        remaining_streams = streaming_service.get_active_streams()
        if len(remaining_streams) > 0:
            print(f"❌ {len(remaining_streams)} streams not cleaned up properly")
            return False
        
        print("✅ All streams cleaned up successfully")
        return True
        
    except Exception as e:
        print(f"❌ Multiple jobs test failed: {e}")
        return False

def test_event_types():
    """Test different event types that can be emitted during PPT generation"""
    print("\n📡 TESTING DIFFERENT EVENT TYPES")
    print("=" * 60)
    
    try:
        job_id = "event-types-test"
        stream_id = streaming_service.create_stream(job_id, "Event Types Test", "event_tester")
        
        # Test all possible event types
        event_types_to_test = [
            # Job lifecycle events
            ("job_started", {"message": "Job initialization", "progress": 0}),
            ("job_queued", {"message": "Job added to processing queue", "progress": 5}),
            
            # Analysis phase
            ("analyzing_topic", {"message": "Analyzing topic content", "progress": 10}),
            ("topic_analysis_complete", {"analysis_results": {"complexity": "medium", "slides_suggested": 8}, "progress": 15}),
            
            # Content generation
            ("generating_outline", {"message": "Creating presentation structure", "progress": 20}),
            ("outline_complete", {"outline": ["Intro", "Main Content", "Conclusion"], "progress": 25}),
            
            # Slide creation
            ("slide_created", {"slide_number": 1, "title": "Introduction", "type": "title", "progress": 35}),
            ("slide_created", {"slide_number": 2, "title": "Key Concepts", "type": "content", "progress": 45}),
            ("slide_created", {"slide_number": 3, "title": "Examples", "type": "image", "progress": 55}),
            
            # Media handling
            ("fetching_images", {"message": "Searching for relevant images", "progress": 60}),
            ("image_found", {"slide_number": 3, "image_url": "https://example.com/image1.jpg", "progress": 65}),
            ("image_added", {"slide_number": 3, "image_url": "https://example.com/image1.jpg", "progress": 70}),
            
            # Diagram creation
            ("creating_diagrams", {"message": "Generating process diagrams", "progress": 75}),
            ("diagram_created", {"slide_number": 4, "diagram_type": "process", "steps": 5, "progress": 80}),
            ("diagram_added", {"slide_number": 4, "diagram_type": "process", "progress": 85}),
            
            # Finalization
            ("applying_theme", {"theme": "professional", "progress": 90}),
            ("finalizing", {"message": "Applying final formatting", "progress": 95}),
            ("uploading", {"message": "Uploading to cloud storage", "progress": 98}),
            
            # Completion
            ("completed", {
                "message": "PPT generation completed successfully",
                "progress": 100,
                "download_url": "https://gofile.io/d/xyz789",
                "filename": "event_tester_Event_Types_Test.pptx",
                "total_slides": 8,
                "processing_time": "45.2s"
            }),
            
            # Error scenarios (optional)
            ("warning", {"message": "Image fetch timeout, using placeholder", "slide_number": 5}),
        ]
        
        print(f"\n1️⃣ Testing {len(event_types_to_test)} different event types...")
        
        for event_type, data in event_types_to_test:
            streaming_service.emit_event(job_id, event_type, data)
            
            # Show what we're testing
            if "progress" in data:
                print(f"   📡 {event_type}: {data.get('message', '')} ({data['progress']}%)")
            else:
                print(f"   ⚠️  {event_type}: {data.get('message', 'Additional info')}")
        
        # Retrieve and verify events
        print(f"\n2️⃣ Retrieving and verifying events...")
        events = streaming_service.get_events(stream_id)
        
        if len(events) != len(event_types_to_test):
            print(f"❌ Expected {len(event_types_to_test)} events, got {len(events)}")
            return False
        
        # Check event structure
        required_fields = ["type", "timestamp", "data"]
        for i, event in enumerate(events):
            for field in required_fields:
                if field not in event:
                    print(f"❌ Event {i+1} missing required field: {field}")
                    return False
            
            # Verify timestamp format
            try:
                datetime.fromisoformat(event["timestamp"])
            except ValueError:
                print(f"❌ Event {i+1} has invalid timestamp format: {event['timestamp']}")
                return False
        
        print("✅ All events have correct structure and timestamps")
        
        # Cleanup
        streaming_service.cleanup_stream(stream_id)
        print("✅ Stream cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Event types test failed: {e}")
        return False

def run_all_tests():
    """Run all streaming service tests"""
    print("🚀 STREAMING SERVICE - COMPREHENSIVE TEST SUITE")
    print("=" * 70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Basic Streaming Functionality", test_basic_streaming),
        ("Multiple Concurrent Jobs", test_multiple_jobs),
        ("Event Types Coverage", test_event_types)
    ]
    
    results = {}
    
    for test_name, test_function in tests:
        print(f"\n🧪 Running: {test_name}")
        try:
            result = test_function()
            results[test_name] = result
            
            if result:
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
                
        except Exception as e:
            print(f"💥 {test_name}: ERROR - {e}")
            results[test_name] = False
    
    # Final Results Summary
    print("\n" + "=" * 70)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 70)
    
    passed_tests = sum(1 for result in results.values() if result)
    total_tests = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:.<50} {status}")
    
    print("\n" + "-" * 70)
    print(f"Overall Results: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED! Streaming service is working correctly.")
        print("\nNext steps:")
        print("1. Start the server: uvicorn main:app --reload --host 0.0.0.0 --port 8001")
        print("2. Test HTTP streaming: curl http://localhost:8001/streams/active")
        print("3. Generate a PPT and watch real-time progress!")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        print("Fix the issues before using the streaming service in production.")
    
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return passed_tests == total_tests

def main():
    """Main function"""
    print("🔧 PPT Generator - Streaming Service Test")
    
    # Run tests
    success = run_all_tests()
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
