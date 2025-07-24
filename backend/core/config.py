from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    temp_file_lifetime: int = 600  # seconds
    allowed_origins: str = "*"

    class Config:
        env_file = ".env"

settings = Settings()
