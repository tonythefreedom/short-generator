from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # Model settings (WAN 2.1 1.3B - lightweight model, ~8GB VRAM)
    model_id: str = "Wan-AI/Wan2.1-T2V-1.3B-Diffusers"

    # Output settings
    output_dir: Path = Path("outputs")

    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000

    # Device settings
    device: str = "cuda"  # or "mps" for Mac, "cpu" for CPU

    class Config:
        env_file = ".env"


settings = Settings()

# Ensure output directory exists
settings.output_dir.mkdir(parents=True, exist_ok=True)
