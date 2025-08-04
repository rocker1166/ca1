from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Gemini API settings
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    
    # Unsplash API settings
    unsplash_access_key: Optional[str] = None
    unsplash_secret_key: Optional[str] = None
    
    # GoFile.io API settings
    gofile_api_token: Optional[str] = None
    gofile_folder_id: Optional[str] = None
    gofile_enabled: bool = True
    
    # Image settings
    default_image_size: str = "800x600"
    enable_images: bool = True
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8001
    debug: bool = False
    
    # Other settings
    temp_file_lifetime: int = 600  # seconds
    allowed_origins: str = "*"

    class Config:
        env_file = ".env"
        case_sensitive = False  # Allow case-insensitive environment variables

settings = Settings()
