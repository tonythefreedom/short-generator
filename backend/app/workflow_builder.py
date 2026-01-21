import json
import random
from pathlib import Path
from typing import Optional

from .models import VideoGenerationRequest, AspectRatio


class WorkflowBuilder:
    """Build ComfyUI workflow from template"""

    def __init__(self):
        self.template_path = Path(__file__).parent / "workflows" / "wan22_t2v.json"

    def get_resolution(self, aspect_ratio: AspectRatio) -> tuple[int, int]:
        """Get resolution based on aspect ratio (optimized for 24GB unified memory)

        Note: Using smaller resolution to avoid MPS memory issues during VAE decode.
        Higher resolutions cause OOM on 24GB M4 Pro during VAE decode stage.
        """
        # Using 496x496 (must be divisible by 16 for VAE)
        return (496, 496)  # 1:1 ratio for memory efficiency

    def build_workflow(self, request: VideoGenerationRequest) -> dict:
        """Build workflow dict from request parameters"""
        with open(self.template_path, 'r') as f:
            template = f.read()

        # Get resolution
        width, height = self.get_resolution(request.aspect_ratio)

        # Generate seed if not provided
        seed = request.seed if request.seed is not None else random.randint(0, 2**32 - 1)

        # Calculate high-noise end step (first 50% of steps use high-noise model)
        high_noise_end_step = request.num_inference_steps // 2

        # Replace placeholders
        workflow_str = template
        workflow_str = workflow_str.replace("{{PROMPT}}", request.prompt.replace('"', '\\"'))
        workflow_str = workflow_str.replace("{{NEGATIVE_PROMPT}}", request.negative_prompt.replace('"', '\\"'))
        workflow_str = workflow_str.replace('"{{WIDTH}}"', str(width))
        workflow_str = workflow_str.replace('"{{HEIGHT}}"', str(height))
        workflow_str = workflow_str.replace('"{{NUM_FRAMES}}"', str(request.num_frames))
        workflow_str = workflow_str.replace('"{{SEED}}"', str(seed))
        workflow_str = workflow_str.replace('"{{STEPS}}"', str(request.num_inference_steps))
        workflow_str = workflow_str.replace('"{{GUIDANCE_SCALE}}"', str(request.guidance_scale))
        workflow_str = workflow_str.replace('"{{FPS}}"', str(float(request.fps)))
        workflow_str = workflow_str.replace('"{{HIGH_NOISE_END_STEP}}"', str(high_noise_end_step))

        workflow = json.loads(workflow_str)
        return workflow, seed


workflow_builder = WorkflowBuilder()
