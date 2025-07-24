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

def job_worker(job_id, topic, use_template=True):
    with jobs_lock:
        jobs[job_id]["status"] = JobStatus.RUNNING
    try:
        engine = PromptEngine()
        logger.info(f"Calling LLM for topic: {topic}")
        deck = engine.generate_slides(topic)
        logger.info(f"Deck object created: {deck}")
        if not deck.slides:
            logger.error(f"Deck is empty for topic: {topic}")
        builder = PPTBuilder()
        pptx_path = builder.build(deck, use_template=use_template)
        logger.info(f"PPTX built at: {pptx_path}")
        with jobs_lock:
            jobs[job_id]["status"] = JobStatus.DONE
            jobs[job_id]["result"] = pptx_path
            jobs[job_id]["url"] = f"/download/{os.path.basename(pptx_path)}"
        cleanup_file(pptx_path, settings.temp_file_lifetime)
        logger.info(f"Job {job_id} completed: {jobs[job_id]['url']}")
    except Exception as e:
        with jobs_lock:
            jobs[job_id]["status"] = JobStatus.ERROR
            jobs[job_id]["error"] = str(e)
        logger.error(f"Job {job_id} failed: {e}")

@router.post("/generate")
async def generate_ppt(request: Request):
    data = await request.json()
    topic = data.get("topic")
    use_template = data.get("use_template", True)
    sync = data.get("sync", False)
    if not topic or not isinstance(topic, str):
        logger.error(f"Invalid topic received: {topic}")
        raise HTTPException(status_code=400, detail="Missing or invalid 'topic'")
    if sync:
        # Synchronous processing for debugging
        try:
            engine = PromptEngine()
            logger.info(f"Calling LLM for topic: {topic}")
            deck = engine.generate_slides(topic)
            logger.info(f"Deck object created: {deck}")
            if not deck.slides:
                logger.error(f"Deck is empty for topic: {topic}")
            builder = PPTBuilder()
            pptx_path = builder.build(deck, use_template=use_template)
            logger.info(f"PPTX built at: {pptx_path}")
            cleanup_file(pptx_path, settings.temp_file_lifetime)
            url = f"/download/{os.path.basename(pptx_path)}"
            return {"url": url, "slides": [s.title for s in deck.slides]}
        except Exception as e:
            logger.error(f"Failed to generate PPT: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    else:
        # Async job worker (production)
        job_id = str(uuid.uuid4())
        debug_info = {
            "job_id": job_id,
            "topic": topic,
            "status": JobStatus.PENDING,
            "error": None,
            "url": None,
            "use_template": use_template
        }
        with jobs_lock:
            jobs[job_id] = {"status": JobStatus.PENDING, "result": None, "url": None, "error": None}
        threading.Thread(target=job_worker, args=(job_id, topic, use_template), daemon=True).start()
        logger.info(f"Enqueued job {job_id} for topic '{topic}' (use_template={use_template})")
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
