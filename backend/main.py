from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router
from core.config import settings
from core.logger import get_logger

app = FastAPI()
logger = get_logger()

# CORS for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.allowed_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(router)

@app.get("/health")
def health_check():
    logger.info("Health check called")
    return {"status": "ok"} 