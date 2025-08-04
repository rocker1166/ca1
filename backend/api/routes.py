from fastapi import APIRouter, HTTPException, Response, Request
from fastapi.responses import FileResponse
from services.prompt_engine import PromptEngine
from services.ppt_builder import PPTBuilder
from services.slide_schema import Deck
from utils.file_manager import get_download_path, cleanup_file
from core.logger import get_logger
from core.config import settings
import os
import uuid
import threading
import time

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
    try:
        engine = PromptEngine()
        logger.info(f"Calling LLM for topic: {topic} (user: {username})")
        deck = engine.generate_slides(topic, num_slides=num_slides, include_images=include_images, include_diagrams=include_diagrams)
        logger.info(f"Deck object created: {deck}")
        if not deck.slides:
            logger.error(f"Deck is empty for topic: {topic}")
        # Pass theme to PPTBuilder
        builder = PPTBuilder(theme=theme)
        pptx_path = builder.build(deck, use_template=use_template)
        logger.info(f"PPTX built at: {pptx_path}")
        
        # Set local download URL
        local_url = f"/download/{os.path.basename(pptx_path)}"
        
        # Try to upload to GoFile if enabled
        online_url = None
        if settings.gofile_enabled:
            try:
                from services.gofile_service import gofile_service
                
                # Create custom filename for GoFile: [username]_[topic_name].pptx
                custom_filename = create_custom_filename(username, topic)
                upload_result = gofile_service.upload_file(pptx_path, custom_filename=custom_filename)
                
                if upload_result["success"]:
                    online_url = upload_result["download_url"]
                    logger.info(f"Uploaded to GoFile with custom name '{custom_filename}': {online_url}")
                else:
                    logger.error(f"GoFile upload failed: {upload_result.get('error')}")
            except Exception as upload_err:
                logger.error(f"Failed to upload to GoFile: {upload_err}")
        
        # Update job status
        with jobs_lock:
            jobs[job_id]["status"] = JobStatus.DONE
            jobs[job_id]["result"] = pptx_path
            jobs[job_id]["url"] = local_url
            if online_url:
                jobs[job_id]["online_url"] = online_url
        
        cleanup_file(pptx_path, settings.temp_file_lifetime)
        logger.info(f"Job {job_id} completed: Local URL: {local_url}, Online URL: {online_url or 'N/A'}")
    except Exception as e:
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
    use_template = data.get("use_template", True)
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
            pptx_path = builder.build(deck, use_template=use_template)
            logger.info(f"PPTX built at: {pptx_path}")
            
            # Set local download URL
            url = f"/download/{os.path.basename(pptx_path)}"
            
            # Try to upload to GoFile if enabled
            online_url = None
            if settings.gofile_enabled:
                try:
                    from services.gofile_service import gofile_service
                    
                    # Create custom filename for GoFile: [username]_[topic_name].pptx
                    custom_filename = create_custom_filename(username, topic)
                    upload_result = gofile_service.upload_file(pptx_path, custom_filename=custom_filename)
                    
                    if upload_result["success"]:
                        online_url = upload_result["download_url"]
                        logger.info(f"Uploaded to GoFile with custom name '{custom_filename}': {online_url}")
                    else:
                        logger.error(f"GoFile upload failed: {upload_result.get('error')}")
                except Exception as upload_err:
                    logger.error(f"Failed to upload to GoFile: {upload_err}")
            
            cleanup_file(pptx_path, settings.temp_file_lifetime)
            response = {
                "url": url, 
                "slides": [s.title for s in deck.slides],
                "username": username,
                "topic": topic
            }
            
            if online_url:
                response["online_url"] = online_url
                
            return response
        except Exception as e:
            logger.error(f"Failed to generate PPT: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    else:
        # Async job worker (production)
        job_id = str(uuid.uuid4())
        debug_info = {
            "job_id": job_id,
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
            jobs[job_id] = {"status": JobStatus.PENDING, "result": None, "url": None, "error": None}
        threading.Thread(target=job_worker, args=(job_id, topic, username, use_template, num_slides, include_images, include_diagrams, theme), daemon=True).start()
        logger.info(f"Enqueued job {job_id} for topic '{topic}' by user '{username}' (use_template={use_template}, num_slides={num_slides})")
        return {
            "job_id": job_id,
            "topic": topic,
            "username": username,
            "status": JobStatus.PENDING,
            "debug": debug_info
        }
        return {
            "job_id": job_id,
            "topic": topic,
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
            resp["url"] = job["url"]
            # Include online URL if available
            if "online_url" in job:
                resp["online_url"] = job["online_url"]
        if job["status"] == JobStatus.ERROR:
            resp["error"] = job["error"]
    return resp

@router.get("/download/{filename}")
def download_ppt(filename: str):
    path = get_download_path(filename)
    if not os.path.exists(path):
        logger.error(f"Download requested for missing file: {filename}")
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path, media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation", filename=filename)
