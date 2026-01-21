import torch
import random
from pathlib import Path
from datetime import datetime
from typing import Optional, Callable
from diffusers import WanPipeline
from diffusers.utils import export_to_video

from .config import settings
from .models import AspectRatio, VideoGenerationRequest


class VideoGenerator:
    def __init__(self):
        self.pipe = None
        self.is_loaded = False
        self.is_loading = False
        self.device = None

    def get_resolution(self, aspect_ratio: AspectRatio) -> tuple[int, int]:
        """Get resolution based on aspect ratio
        WAN 2.1 1.3B performs best at 480P resolution
        """
        if aspect_ratio == AspectRatio.PORTRAIT:
            return (480, 832)  # 9:16 ratio at 480P
        else:
            return (832, 480)  # 16:9 ratio at 480P

    def load_model(self, progress_callback: Optional[Callable] = None):
        """Load the WAN 2.1 model"""
        if self.is_loaded:
            return

        self.is_loading = True

        try:
            if progress_callback:
                progress_callback("Detecting device...")

            # Determine device
            if torch.cuda.is_available():
                self.device = "cuda"
                dtype = torch.bfloat16
            elif torch.backends.mps.is_available():
                self.device = "mps"
                dtype = torch.float32  # MPS works better with float32
            else:
                self.device = "cpu"
                dtype = torch.float32

            if progress_callback:
                progress_callback(f"Using device: {self.device}, dtype: {dtype}")

            if progress_callback:
                progress_callback("Loading WAN 2.1 pipeline (this may take a while)...")

            # Load pipeline directly
            self.pipe = WanPipeline.from_pretrained(
                settings.model_id,
                torch_dtype=dtype
            )

            if progress_callback:
                progress_callback("Moving model to device...")

            # Enable memory optimizations based on device
            if self.device == "cuda":
                self.pipe.enable_model_cpu_offload()
            else:
                self.pipe = self.pipe.to(self.device)

            self.is_loaded = True
            self.is_loading = False

            if progress_callback:
                progress_callback("Model loaded successfully!")

        except Exception as e:
            self.is_loading = False
            raise RuntimeError(f"Failed to load model: {str(e)}")

    def generate_video(
        self,
        request: VideoGenerationRequest,
        progress_callback: Optional[Callable] = None
    ) -> tuple[str, int]:
        """Generate a video from the request parameters"""

        if not self.is_loaded:
            raise RuntimeError("Model not loaded. Please load the model first.")

        # Set seed
        seed = request.seed if request.seed is not None else random.randint(0, 2**32 - 1)

        # Create generator on appropriate device
        if self.device == "cuda":
            gen_device = "cuda"
        elif self.device == "mps":
            gen_device = "cpu"  # MPS generator should be on CPU
        else:
            gen_device = "cpu"

        generator = torch.Generator(device=gen_device).manual_seed(seed)

        # Get resolution
        width, height = self.get_resolution(request.aspect_ratio)

        if progress_callback:
            progress_callback(f"Generating video ({width}x{height}, {request.num_frames} frames)...")

        # Generate video with WAN 2.1 recommended parameters
        output = self.pipe(
            prompt=request.prompt,
            negative_prompt=request.negative_prompt,
            height=height,
            width=width,
            num_frames=request.num_frames,
            num_inference_steps=request.num_inference_steps,
            guidance_scale=request.guidance_scale,
            generator=generator,
        )

        # Export video
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"video_{timestamp}_{seed}.mp4"
        output_path = settings.output_dir / output_filename

        if progress_callback:
            progress_callback("Exporting video...")

        export_to_video(output.frames[0], str(output_path), fps=request.fps)

        return str(output_path), seed

    def unload_model(self):
        """Unload the model to free memory"""
        if self.pipe is not None:
            del self.pipe
            self.pipe = None

        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        if torch.backends.mps.is_available():
            torch.mps.empty_cache()

        self.is_loaded = False
        self.device = None


# Global generator instance
generator = VideoGenerator()
