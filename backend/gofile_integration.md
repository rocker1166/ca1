# GoFile Integration for Online PowerPoint Storage

This document explains the integration with GoFile.io API to store generated PowerPoint presentations online, making them accessible via public URLs.

## Overview

The system now supports storing generated PPT files online using the GoFile.io service. This allows:

1. Automatic uploading of generated PPTs to GoFile.io
2. Providing a public URL for presentation download
3. Long-term storage of presentations beyond the server's temporary storage

## Configuration

Add the following variables to your `.env` file:

```
# GoFile.io API settings
GOFILE_API_TOKEN=eOVIAo1oZzFaS0XTjJwZqgt4GQ9rC3lA
GOFILE_FOLDER_ID=bc5826dd-d9cb-4882-9da4-98e785c9b0ad
GOFILE_ENABLED=true
```

Where:
- `GOFILE_API_TOKEN`: Your GoFile.io API token (from your profile page at GoFile.io)
- `GOFILE_FOLDER_ID`: (Optional) ID of a specific folder to upload files to
- `GOFILE_ENABLED`: Set to "true" to enable online storage, "false" to disable it

## API Response Changes

When the GoFile integration is enabled and working correctly, the following endpoints will include additional information:

### Status Endpoint

`GET /status/{job_id}`

Response now includes:
```json
{
  "status": "done",
  "url": "/download/local_filename.pptx",
  "online_url": "https://gofile.io/d/abcdef123456"
}
```

The `online_url` field contains the public GoFile.io URL where the presentation can be downloaded.

### Generate Endpoint (sync=true)

`POST /generate` with `sync=true`

Response now includes:
```json
{
  "url": "/download/local_filename.pptx",
  "online_url": "https://gofile.io/d/abcdef123456",
  "slides": ["Title Slide", "Introduction", "..."]
}
```

## Test Commands

### 1. Test GoFile Service

```bash
python test_gofile_service.py
```

### 2. Test Full Integration with cURL

Generate a presentation:
```bash
curl -X POST "http://localhost:8001/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Cloud Storage Integration Test",
    "use_template": true,
    "num_slides": 5,
    "include_images": true,
    "include_diagrams": true,
    "theme": "professional"
  }'
```

Check status (replace YOUR_JOB_ID):
```bash
curl -X GET "http://localhost:8001/status/YOUR_JOB_ID"
```

### 3. Synchronous Test

```bash
curl -X POST "http://localhost:8001/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Synchronous Cloud Upload Test",
    "sync": true,
    "num_slides": 3
  }'
```

## Implementation Details

### Flow

1. The PPT is generated as before and stored in the local `results` directory
2. If GoFile integration is enabled, the system attempts to upload the file to GoFile.io
3. If the upload is successful, the online URL is included in the API response
4. The local file is still subject to cleanup after the configured lifetime

### Fallback

If the GoFile upload fails for any reason (API issues, rate limits, etc.), the system will:

1. Log the error
2. Continue functioning with just the local file
3. Return the local download URL without the online URL

This ensures the system remains functional even if the GoFile service is unavailable.

## Important Notes

- Files are uploaded to your specified folder: `bc5826dd-d9cb-4882-9da4-98e785c9b0ad`
- Account ID: `83e2e615-20ec-4cfd-a060-f4a9c7eb4397`
- Free GoFile.io accounts have limitations on API usage
- For production use, monitor usage and consider premium account if needed
- Files on GoFile are accessible via public URLs without authentication
