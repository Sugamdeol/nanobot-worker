# nanobot-worker 🚀

A lightweight FastAPI service for offloading heavy tasks from nanobot. Optimized for Render's free tier (512MB RAM).

## Features

- 📄 **PDF Solving** - Solve JEE questions from PDFs using Gemini API
- 📸 **Screenshots** - Capture webpage screenshots
- 🎨 **AI Image Generation** - Generate images using Pollinations AI
- 🔊 **Text-to-Speech** - Generate voiceovers with ElevenLabs
- 💾 **Memory Efficient** - Optimized for 512MB RAM environments

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/solve-pdf` | POST | Solve JEE questions from PDF |
| `/screenshot` | POST | Capture webpage screenshot |
| `/generate-image` | POST | Generate AI image |
| `/voiceover` | POST | Generate text-to-speech |
| `/docs` | GET | Interactive API documentation |

## Quick Start

### Local Development

```bash
# Clone the repository
git clone https://github.com/Sugamdeol/nanobot-worker.git
cd nanobot-worker

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GEMINI_API_KEY="your_gemini_api_key"
export ELEVENLABS_API_KEY="your_elevenlabs_api_key"

# Run the server
python main.py
```

The server will start at `http://localhost:8000`

### Docker

```bash
# Build the image
docker build -t nanobot-worker .

# Run the container
docker run -p 8000:8000 \
  -e GEMINI_API_KEY="your_key" \
  -e ELEVENLABS_API_KEY="your_key" \
  nanobot-worker
```

## Deployment on Render

### Using Render Dashboard (Recommended)

1. **Create a new Web Service**
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New" → "Web Service"
   - Connect your GitHub repository

2. **Configure the service**
   - **Name**: `nanobot-worker`
   - **Runtime**: Docker
   - **Plan**: Free
   - **Branch**: `main`

3. **Set Environment Variables**
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
   SCREENSHOTONE_KEY=your_screenshotone_key_here  # Optional
   ```

4. **Deploy**
   - Click "Create Web Service"
   - Render will automatically build and deploy

### Using Render CLI

```bash
# Install Render CLI
npm install -g @renderinc/cli

# Login
render login

# Deploy using blueprint
render blueprint apply
```

## API Usage Examples

### Health Check
```bash
curl https://your-service.onrender.com/health
```

### Solve PDF Question
```bash
curl -X POST "https://your-service.onrender.com/solve-pdf" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@jee_question.pdf" \
  -F "question=Solve this physics problem step by step"
```

### Capture Screenshot
```bash
curl -X POST "https://your-service.onrender.com/screenshot" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "width": 1920, "height": 1080}' \
  --output screenshot.png
```

### Generate AI Image
```bash
curl -X POST "https://your-service.onrender.com/generate-image" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "A futuristic city with flying cars", "width": 1024, "height": 1024}' \
  --output image.png
```

### Generate Voiceover
```bash
curl -X POST "https://your-service.onrender.com/voiceover" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, this is a test voiceover.", "voice_id": "21m00Tcm4TlvDq8ikWAM"}' \
  --output voiceover.mp3
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Yes | Google Gemini API key for PDF solving |
| `ELEVENLABS_API_KEY` | Yes | ElevenLabs API key for voiceover |
| `SCREENSHOTONE_KEY` | No | ScreenshotOne API key (has free tier) |
| `PORT` | No | Server port (default: 8000) |

## Memory Optimization

This service is optimized for Render's free tier (512MB RAM):

- **Single worker** - Only one Gunicorn worker to minimize memory
- **Request limits** - Workers restart after 100 requests to free memory
- **Streaming responses** - Large files are streamed to reduce memory usage
- **Garbage collection** - Automatic cleanup after each request
- **Multi-stage Docker build** - Smaller final image

## API Keys Setup

### Google Gemini (Required for PDF solving)
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add to environment variables

### ElevenLabs (Required for voiceover)
1. Sign up at [ElevenLabs](https://elevenlabs.io)
2. Get API key from dashboard
3. Add to environment variables

### ScreenshotOne (Optional, for better screenshots)
1. Sign up at [ScreenshotOne](https://screenshotone.com)
2. Free tier: 100 screenshots/month
3. Add API key to environment variables

## Architecture

```
nanobot (main)          nanobot-worker (this service)
     │                           │
     │  1. Offload heavy task   │
     ├──────────────────────────►│
     │                           │
     │  2. Process (async)       │
     │                           ├─► Gemini API (PDF solving)
     │                           ├─► ScreenshotOne (Screenshots)
     │                           ├─► Pollinations AI (Images)
     │                           └─► ElevenLabs (Voiceover)
     │                           │
     │  3. Return result         │
     │◄──────────────────────────┤
```

## Monitoring

### Health Check
```bash
curl https://your-service.onrender.com/health
```

### Memory Cleanup (manual)
```bash
curl -X POST https://your-service.onrender.com/cleanup
```

## Troubleshooting

### Memory Issues
- The service automatically restarts workers after 100 requests
- Use `/cleanup` endpoint to force garbage collection
- For large PDFs, the service processes in chunks

### API Timeouts
- PDF solving: 60s timeout
- Screenshots: 30s timeout
- Image generation: 60s timeout
- Voiceover: 60s timeout

### Rate Limits
- Gemini: Check your Google AI Studio quota
- ElevenLabs: Depends on your plan
- Pollinations AI: Free, no limits
- ScreenshotOne: 100/month on free tier

## Development

```bash
# Install dev dependencies
pip install -r requirements.txt

# Run with auto-reload
uvicorn main:app --reload

# Run tests (when added)
pytest
```

## License

MIT License - See LICENSE file for details

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

Made with ❤️ for the nanobot ecosystem
