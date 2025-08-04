# PPT Generator Backend API Documentation

**Base URL:** `http://localhost:8000` (or your deployed URL)  
**Content-Type:** `application/json` for all POST requests  
**CORS:** Enabled for all origins

---

## 📋 Table of Contents
1. [Health Check](#health-check)
2. [PowerPoint Generation](#powerpoint-generation)
3. [Job Status Management](#job-status-management)
4. [Real-time Streaming](#real-time-streaming)
5. [Error Responses](#error-responses)
6. [Frontend Integration Guide](#frontend-integration-guide)

---

## 🏥 Health Check

### GET `/health`
Check if the backend server is running.

**Request:**
```http
GET /health
```

**Response:**
```json
{
  "status": "ok"
}
```

**Use Case:** Use this endpoint to verify server connectivity before making other API calls.

---

## 🎯 PowerPoint Generation

### POST `/generate`
Generate a PowerPoint presentation from a topic.

**Request Body:**
```json
{
  "topic": "Machine Learning Fundamentals",      // Required: string
  "username": "john_doe",                        // Optional: string (default: "anonymous")
  "sync": false,                                 // Optional: boolean (default: false)
  "use_template": true,                          // Optional: boolean (default: true)
  "num_slides": 8,                              // Optional: integer (default: 8)
  "include_images": true,                        // Optional: boolean (default: true)
  "include_diagrams": true,                      // Optional: boolean (default: true)
  "theme": "professional"                        // Optional: string (default: "professional")
}
```

#### Parameter Details:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `topic` | string | ✅ Yes | - | Main subject for the presentation |
| `username` | string | ❌ No | "anonymous" | User identifier (used in filename) |
| `sync` | boolean | ❌ No | false | Processing mode (see below) |
| `use_template` | boolean | ❌ No | true | Whether to use PowerPoint template |
| `num_slides` | integer | ❌ No | 8 | Number of slides to generate (1-20) |
| `include_images` | boolean | ❌ No | true | Fetch and include relevant images |
| `include_diagrams` | boolean | ❌ No | true | Generate process/comparison diagrams |
| `theme` | string | ❌ No | "professional" | Presentation theme |

#### Available Themes:
- `"professional"` - Business/corporate style
- `"academic"` - Academic/research style  
- `"creative"` - Creative/colorful style
- `"minimal"` - Clean/minimal style

#### Processing Modes:

**Synchronous Mode (`sync: true`):**
- Blocks until completion
- Returns complete response immediately
- Good for testing/small presentations

**Asynchronous Mode (`sync: false`):**
- Returns job ID immediately
- Use streaming or polling for progress
- Recommended for production

---

### Response Examples

#### Synchronous Response (`sync: true`):
```json
{
  "slides": [
    "Introduction to Machine Learning",
    "Types of Machine Learning", 
    "Supervised Learning",
    "Unsupervised Learning",
    "Neural Networks",
    "Applications",
    "Tools and Frameworks",
    "Conclusion"
  ],
  "username": "john_doe",
  "topic": "Machine Learning Fundamentals",
  "online_url": "https://gofile.io/d/BAEktE"
}
```

#### Asynchronous Response (`sync: false`):
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "stream_id": "660f9500-f30c-52e5-b827-557766551111", 
  "topic": "Machine Learning Fundamentals",
  "username": "john_doe",
  "status": "pending",
  "debug": {
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "stream_id": "660f9500-f30c-52e5-b827-557766551111",
    "topic": "Machine Learning Fundamentals",
    "username": "john_doe",
    "status": "pending",
    "error": null,
    "url": null,
    "use_template": true,
    "num_slides": 8,
    "include_images": true,
    "include_diagrams": true,
    "theme": "professional"
  }
}
```

---

## 📊 Job Status Management

### GET `/status/{job_id}`
Check the status of an asynchronous job.

**Path Parameters:**
- `job_id` (string): The job ID returned from `/generate`

**Response Examples:**

#### Job Pending:
```json
{
  "status": "pending",
  "stream_id": "660f9500-f30c-52e5-b827-557766551111"
}
```

#### Job Running:
```json
{
  "status": "running",
  "stream_id": "660f9500-f30c-52e5-b827-557766551111"
}
```

#### Job Completed:
```json
{
  "status": "done",
  "online_url": "https://gofile.io/d/abc123/john_doe_Machine_Learning_Fundamentals.pptx",
  "stream_id": "660f9500-f30c-52e5-b827-557766551111"
}
```

#### Job Failed:
```json
{
  "status": "error",
  "error": "LLM API failed: Rate limit exceeded",
  "stream_id": "660f9500-f30c-52e5-b827-557766551111"
}
```

---

## 🌊 Real-time Streaming

### GET `/stream/{stream_id}`
Stream real-time progress updates using Server-Sent Events (SSE).

**Path Parameters:**
- `stream_id` (string): The stream ID returned from `/generate`

**Headers:**
```http
Accept: text/event-stream
Cache-Control: no-cache
```

**Response:** Server-Sent Events stream

#### Event Types:

| Event Type | Description | Data Fields |
|------------|-------------|-------------|
| `connected` | Initial connection | `message`, `stream_id`, `job_id`, `topic`, `username` |
| `job_started` | Job initialization | `message`, `topic`, `username`, `num_slides` |
| `llm_processing` | AI content generation | `message`, `step` |
| `slides_generated` | Slides structure created | `message`, `slide_count`, `slide_titles` |
| `building_pptx` | PowerPoint creation | `message`, `step` |
| `pptx_built` | PPTX file created | `message`, `file_size` |
| `uploading` | Cloud upload started | `message`, `step` |
| `upload_complete` | Upload finished | `message`, `filename`, `download_url` |
| `job_complete` | Job finished | `message`, `download_url`, `slide_count` |
| `error` | Error occurred | `message`, `error`, `step` |

#### Example Event Stream:
```
event: connected
data: {"message": "Connected to stream", "stream_id": "660f9500...", "job_id": "550e8400...", "topic": "AI Basics", "username": "user"}

event: job_started  
data: {"message": "Starting PPT generation for 'AI Basics'", "topic": "AI Basics", "username": "user", "num_slides": 8}

event: llm_processing
data: {"message": "Calling AI to generate slide content...", "step": "content_generation"}

event: slides_generated
data: {"message": "Generated 8 slides", "slide_count": 8, "slide_titles": ["Introduction", "Key Concepts", "..."]}

event: job_complete
data: {"message": "Presentation generation completed successfully!", "download_url": "https://gofile.io/d/abc123", "slide_count": 8}
```

### GET `/stream/{stream_id}/info`
Get information about a streaming session.

**Response:**
```json
{
  "stream_id": "660f9500-f30c-52e5-b827-557766551111",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "topic": "Machine Learning Fundamentals",
  "username": "john_doe",
  "created_at": "2025-08-04T14:30:00.123456",
  "status": "running", 
  "connected": true
}
```

### GET `/streams/active`
Get all currently active streaming sessions.

**Response:**
```json
{
  "active_streams": 2,
  "streams": [
    {
      "stream_id": "660f9500-f30c-52e5-b827-557766551111",
      "job_id": "550e8400-e29b-41d4-a716-446655440000", 
      "topic": "Machine Learning Fundamentals",
      "username": "john_doe",
      "status": "running",
      "created_at": "2025-08-04T14:30:00.123456"
    },
    {
      "stream_id": "770g0600-g41d-63f6-c938-668877662222",
      "job_id": "661f0511-g41e-63f6-c938-668877662222",
      "topic": "Data Science with Python", 
      "username": "data_scientist",
      "status": "pending",
      "created_at": "2025-08-04T14:32:15.789012"
    }
  ]
}
```

---

## ❌ Error Responses

### HTTP Status Codes:
- `200` - Success
- `400` - Bad Request (invalid parameters)
- `404` - Not Found (job/stream not found)
- `500` - Internal Server Error

### Error Response Format:
```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common Errors:

#### Missing Topic (400):
```json
{
  "detail": "Missing or invalid 'topic'"
}
```

#### Job Not Found (404):
```json
{
  "detail": "Job not found"
}
```

#### Stream Not Found (404):
```json
{
  "detail": "Stream not found"
}
```

#### File Storage Error (500):
```json
{
  "detail": "File storage is not configured"
}
```

#### Upload Failure (500):
```json
{
  "detail": "File upload failed: Connection timeout"
}
```

---

## 🎨 Frontend Integration Guide

### 1. Basic Job Flow
```javascript
// 1. Start generation
const response = await fetch('/generate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    topic: 'AI Fundamentals',
    username: 'user123',
    num_slides: 10,
    sync: false  // Use async for better UX
  })
});

const { job_id, stream_id } = await response.json();

// 2. Set up real-time streaming (recommended)
const eventSource = new EventSource(`/stream/${stream_id}`);

eventSource.onopen = () => {
  console.log('Connected to stream');
};

eventSource.addEventListener('job_started', (event) => {
  const data = JSON.parse(event.data);
  updateUI('Starting generation...', 0);
});

eventSource.addEventListener('slides_generated', (event) => {
  const data = JSON.parse(event.data);
  updateUI(`Generated ${data.slide_count} slides`, 50);
  showSlidePreview(data.slide_titles);
});

eventSource.addEventListener('job_complete', (event) => {
  const data = JSON.parse(event.data);
  updateUI('Complete!', 100);
  showDownloadLink(data.download_url);
  eventSource.close();
});

eventSource.addEventListener('error', (event) => {
  const data = JSON.parse(event.data);
  showError(data.error);
  eventSource.close();
});

// 3. Fallback: Poll status if SSE not supported
// (Use this as backup for older browsers)
async function pollStatus(jobId) {
  const response = await fetch(`/status/${jobId}`);
  const data = await response.json();
  
  if (data.status === 'done') {
    showDownloadLink(data.online_url);
  } else if (data.status === 'error') {
    showError(data.error);
  } else {
    setTimeout(() => pollStatus(jobId), 2000);
  }
}
```

### 2. Real-time Progress UI
```javascript
// Progress tracking
let currentProgress = 0;

const progressMap = {
  'job_started': 5,
  'llm_processing': 20,
  'slides_generated': 40,
  'building_pptx': 60,
  'pptx_built': 70,
  'uploading': 85,
  'upload_complete': 95,
  'job_complete': 100
};

eventSource.addEventListener('message', (event) => {
  const eventType = event.type;
  const progress = progressMap[eventType] || currentProgress;
  
  updateProgressBar(progress);
  currentProgress = progress;
});
```

### 3. Error Handling
```javascript
async function generatePPT(formData) {
  try {
    const response = await fetch('/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(formData)
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Generation failed');
    }
    
    return await response.json();
    
  } catch (error) {
    if (error.message.includes('Failed to fetch')) {
      showError('Cannot connect to server. Please check your connection.');
    } else {
      showError(error.message);
    }
  }
}
```

### 4. Form Validation
```javascript
function validateForm(formData) {
  const errors = [];
  
  if (!formData.topic || formData.topic.trim().length < 3) {
    errors.push('Topic must be at least 3 characters long');
  }
  
  if (formData.num_slides < 1 || formData.num_slides > 20) {
    errors.push('Number of slides must be between 1 and 20');
  }
  
  if (!['professional', 'academic', 'creative', 'minimal'].includes(formData.theme)) {
    errors.push('Invalid theme selected');
  }
  
  return errors;
}
```

### 5. Browser Compatibility
```javascript
// Check for EventSource support
if (typeof EventSource !== 'undefined') {
  // Use real-time streaming
  setupEventSource(stream_id);
} else {
  // Fallback to polling
  pollJobStatus(job_id);
}
```

### 6. Component State Management
```javascript
// React example
const [jobState, setJobState] = useState({
  status: 'idle',        // idle, generating, complete, error
  progress: 0,
  message: '',
  slideCount: 0,
  slideTitles: [],
  downloadUrl: null,
  error: null
});

// Vue example
const jobState = reactive({
  status: 'idle',
  progress: 0,
  message: '',
  slideCount: 0,
  slideTitles: [],
  downloadUrl: null,
  error: null
});
```

---

## 🔧 Development Tips

### 1. Testing Endpoints
```bash
# Health check
curl http://localhost:8001/health

# Generate PPT (sync)
curl -X POST "http://localhost:8001/generate" \
  -H "Content-Type: application/json" \
  -d '{"topic": "Test Topic", "sync": true}'

# Stream events
curl -N -H "Accept: text/event-stream" \
  "http://localhost:8001/stream/YOUR_STREAM_ID"
```

### 2. Environment Setup
Make sure backend server is running:
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

### 3. CORS Configuration
The backend allows all origins (`*`) by default. For production, configure specific origins in the backend settings.

---

## 📝 Notes for Frontend Development

1. **File Storage**: All files are stored in cloud (GoFile.io). No local download endpoints.

2. **Filename Format**: Generated files use format: `{username}_{topic}.pptx`

3. **Rate Limiting**: Be mindful of API rate limits. Implement proper error handling.

4. **Stream Cleanup**: EventSource connections are automatically cleaned up, but close them manually when component unmounts.

5. **Offline Handling**: Implement proper offline detection and retry mechanisms.

6. **Progress Feedback**: Use the streaming events to provide rich progress feedback to users.

7. **Mobile Support**: Test SSE compatibility on mobile browsers and provide polling fallback.

This API documentation provides everything needed to build a comprehensive frontend interface for the PPT Generator!
