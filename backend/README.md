# Backend for Slide Deck Generator

This backend powers an AI-driven slide deck generator. It exposes a REST API to generate, check status, and download PowerPoint presentations based on a user-provided topic, leveraging Google Gemini (via LangChain) and dynamic slide layouts.

## Features
- **FastAPI**-based REST API
- Asynchronous job queue for slide generation
- Google Gemini LLM integration (via LangChain)
- Dynamic slide layouts (text, images, diagrams)
- PPTX generation using python-pptx
- Download endpoint for generated files
- Configurable via environment variables
- Includes basic tests and linting

## Directory Structure
```
backend/
  api/           # API route definitions
  core/          # Configuration and logging
  services/      # Business logic: prompt engine, PPT builder, schema
  utils/         # File management utilities
  templates/     # PowerPoint template(s)
  tests/         # Unit tests
  main.py        # FastAPI entry point
  requirements.txt
  run.sh         # Dev run script
  .flake8        # Linting config
  Dockerfile     # (empty, for future use)
  venv/          # (optional) Python virtual environment
```

## Setup Guide

### 1. Prerequisites
- Python 3.8+
- (Optional) [virtualenv](https://virtualenv.pypa.io/)
- Google Gemini API key (for LLM-powered slide generation)

### 2. Clone and Enter Backend Directory
```sh
cd backend
```

### 3. Create and Activate Virtual Environment (Recommended)
```sh
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 4. Install Dependencies
```sh
pip install -r requirements.txt
```

### 5. Configure Environment Variables
Create a `.env` file in `backend/` with your Gemini API key:
```
gemini_api_key=YOUR_API_KEY
```
Other settings (with defaults):
- `gemini_model` (default: models/gemini-pro)
- `temp_file_lifetime` (default: 600)
- `allowed_origins` (default: *)

#### Example `.env` file
```ini
# Google Gemini API key (required)
gemini_api_key=YOUR_API_KEY

# Gemini model name (optional)
gemini_model=models/gemini-pro

# Lifetime (in seconds) for temporary files (optional)
temp_file_lifetime=600

# Allowed CORS origins (optional)
allowed_origins=*
```

### 6. Run the Server (Development)
```sh
# With auto-reload:
sh run.sh
# Or manually:
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 7. API Endpoints
- `POST /generate` — Start slide deck generation. Body: `{ "topic": "Your topic" }`
- `GET /status/{job_id}` — Check job status. Returns status and download URL if ready.
- `GET /download/{filename}` — Download generated PPTX file.
- `GET /health` — Health check.

## Testing
- Run all tests:
```sh
pytest tests/
```
- Lint code:
```sh
flake8
```

## Main Components
- **api/routes.py**: Defines endpoints for generation, status, and download.
- **services/prompt_engine.py**: Handles prompt construction and LLM calls.
- **services/ppt_builder.py**: Builds PPTX files from slide data.
- **services/slide_schema.py**: Pydantic models for slides and decks.
- **core/config.py**: Loads settings from `.env` or environment.
- **core/logger.py**: JSON logging setup.
- **utils/file_manager.py**: Handles temp file storage and cleanup.

## Notes
- The `Dockerfile` is currently empty; add your own for containerization.
- The `template.pptx` in `templates/` is used as a base for generated decks.
- The backend is designed for local development and prototyping. For production, consider using a persistent job queue and secure file handling.

---

Feel free to extend or modify this README as your project evolves. 