from fastapi import APIRouter, HTTPException, Response, Request
from fastapi.responses import StreamingResponse
from services.prompt_engine import PromptEngine
from services.ppt_builder import PPTBuilder
from services.slide_schema import Deck
from services.streaming_service import streaming_service
from core.logger import get_logger
from core.config import settings
import threading
import uuid
import re
import uuid
import threading
import re

router = APIRouter()
logger = get_logger("api.routes")

# In-memory job store (for MVP; use Redis for prod)
jobs = {}
jobs_lock = threading.Lock()

class JobStatus:
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    ERROR = "error"

def job_worker(job_id, topic, username="anonymous", use_template=True, num_slides=8, include_images=True, include_diagrams=True, theme="professional"):
    with jobs_lock:
        jobs[job_id]["status"] = JobStatus.RUNNING
    
    # Emit job started event
    streaming_service.emit_event(job_id, "job_started", {
        "message": f"Starting PPT generation for '{topic}'",
        "topic": topic,
        "username": username,
        "num_slides": num_slides,
        "include_images": include_images,
        "include_diagrams": include_diagrams,
        "theme": theme
    })
    
    try:
        # Step 1: Generate slides with LLM
        streaming_service.emit_event(job_id, "llm_processing", {
            "message": "Calling AI to generate slide content...",
            "step": "content_generation"
        })
        
        engine = PromptEngine()
        logger.info(f"Calling LLM for topic: {topic} (user: {username})")
        deck = engine.generate_slides(topic, num_slides=num_slides, include_images=include_images, include_diagrams=include_diagrams)
        logger.info(f"Deck object created: {deck}")
        
        if not deck.slides:
            logger.error(f"Deck is empty for topic: {topic}")
            streaming_service.emit_event(job_id, "error", {
                "message": "No slides were generated",
                "error": "Empty deck"
            })
            return
        
        # Emit slides generated event
        slide_titles = [slide.title for slide in deck.slides]
        streaming_service.emit_event(job_id, "slides_generated", {
            "message": f"Generated {len(deck.slides)} slides",
            "slide_count": len(deck.slides),
            "slide_titles": slide_titles
        })
        
        # Step 2: Build PPTX
        streaming_service.emit_event(job_id, "building_pptx", {
            "message": "Creating PowerPoint presentation...",
            "step": "pptx_generation"
        })
        
        # Pass theme to PPTBuilder
        builder = PPTBuilder(theme=theme)
        pptx_stream = builder.build(deck, use_template=use_template, job_id=job_id)
        logger.info(f"PPTX built in memory")
        
        streaming_service.emit_event(job_id, "pptx_built", {
            "message": "PowerPoint presentation created successfully",
            "file_size": len(pptx_stream.getvalue())
        })
        
        # Step 3: Upload to cloud storage
        streaming_service.emit_event(job_id, "uploading", {
            "message": "Uploading presentation to cloud storage...",
            "step": "cloud_upload"
        })
        
        # Upload to GoFile - this is now the primary storage
        online_url = None
        if settings.gofile_enabled:
            try:
                from services.gofile_service import gofile_service
                
                # Create custom filename for GoFile: [username]_[topic_name].pptx
                custom_filename = create_custom_filename(username, topic)
                upload_result = gofile_service.upload_stream(pptx_stream, custom_filename)
                
                if upload_result["success"]:
                    online_url = upload_result["download_url"]
                    logger.info(f"Uploaded to GoFile with custom name '{custom_filename}': {online_url}")
                    
                    streaming_service.emit_event(job_id, "upload_complete", {
                        "message": "Upload completed successfully",
                        "filename": custom_filename,
                        "download_url": online_url
                    })
                else:
                    logger.error(f"GoFile upload failed: {upload_result.get('error')}")
                    streaming_service.emit_event(job_id, "error", {
                        "message": "Failed to upload presentation",
                        "error": upload_result.get('error')
                    })
                    raise Exception(f"GoFile upload failed: {upload_result.get('error')}")
            except Exception as upload_err:
                logger.error(f"Failed to upload to GoFile: {upload_err}")
                streaming_service.emit_event(job_id, "error", {
                    "message": "Upload failed",
                    "error": str(upload_err)
                })
                with jobs_lock:
                    jobs[job_id]["status"] = JobStatus.ERROR
                    jobs[job_id]["error"] = f"File upload failed: {str(upload_err)}"
                return
        else:
            logger.error("GoFile integration is disabled - cannot store PPTX file")
            streaming_service.emit_event(job_id, "error", {
                "message": "Cloud storage not configured",
                "error": "GoFile integration disabled"
            })
            with jobs_lock:
                jobs[job_id]["status"] = JobStatus.ERROR
                jobs[job_id]["error"] = "File storage is not configured"
            return
        
        # Step 4: Job completed
        streaming_service.emit_event(job_id, "job_complete", {
            "message": "Presentation generation completed successfully!",
            "download_url": online_url,
            "slide_count": len(deck.slides),
            "slide_titles": slide_titles
        })
        
        # Update job status - only online URL now
        with jobs_lock:
            jobs[job_id]["status"] = JobStatus.DONE
            jobs[job_id]["online_url"] = online_url
        
        logger.info(f"Job {job_id} completed: Online URL: {online_url}")
    except Exception as e:
        streaming_service.emit_event(job_id, "error", {
            "message": "An error occurred during generation",
            "error": str(e),
            "step": "general_error"
        })
        with jobs_lock:
            jobs[job_id]["status"] = JobStatus.ERROR
            jobs[job_id]["error"] = str(e)
        logger.error(f"Job {job_id} failed: {e}")

def create_custom_filename(username: str, topic: str) -> str:
    """Create a custom filename using format: [username]_[topic_name].pptx"""
    import re
    
    # Clean username - remove special characters and spaces
    clean_username = re.sub(r'[^\w\-_]', '', username.replace(' ', '_'))
    
    # Clean topic - remove special characters, replace spaces with underscores
    clean_topic = re.sub(r'[^\w\-_\s]', '', topic).replace(' ', '_')
    
    # Limit length to avoid very long filenames
    clean_username = clean_username[:20] if clean_username else "anonymous"
    clean_topic = clean_topic[:50] if clean_topic else "presentation"
    
    return f"{clean_username}_{clean_topic}.pptx"

@router.post("/generate")
async def generate_ppt(request: Request):
    data = await request.json()
    topic = data.get("topic")
    username = data.get("username", "anonymous")  # New username field
    use_template = data.get("use_template", False)
    sync = data.get("sync", False)
    
    # Enhanced options
    num_slides = data.get("num_slides", 8)
    include_images = data.get("include_images", True)
    include_diagrams = data.get("include_diagrams", True)
    theme = data.get("theme", "professional")
    
    if not topic or not isinstance(topic, str):
        logger.error(f"Invalid topic received: {topic}")
        raise HTTPException(status_code=400, detail="Missing or invalid 'topic'")
    
    if sync:
        # Synchronous processing for debugging
        try:
            engine = PromptEngine()
            logger.info(f"Calling LLM for topic: {topic} (user: {username})")
            deck = engine.generate_slides(topic, num_slides=num_slides, include_images=include_images, include_diagrams=include_diagrams)
            logger.info(f"Deck object created: {deck}")
            if not deck.slides:
                logger.error(f"Deck is empty for topic: {topic}")
            builder = PPTBuilder(theme=theme)
            pptx_stream = builder.build(deck, use_template=use_template)
            logger.info(f"PPTX built in memory")
            
            # Create response without local download URL
            response = {
                "slides": [s.title for s in deck.slides],
                "username": username,
                "topic": topic
            }
            
            # Upload to GoFile if enabled - this is now the primary storage
            if settings.gofile_enabled:
                try:
                    from services.gofile_service import gofile_service
                    
                    # Create custom filename for GoFile: [username]_[topic_name].pptx
                    custom_filename = create_custom_filename(username, topic)
                    upload_result = gofile_service.upload_stream(pptx_stream, custom_filename)
                    
                    if upload_result["success"]:
                        online_url = upload_result["download_url"]
                        response["online_url"] = online_url
                        logger.info(f"Uploaded to GoFile with custom name '{custom_filename}': {online_url}")
                    else:
                        logger.error(f"GoFile upload failed: {upload_result.get('error')}")
                        raise HTTPException(status_code=500, detail=f"File upload failed: {upload_result.get('error')}")
                except Exception as upload_err:
                    logger.error(f"Failed to upload to GoFile: {upload_err}")
                    raise HTTPException(status_code=500, detail=f"File upload failed: {str(upload_err)}")
            else:
                logger.error("GoFile integration is disabled - cannot store PPTX file")
                raise HTTPException(status_code=500, detail="File storage is not configured")
                
            return response
        except Exception as e:
            logger.error(f"Failed to generate PPT: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    else:
        # Async job worker (production)
        job_id = str(uuid.uuid4())
        
        # Create streaming session for this job
        stream_id = streaming_service.create_stream(job_id, topic, username)
        
        debug_info = {
            "job_id": job_id,
            "stream_id": stream_id,
            "topic": topic,
            "username": username,
            "status": JobStatus.PENDING,
            "error": None,
            "url": None,
            "use_template": use_template,
            "num_slides": num_slides,
            "include_images": include_images,
            "include_diagrams": include_diagrams,
            "theme": theme
        }
        with jobs_lock:
            jobs[job_id] = {"status": JobStatus.PENDING, "online_url": None, "error": None, "stream_id": stream_id}
        threading.Thread(target=job_worker, args=(job_id, topic, username, use_template, num_slides, include_images, include_diagrams, theme), daemon=True).start()
        logger.info(f"Enqueued job {job_id} for topic '{topic}' by user '{username}' (use_template={use_template}, num_slides={num_slides})")
        return {
            "job_id": job_id,
            "stream_id": stream_id,
            "topic": topic,
            "username": username,
            "status": JobStatus.PENDING,
            "debug": debug_info
        }

@router.get("/status/{job_id}")
def get_status(job_id: str):
    with jobs_lock:
        job = jobs.get(job_id)
        if not job:
            logger.error(f"Status check for missing job_id: {job_id}")
            raise HTTPException(status_code=404, detail="Job not found")
        resp = {"status": job["status"]}
        if job["status"] == JobStatus.DONE:
            # Only include online URL now
            if "online_url" in job:
                resp["online_url"] = job["online_url"]
        if job["status"] == JobStatus.ERROR:
            resp["error"] = job["error"]
        # Include stream ID if available
        if "stream_id" in job:
            resp["stream_id"] = job["stream_id"]
    return resp

@router.get("/stream/{stream_id}")
async def stream_job_progress(stream_id: str):
    """Stream real-time updates about job progress using Server-Sent Events"""
    
    # Validate stream exists
    stream_info = streaming_service.get_stream_info(stream_id)
    if not stream_info:
        raise HTTPException(status_code=404, detail="Stream not found")
    
    # Return streaming response
    return StreamingResponse(
        streaming_service.stream_events(stream_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )

@router.get("/stream/{stream_id}/info")
def get_stream_info(stream_id: str):
    """Get information about a streaming session"""
    stream_info = streaming_service.get_stream_info(stream_id)
    if not stream_info:
        raise HTTPException(status_code=404, detail="Stream not found")
    
    return {
        "stream_id": stream_id,
        "job_id": stream_info["job_id"],
        "topic": stream_info["topic"],
        "username": stream_info["username"],
        "created_at": stream_info["created_at"],
        "status": stream_info["status"],
        "connected": stream_info["connected"]
    }

@router.get("/streams/active")
def get_active_streams():
    """Get all active streaming sessions"""
    active_streams = streaming_service.get_active_streams()
    return {
        "active_streams": len(active_streams),
        "streams": [
            {
                "stream_id": stream_id,
                "job_id": info["job_id"],
                "topic": info["topic"],
                "username": info["username"],
                "status": info["status"],
                "created_at": info["created_at"]
            }
            for stream_id, info in active_streams.items()
        ]
    }


