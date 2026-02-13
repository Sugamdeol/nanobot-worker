"""
nanobot-worker - A lightweight FastAPI service for offloading heavy tasks.
Optimized for Render's free tier (512MB RAM).
"""

import os
import io
import gc
import base64
import tempfile
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, HttpUrl
import httpx

# Configure for memory efficiency
os.environ["PYTHONUNBUFFERED"] = "1"
os.environ["MALLOC_TRIM_THRESHOLD_"] = "0"

# API Keys from environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY", "")  # Optional, can work without

# Request/Response Models
class ScreenshotRequest(BaseModel):
    url: HttpUrl
    width: int = 1920
    height: int = 1080
    full_page: bool = False

class ImageGenerationRequest(BaseModel):
    prompt: str
    width: int = 1024
    height: int = 1024
    seed: Optional[int] = None
    model: str = "flux"

class VoiceoverRequest(BaseModel):
    text: str
    voice_id: Optional[str] = "21m00Tcm4TlvDq8ikWAM"  # Default: Rachel
    model_id: str = "eleven_multilingual_v2"

class PDFSolveRequest(BaseModel):
    question: str
    max_tokens: int = 2048
    temperature: float = 0.7


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle with memory cleanup."""
    # Startup
    print("🚀 nanobot-worker starting up...")
    yield
    # Shutdown
    print("🛑 nanobot-worker shutting down...")
    gc.collect()


app = FastAPI(
    title="nanobot-worker",
    description="Heavy task offloading service for nanobot",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "nanobot-worker",
        "version": "1.0.0",
        "endpoints": [
            "/solve-pdf",
            "/screenshot",
            "/generate-image",
            "/voiceover",
            "/health"
        ]
    }


@app.post("/solve-pdf")
async def solve_pdf(
    file: UploadFile = File(...),
    question: str = Form("Solve this JEE question step by step."),
    max_tokens: int = Form(2048),
    temperature: float = Form(0.7)
):
    """
    Solve JEE questions from PDF using Gemini API.
    
    - **file**: PDF file containing the question
    - **question**: Specific question or solving instructions
    - **max_tokens**: Maximum response tokens
    - **temperature**: Creativity level (0.0-1.0)
    """
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured")
    
    if not file.content_type or not file.content_type.startswith("application/pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    try:
        # Read PDF in chunks to save memory
        contents = await file.read()
        
        # Encode to base64
        pdf_base64 = base64.b64encode(contents).decode('utf-8')
        
        # Call Gemini API
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}",
                json={
                    "contents": [{
                        "parts": [
                            {"text": question},
                            {
                                "inline_data": {
                                    "mime_type": "application/pdf",
                                    "data": pdf_base64
                                }
                            }
                        ]
                    }],
                    "generationConfig": {
                        "maxOutputTokens": max_tokens,
                        "temperature": temperature
                    }
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=500, 
                    detail=f"Gemini API error: {response.text}"
                )
            
            result = response.json()
            
            # Extract text response
            if "candidates" in result and len(result["candidates"]) > 0:
                candidate = result["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    text_parts = [
                        part["text"] 
                        for part in candidate["content"]["parts"] 
                        if "text" in part
                    ]
                    answer = "\n".join(text_parts)
                else:
                    answer = "No answer generated"
            else:
                answer = "No response from Gemini"
            
            return {
                "success": True,
                "answer": answer,
                "model": "gemini-1.5-flash",
                "tokens_used": result.get("usageMetadata", {}).get("totalTokenCount", 0)
            }
    
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Gemini API timeout")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")
    finally:
        # Clean up memory
        gc.collect()


@app.post("/screenshot")
async def capture_screenshot(request: ScreenshotRequest):
    """
    Capture webpage screenshot using ScreenshotOne API (free tier available).
    Falls back to screenshotapi.net if no API key.
    
    - **url**: Target webpage URL
    - **width**: Viewport width (default: 1920)
    - **height**: Viewport height (default: 1080)
    - **full_page**: Capture full page (default: False)
    """
    try:
        # Using ScreenshotOne (free tier: 100 screenshots/month)
        screenshot_key = os.getenv("SCREENSHOTONE_KEY", "")
        
        if screenshot_key:
            api_url = "https://api.screenshotone.com/take"
            params = {
                "access_key": screenshot_key,
                "url": str(request.url),
                "viewport_width": request.width,
                "viewport_height": request.height,
                "full_page": request.full_page,
                "format": "png"
            }
        else:
            # Fallback: screenshotapi.net (no key required, rate limited)
            api_url = f"https://shot.screenshotapi.net/screenshot"
            params = {
                "token": "DEMO_TOKEN",  # Demo token for testing
                "url": str(request.url),
                "width": request.width,
                "height": request.height,
                "output": "image",
                "file_type": "png"
            }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(api_url, params=params)
            
            if response.status_code == 200:
                # Return image directly
                return StreamingResponse(
                    io.BytesIO(response.content),
                    media_type="image/png",
                    headers={"Content-Disposition": "attachment; filename=screenshot.png"}
                )
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Screenshot service error: {response.text}"
                )
    
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Screenshot service timeout")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Screenshot error: {str(e)}")


@app.post("/generate-image")
async def generate_image(request: ImageGenerationRequest):
    """
    Generate AI images using Pollinations AI (free, no API key needed).
    
    - **prompt**: Image description
    - **width**: Image width (default: 1024)
    - **height**: Image height (default: 1024)
    - **seed**: Random seed for reproducibility
    - **model**: Model to use (flux, turbo, etc.)
    """
    try:
        # Build Pollinations URL
        encoded_prompt = request.prompt.replace(" ", "%20")
        seed_param = f"&seed={request.seed}" if request.seed else ""
        
        image_url = (
            f"https://image.pollinations.ai/prompt/{encoded_prompt}"
            f"?width={request.width}&height={request.height}&nologo=true{seed_param}"
        )
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(image_url)
            
            if response.status_code == 200:
                return StreamingResponse(
                    io.BytesIO(response.content),
                    media_type="image/png",
                    headers={"Content-Disposition": f"attachment; filename=generated_image.png"}
                )
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Image generation error: {response.status_code}"
                )
    
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Image generation timeout")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image generation error: {str(e)}")


@app.post("/voiceover")
async def generate_voiceover(request: VoiceoverRequest):
    """
    Generate text-to-speech using ElevenLabs API.
    
    - **text**: Text to convert to speech
    - **voice_id**: ElevenLabs voice ID (default: Rachel)
    - **model_id**: Model to use (default: eleven_multilingual_v2)
    """
    if not ELEVENLABS_API_KEY:
        raise HTTPException(status_code=500, detail="ELEVENLABS_API_KEY not configured")
    
    if len(request.text) > 5000:
        raise HTTPException(status_code=400, detail="Text too long (max 5000 chars)")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{request.voice_id}",
                headers={
                    "xi-api-key": ELEVENLABS_API_KEY,
                    "Content-Type": "application/json"
                },
                json={
                    "text": request.text,
                    "model_id": request.model_id,
                    "voice_settings": {
                        "stability": 0.5,
                        "similarity_boost": 0.75
                    }
                }
            )
            
            if response.status_code == 200:
                return StreamingResponse(
                    io.BytesIO(response.content),
                    media_type="audio/mpeg",
                    headers={"Content-Disposition": "attachment; filename=voiceover.mp3"}
                )
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"ElevenLabs API error: {response.text}"
                )
    
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Voiceover generation timeout")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Voiceover error: {str(e)}")


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "service": "nanobot-worker",
        "version": "1.0.0",
        "description": "Heavy task offloading service for nanobot",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "solve_pdf": {"method": "POST", "path": "/solve-pdf"},
            "screenshot": {"method": "POST", "path": "/screenshot"},
            "generate_image": {"method": "POST", "path": "/generate-image"},
            "voiceover": {"method": "POST", "path": "/voiceover"}
        }
    }


# Memory cleanup endpoint for Render's free tier
@app.post("/cleanup")
async def cleanup_memory():
    """Force garbage collection to free memory."""
    gc.collect()
    import psutil
    process = psutil.Process()
    memory_info = process.memory_info()
    return {
        "success": True,
        "memory_mb": round(memory_info.rss / 1024 / 1024, 2),
        "message": "Garbage collection completed"
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        workers=1,  # Single worker for memory efficiency
        limit_max_requests=100,  # Restart worker after 100 requests to free memory
    )
