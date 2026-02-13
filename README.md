# Nanobot Worker

A lightweight Flask-based microservice for AI-powered tasks including JEE question solving, webpage screenshots, AI image generation, and text-to-speech.

## Environment Variables

The following environment variables are required:

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Yes (for PDF solving) | Google Gemini API key for JEE question solving |
| `POLLINATIONS_API_KEY` | Yes (for image/voice) | Pollinations API key for image generation and TTS |

## Deployment Instructions

### Deploy to Render

1. Fork or push this repository to GitHub
2. Connect your GitHub account to [Render](https://render.com)
3. Click "New +" → "Web Service"
4. Select this repository
5. Choose "Docker" as the runtime
6. Add environment variables in the dashboard:
   - `GEMINI_API_KEY`: Your Google Gemini API key
   - `POLLINATIONS_API_KEY`: Your Pollinations API key
7. Click "Create Web Service"

### Local Development

```bash
# Clone the repository
git clone https://github.com/Sugamdeol/nanobot-worker.git
cd nanobot-worker

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Set environment variables
export GEMINI_API_KEY=your_gemini_key
export POLLINATIONS_API_KEY=your_pollinations_key

# Run the app
python main.py
```

## API Endpoints

### Health Check
```
GET /health
```
Returns service health status.

**Response:**
```json
{
  "status": "healthy",
  "service": "nanobot-worker"
}
```

### Solve JEE Questions from PDF
```
POST /solve-pdf
Content-Type: multipart/form-data
```
Upload a PDF containing JEE questions and get AI-generated solutions.

**Parameters:**
- `file` (required): PDF file containing JEE questions

**Response:**
```json
{
  "solution": "Step-by-step solution text...",
  "status": "success"
}
```

### Capture Webpage Screenshot
```
POST /screenshot
Content-Type: application/json
```
Capture a screenshot of any webpage.

**Request Body:**
```json
{
  "url": "https://example.com",
  "width": 1280,
  "height": 720,
  "full_page": false
}
```

**Response:**
```json
{
  "screenshot": "base64_encoded_png",
  "format": "png",
  "status": "success"
}
```

### Generate AI Image
```
POST /generate-image
Content-Type: application/json
```
Generate images using AI.

**Request Body:**
```json
{
  "prompt": "A futuristic city at sunset",
  "width": 1024,
  "height": 1024,
  "seed": 42
}
```

**Response:**
```json
{
  "image": "base64_encoded_png",
  "format": "png",
  "status": "success"
}
```

### Text-to-Speech
```
POST /voiceover
Content-Type: application/json
```
Convert text to speech.

**Request Body:**
```json
{
  "text": "Hello, this is a test message",
  "voice": "alloy"
}
```

**Response:**
```json
{
  "audio": "base64_encoded_mp3",
  "format": "mp3",
  "status": "success"
}
```

## Memory Optimization

This service is optimized to run within 512MB RAM limits:
- Single worker process with threaded handling
- PDF processing uses streaming to minimize memory usage
- Browser instances are properly closed after screenshots
- Request limits and jitter to prevent memory leaks

## License

MIT License
