import asyncio
import json
import uuid
from typing import Dict, Any, Optional, AsyncGenerator
from datetime import datetime
from core.logger import get_logger
from fastapi import Request
from fastapi.responses import StreamingResponse
from threading import Lock

logger = get_logger("streaming_service")

class StreamingService:
    """Service for streaming real-time updates about PPT generation progress"""
    
    def __init__(self):
        self.active_streams: Dict[str, Dict[str, Any]] = {}
        self.stream_lock = Lock()
    
    def create_stream(self, job_id: str, topic: str, username: str = "anonymous") -> str:
        """Create a new streaming session for a job"""
        stream_id = str(uuid.uuid4())
        
        with self.stream_lock:
            self.active_streams[stream_id] = {
                "job_id": job_id,
                "topic": topic,
                "username": username,
                "created_at": datetime.now().isoformat(),
                "status": "initializing",
                "events": [],
                "connected": True
            }
        
        logger.info(f"Created stream {stream_id} for job {job_id}")
        return stream_id
    
    def emit_event(self, job_id: str, event_type: str, data: Dict[str, Any]):
        """Emit an event to all streams watching this job"""
        event = {
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        
        with self.stream_lock:
            # Find all streams for this job
            for stream_id, stream_info in self.active_streams.items():
                if stream_info["job_id"] == job_id and stream_info["connected"]:
                    stream_info["events"].append(event)
                    stream_info["status"] = event_type
        
        logger.info(f"Emitted event '{event_type}' for job {job_id}: {data}")
    
    def get_events(self, stream_id: str) -> list:
        """Get all events for a stream and clear them"""
        with self.stream_lock:
            if stream_id in self.active_streams:
                events = self.active_streams[stream_id]["events"].copy()
                self.active_streams[stream_id]["events"].clear()
                return events
        return []
    
    def close_stream(self, stream_id: str):
        """Close a streaming session"""
        with self.stream_lock:
            if stream_id in self.active_streams:
                self.active_streams[stream_id]["connected"] = False
                logger.info(f"Closed stream {stream_id}")
    
    def cleanup_stream(self, stream_id: str):
        """Remove a streaming session completely"""
        with self.stream_lock:
            if stream_id in self.active_streams:
                del self.active_streams[stream_id]
                logger.info(f"Cleaned up stream {stream_id}")
    
    async def stream_events(self, stream_id: str) -> AsyncGenerator[str, None]:
        """Generate Server-Sent Events for a stream"""
        if stream_id not in self.active_streams:
            yield f"event: error\ndata: {json.dumps({'error': 'Stream not found'})}\n\n"
            return
        
        # Send initial connection event
        initial_data = {
            "message": "Connected to stream",
            "stream_id": stream_id,
            "job_id": self.active_streams[stream_id]["job_id"],
            "topic": self.active_streams[stream_id]["topic"],
            "username": self.active_streams[stream_id]["username"]
        }
        yield f"event: connected\ndata: {json.dumps(initial_data)}\n\n"
        
        try:
            while True:
                # Check if stream is still active
                with self.stream_lock:
                    if stream_id not in self.active_streams or not self.active_streams[stream_id]["connected"]:
                        break
                
                # Get new events
                events = self.get_events(stream_id)
                
                # Send each event
                for event in events:
                    event_data = json.dumps(event["data"])
                    yield f"event: {event['type']}\ndata: {event_data}\n\n"
                    
                    # If this is a job_complete or error event, close the stream
                    if event['type'] in ['job_complete', 'error']:
                        logger.info(f"Stream {stream_id} ending due to {event['type']} event")
                        self.close_stream(stream_id)
                        return
                
                # Wait before checking for new events
                await asyncio.sleep(0.1)  # Reduced from 0.5 to 0.1 for faster updates
                
        except asyncio.CancelledError:
            logger.info(f"Stream {stream_id} cancelled by client")
        except Exception as e:
            logger.error(f"Error in stream {stream_id}: {e}")
            error_data = {"error": str(e)}
            yield f"event: error\ndata: {json.dumps(error_data)}\n\n"
        finally:
            self.close_stream(stream_id)
    
    def get_stream_info(self, stream_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a stream"""
        with self.stream_lock:
            return self.active_streams.get(stream_id)
    
    def get_active_streams(self) -> Dict[str, Dict[str, Any]]:
        """Get all active streams"""
        with self.stream_lock:
            return {sid: info for sid, info in self.active_streams.items() if info["connected"]}

# Global instance
streaming_service = StreamingService()
