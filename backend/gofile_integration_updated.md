# GoFile Integration for Online PowerPoint Storage

This document explains the integration with GoFile.io API to store generated PowerPoint presentations online, making them accessible via public URLs with custom filenames.

## Overview

The system now supports storing generated PPT files online using the GoFile.io service. This allows:

1. Automatic uploading of generated PPTs to GoFile.io
2. Custom filename format: `[username]_[topic_name].pptx`
3. Providing a public URL for presentation download
4. Long-term storage of presentations beyond the server's temporary storage
5. Easy identification of presentations by username and topic

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

## API Usage

### Generate Endpoint

The generate endpoint now accepts a `username` parameter:

```json
{
  "topic": "Machine Learning Basics",
  "username": "john_doe",
  "use_template": true,
  "theme": "professional",
  "num_slides": 8,
  "include_images": true,
  "include_diagrams": true,
  "sync": false
}
```

### Filename Convention

Files are stored in GoFile.io using the format: `[username]_[topic_name].pptx`

Examples:
- User: "john_doe", Topic: "Machine Learning Basics" → `john_doe_Machine_Learning_Basics.pptx`
- User: "alice@company.com", Topic: "Data Science & Analytics!" → `alicecompanycom_Data_Science_Analytics.pptx`

The system automatically:
- Removes special characters from usernames and topics
- Replaces spaces with underscores
- Limits username to 20 characters and topic to 50 characters
- Uses "anonymous" as default if username is empty or invalid

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

### Generate Endpoint (sync=true)

`POST /generate` with `sync=true`

Response now includes:
```json
{
  "url": "/download/local_filename.pptx",
  "online_url": "https://gofile.io/d/abcdef123456",
  "slides": ["Title Slide", "Introduction", "..."],
  "username": "john_doe",
  "topic": "Machine Learning Basics"
}
```

## Example curl Commands

### Generate with Username (Async)
```bash
curl -X POST "http://localhost:8001/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Cloud Storage Integration",
    "username": "developer_jane",
    "use_template": true,
    "num_slides": 5,
    "include_images": true
  }'
```

### Generate with Username (Sync)
```bash
curl -X POST "http://localhost:8001/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Data Science Overview",
    "username": "data_scientist_bob",
    "sync": true,
    "num_slides": 4
  }'
```

## Implementation Details

### Flow

1. The PPT is generated as before and stored in the local `results` directory
2. A custom filename is created using the format: `[username]_[topic_name].pptx`
3. If GoFile integration is enabled, the file is uploaded to GoFile.io with the custom filename
4. If the upload is successful, the online URL is included in the API response
5. The local file is still subject to cleanup after the configured lifetime

### Fallback

If the GoFile upload fails for any reason (API issues, rate limits, etc.), the system will:

1. Log the error
2. Continue functioning with just the local file
3. Return the local download URL without the online URL

This ensures the system remains functional even if the GoFile service is unavailable.

## Testing

To test the GoFile integration with custom filenames, run:

```bash
python test_gofile_custom.py
```

This will verify:
- Connection to GoFile API
- File upload functionality with custom filenames
- Filename creation logic

## Important Notes

- Free GoFile.io accounts have limitations on API usage
- Files uploaded to GoFile.io without an account may expire sooner
- For production use, consider a premium GoFile account or alternative storage solution
- Custom filenames help organize and identify presentations by user and topic
- Special characters in usernames and topics are automatically cleaned for valid filenames
- If no username is provided, "anonymous" will be used as the default
