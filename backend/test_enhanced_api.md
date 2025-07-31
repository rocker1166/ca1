# Enhanced PowerPoint API Test Examples

## Server is running on: http://localhost:8001

## Basic Enhanced Presentation
```bash
curl -X POST "http://localhost:8001/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Machine Learning Fundamentals",
    "use_template": false,
    "num_slides": 10,
    "include_images": true,
    "include_diagrams": true,
    "sync": true
  }'
```

## Without Template and Enhanced Features
```bash
curl -X POST "http://localhost:8001/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Python Programming Best Practices",
    "use_template": false,
    "num_slides": 8,
    "include_images": true,
    "include_diagrams": true,
    "theme": "professional"
  }'
```

## Minimal Request (uses defaults)
```bash
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Data Science Overview",
    "use_template": false
  }'
```

## Asynchronous Processing
```bash
# 1. Start generation
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Web Development with React",
    "use_template": false,
    "num_slides": 12,
    "include_images": true,
    "include_diagrams": true
  }'

# 2. Check status (replace JOB_ID with actual ID from response)
curl -X GET "http://localhost:8000/status/YOUR_JOB_ID"

# 3. Download when ready
curl -X GET "http://localhost:8000/download/FILENAME.pptx" --output "presentation.pptx"
```

## Features Implemented:

### ✅ Enhanced Formatting
- **Bold and colored headings**: Titles are now bold with professional colors
- **Font sizing**: Different font sizes for titles (36pt), subtitles (24pt), and content (20pt)
- **Color scheme**: Professional blue/gray color palette

### ✅ Bullet Points
- **Multi-level bullets**: Support for main points and sub-points
- **Enhanced structure**: Use both simple strings and complex bullet objects
- **Proper indentation**: Different levels with appropriate spacing

### ✅ Headings & Subheadings
- **Title slides**: Dedicated title slide with subtitle support
- **Content slides**: Clear, bold headings for each slide
- **Conclusion slides**: Special formatting for summary slides

### ✅ Images
- **Automatic placement**: Images positioned on right, center, or left
- **Placeholder support**: Fallback placeholders when images fail to load
- **Multiple positions**: Configurable image positioning

### ✅ Diagrams
- **Process diagrams**: Step-by-step flow diagrams
- **Comparison diagrams**: Side-by-side comparison layouts
- **Hierarchy diagrams**: Organizational structure visuals

### ✅ Professional Styling
- **Color consistency**: Unified color scheme throughout
- **Typography**: Professional font choices and sizing
- **Layout**: Well-structured slide layouts
- **Visual hierarchy**: Clear distinction between elements

## New API Parameters:

- `num_slides`: Number of slides to generate (default: 8)
- `include_images`: Whether to include images (default: true)
- `include_diagrams`: Whether to include diagrams (default: true)
- `theme`: Presentation theme (default: "professional")
- `sync`: Synchronous processing for testing (default: false)

## Backward Compatibility:

The enhanced system maintains full backward compatibility with existing API calls while adding new features.
