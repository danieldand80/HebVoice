from vertexai.preview.vision_models import ImageGenerationModel
import vertexai
import os
import base64
import json
import tempfile
from typing import Literal

# Initialize Vertex AI
PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID")
LOCATION = os.getenv("GOOGLE_LOCATION", "us-central1")

# Handle credentials from env or file (for Railway deployment)
credentials_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
if credentials_json:
    # For Railway/cloud: use JSON from env variable
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write(credentials_json)
        credentials_path = f.name
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path

if PROJECT_ID:
    vertexai.init(project=PROJECT_ID, location=LOCATION)

AspectRatio = Literal["9:16", "16:9"]

async def generate_image_from_prompt(
    prompt: str,
    aspect_ratio: AspectRatio = "16:9"
) -> bytes:
    """Generate image using Google Imagen (Nano Banana)"""
    
    if not PROJECT_ID:
        raise Exception("GOOGLE_PROJECT_ID not set in environment")
    
    # Initialize Imagen model
    model = ImageGenerationModel.from_pretrained("imagegeneration@006")
    
    # Map aspect ratios to Imagen format
    imagen_aspect_ratio = "16:9" if aspect_ratio == "16:9" else "9:16"
    
    # Generate image
    response = model.generate_images(
        prompt=prompt,
        number_of_images=1,
        aspect_ratio=imagen_aspect_ratio,
        safety_filter_level="block_some",
        person_generation="allow_adult"
    )
    
    # Get first image
    image = response.images[0]
    
    # Convert to bytes
    image_bytes = image._image_bytes
    
    return image_bytes


async def enhance_product_image(
    image_path: str,
    prompt: str,
    aspect_ratio: AspectRatio = "16:9"
) -> bytes:
    """Enhance product image using Imagen edit capabilities"""
    
    if not PROJECT_ID:
        raise Exception("GOOGLE_PROJECT_ID not set in environment")
    
    # For MVP, we'll generate new image based on prompt
    # In future can add actual image-to-image editing
    
    enhanced_prompt = f"Professional product photography: {prompt}, high quality, clean background, commercial advertising style"
    
    return await generate_image_from_prompt(enhanced_prompt, aspect_ratio)

