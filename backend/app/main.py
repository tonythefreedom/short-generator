import os
import asyncio
from pathlib import Path
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .models import (
    VideoGenerationRequest,
    VideoGenerationResponse,
    GenerationStatus,
)
from .comfyui_client import comfyui_client
from .workflow_builder import workflow_builder


# Global status tracking
current_status = GenerationStatus(status="idle", progress=0.0, message="Ready")
_status_lock = asyncio.Lock()


async def update_status(status: str, progress: float = 0.0, message: str = ""):
    global current_status
    async with _status_lock:
        current_status = GenerationStatus(status=status, progress=progress, message=message)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    yield
    # Shutdown
    pass


app = FastAPI(
    title="Short Video Generator",
    description="Generate short videos using WAN 2.2 model via ComfyUI",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health_check():
    comfyui_available = await comfyui_client.is_available()
    return {
        "status": "healthy",
        "comfyui_available": comfyui_available,
        "model_loaded": comfyui_available  # ComfyUI loads models on demand
    }


@app.get("/api/status")
async def get_status():
    return current_status


@app.post("/api/load-model")
async def load_model():
    """Check if ComfyUI is available (models load on demand)"""
    comfyui_available = await comfyui_client.is_available()

    if comfyui_available:
        await update_status("idle", 1.0, "ComfyUI is ready. Models will load on first generation.")
        return {"message": "ComfyUI is ready"}
    else:
        await update_status("error", 0.0, "ComfyUI is not running. Please start ComfyUI first.")
        raise HTTPException(
            status_code=503,
            detail="ComfyUI is not running. Start it with: cd comfyui && python main.py --listen"
        )


@app.post("/api/unload-model")
async def unload_model():
    """ComfyUI manages model memory automatically"""
    await update_status("idle", 0.0, "Ready")
    return {"message": "Status reset. ComfyUI manages models automatically."}


@app.post("/api/generate", response_model=VideoGenerationResponse)
async def generate_video(request: VideoGenerationRequest, background_tasks: BackgroundTasks):
    # Check ComfyUI availability
    if not await comfyui_client.is_available():
        raise HTTPException(
            status_code=503,
            detail="ComfyUI is not running. Start it with: cd comfyui && python main.py --listen"
        )

    if current_status.status == "generating":
        raise HTTPException(status_code=400, detail="Generation already in progress")

    # Build workflow
    workflow, seed = workflow_builder.build_workflow(request)

    async def generate_task():
        try:
            await update_status("generating", 0.1, "Queuing workflow...")

            # Queue the workflow
            prompt_id = await comfyui_client.queue_prompt(workflow)

            await update_status("generating", 0.2, "Generating video (this may take a while)...")

            # Wait for completion with progress updates
            def progress_cb(progress: float):
                asyncio.create_task(
                    update_status("generating", 0.2 + progress * 0.7, f"Generating... {int(progress * 100)}%")
                )

            history = await comfyui_client.wait_for_completion(prompt_id, progress_cb, timeout=600)

            await update_status("generating", 0.95, "Downloading video...")

            # Get output video URL
            video_url = await comfyui_client.get_output_video(history)

            if video_url:
                # Download to local outputs folder
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"video_{timestamp}_{seed}.mp4"
                output_path = settings.output_dir / output_filename

                await comfyui_client.download_video(video_url, output_path)

                await update_status("completed", 1.0, f"Video generated successfully! Seed: {seed}")
            else:
                await update_status("error", 0.0, "No video output found in workflow result")

        except Exception as e:
            await update_status("error", 0.0, f"Generation failed: {str(e)}")

    background_tasks.add_task(generate_task)

    return VideoGenerationResponse(
        success=True,
        video_url=None,
        message="Generation started",
        seed_used=seed
    )


@app.get("/api/videos")
async def list_videos():
    """List all generated videos"""
    videos = []
    for file in settings.output_dir.glob("*.mp4"):
        videos.append({
            "name": file.name,
            "url": f"/outputs/{file.name}",
            "created": file.stat().st_mtime
        })
    videos.sort(key=lambda x: x["created"], reverse=True)
    return {"videos": videos}


@app.delete("/api/videos/{filename}")
async def delete_video(filename: str):
    """Delete a generated video"""
    video_path = settings.output_dir / filename
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video not found")

    video_path.unlink()
    return {"message": "Video deleted"}


# Mount outputs directory
app.mount("/outputs", StaticFiles(directory=str(settings.output_dir)), name="outputs")

# Serve React static files (built frontend)
frontend_build_path = Path(__file__).parent.parent.parent / "frontend" / "dist"
if frontend_build_path.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_build_path / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Serve index.html for SPA routing
        index_path = frontend_build_path / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        raise HTTPException(status_code=404, detail="Frontend not built")
else:
    @app.get("/")
    async def root():
        return {"message": "Frontend not built. Run 'npm run build' in frontend directory."}
