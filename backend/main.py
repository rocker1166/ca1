from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router
from core.config import settings
from core.logger import get_logger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()
logger = get_logger()

# Initialize services on startup
@app.on_event("startup")
async def startup_event():
    # Initialize GoFile service if enabled
    if settings.gofile_enabled:
        try:
            from services.gofile_service import gofile_service
            connection_result = gofile_service.test_connection()
            if connection_result["success"]:
                logger.info("GoFile service initialized successfully")
                if "account_id" in connection_result:
                    logger.info(f"Using GoFile account: {connection_result['account_id']}")
                else:
                    logger.info("Using GoFile guest upload mode")
            else:
                logger.warning(f"GoFile service initialization failed: {connection_result.get('error')}")
        except Exception as e:
            logger.error(f"Failed to initialize GoFile service: {e}")
            logger.info("Continuing without GoFile service")

# CORS for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.allowed_origins == "*" else [settings.allowed_origins],
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