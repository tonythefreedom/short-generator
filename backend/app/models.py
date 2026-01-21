from pydantic import BaseModel, Field
from typing import Optional, Literal
from enum import Enum


class AspectRatio(str, Enum):
    PORTRAIT = "portrait"  # 9:16 (1080x1920)
    LANDSCAPE = "landscape"  # 16:9 (1920x1080)


class VideoGenerationRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2000, description="Text prompt for video generation")
    negative_prompt: str = Field(
        default="low quality, blurry, distorted, deformed, ugly, bad anatomy",
        description="Negative prompt to avoid unwanted elements"
    )
    aspect_ratio: AspectRatio = Field(default=AspectRatio.PORTRAIT, description="Video aspect ratio")
    num_frames: int = Field(default=81, ge=17, le=129, description="Number of frames (must be 4k+1, e.g., 17, 33, 49, 65, 81)")
    num_inference_steps: int = Field(default=30, ge=10, le=100, description="Number of denoising steps")
    guidance_scale: float = Field(default=5.0, ge=1.0, le=20.0, description="Classifier-free guidance scale")
    seed: Optional[int] = Field(default=None, description="Random seed for reproducibility")
    fps: int = Field(default=16, ge=8, le=30, description="Frames per second for output video")


class VideoGenerationResponse(BaseModel):
    success: bool
    video_url: Optional[str] = None
    message: str
    seed_used: int


class GenerationStatus(BaseModel):
    status: Literal["idle", "loading", "generating", "completed", "error"]
    progress: float = 0.0
    message: str = ""
