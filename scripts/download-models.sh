#!/bin/bash
# Download WAN 2.2 GGUF models for ComfyUI

set -e

cd "$(dirname "$0")/../comfyui"

source venv/bin/activate

echo "=== Downloading WAN 2.2 GGUF Models ==="
echo "This will download approximately 20GB of model files."
echo ""

# Download HighNoise model (Q4_K_S - ~8.75GB)
echo "Downloading HighNoise model (Q4_K_S)..."
huggingface-cli download QuantStack/Wan2.2-T2V-A14B-GGUF \
    --include "HighNoise/*Q4_K_S*" \
    --local-dir ./models/diffusion_models

# Download LowNoise model (Q4_K_S - ~8.75GB)
echo "Downloading LowNoise model (Q4_K_S)..."
huggingface-cli download QuantStack/Wan2.2-T2V-A14B-GGUF \
    --include "LowNoise/*Q4_K_S*" \
    --local-dir ./models/diffusion_models

# Download VAE
echo "Downloading VAE..."
huggingface-cli download QuantStack/Wan2.2-T2V-A14B-GGUF \
    --include "VAE/*" \
    --local-dir ./models/vae

# Download Text Encoder (UMT5-XXL)
echo "Downloading Text Encoder..."
huggingface-cli download Comfy-Org/Wan_2.1_ComfyUI_repackaged \
    --include "split_files/text_encoders/*" \
    --local-dir ./models/text_encoders

echo ""
echo "=== Download Complete ==="
echo ""
echo "Models downloaded to:"
echo "  - comfyui/models/diffusion_models/"
echo "  - comfyui/models/vae/"
echo "  - comfyui/models/text_encoders/"
