"""
Imagen service with NATIVE aspect_ratio support using Vertex AI.
Perfect quality, no crop/resize needed.
"""

from google import genai
from google.genai import types
import os
import io
from typing import Literal
from PIL import Image as PILImage

# Initialize Vertex AI client
PROJECT_ID = os.getenv("VERTEX_PROJECT_ID")  # e.g., "lironhebvoice"
LOCATION = os.getenv("VERTEX_LOCATION", "us-central1")  # or "europe-west1"

if PROJECT_ID:
    # Vertex AI client initialization
    client = genai.Client(
        vertexai=True,
        project=PROJECT_ID,
        location=LOCATION
    )
    print(f"[Vertex AI] Initialized: project={PROJECT_ID}, location={LOCATION}")
else:
    print("WARNING: VERTEX_PROJECT_ID not set in environment")
    client = None

AspectRatio = Literal["9:16", "16:9", "1:1"]


async def generate_image_from_prompt(
    prompt: str,
    aspect_ratio: AspectRatio = "16:9"
) -> bytes:
    """
    Generate image using Vertex AI Imagen 3.0 with NATIVE aspect_ratio support.
    
    Model knows target proportions during generation → perfect composition.
    No crop, no resize needed.
    
    Args:
        prompt: Text description of the image
        aspect_ratio: Target aspect ratio ("16:9", "9:16", "1:1")
    
    Returns:
        Image bytes (PNG format) with EXACT aspect ratio
    """
    
    if not PROJECT_ID or not client:
        raise Exception("VERTEX_PROJECT_ID not set in environment")
    
    print(f"[Vertex AI Imagen] Generating image")
    print(f"[Vertex AI Imagen] Prompt: {prompt}")
    print(f"[Vertex AI Imagen] Aspect ratio: {aspect_ratio} (NATIVE)")
    
    try:
        # Use Vertex AI's generate_images API with native aspect_ratio
        response = client.models.generate_images(
            model="imagen-3.0-generate-001",
            prompt=prompt,
            config=types.GenerateImagesConfig(
                aspectRatio=aspect_ratio,
                numberOfImages=1,
                # Optional advanced parameters:
                # negativePrompt="blurry, low quality, distorted",
                # guidanceScale=7.0,  # How closely to follow prompt (1-20)
                # seed=42,  # For reproducibility
            )
        )
        
        print(f"[Vertex AI Imagen] Response received")
        
        # Extract image
        if not response.generated_images or len(response.generated_images) == 0:
            raise Exception("No images generated in response")
        
        # Get first image
        generated_image = response.generated_images[0]
        pil_image = generated_image.image.as_image()
        
        print(f"[Vertex AI Imagen] ✨ Image generated! Size: {pil_image.size}")
        print(f"[Vertex AI Imagen] ✨ Perfect {aspect_ratio} composition - no resize needed!")
        
        # Convert to bytes
        buffer = io.BytesIO()
        pil_image.save(buffer, format='PNG', optimize=True)
        buffer.seek(0)
        return buffer.getvalue()
        
    except Exception as e:
        print(f"[Vertex AI Imagen] ❌ Failed: {str(e)}")
        raise


async def edit_image_with_prompt(
    image_bytes: bytes,
    prompt: str,
    aspect_ratio: AspectRatio = "16:9"
) -> bytes:
    """
    Edit existing image using Vertex AI Imagen 3.0 with NATIVE aspect_ratio support.
    
    Perfect img2img editing with aspect ratio control.
    No crop, no resize needed.
    
    Args:
        image_bytes: Original image bytes
        prompt: Edit instruction
        aspect_ratio: Target aspect ratio ("16:9", "9:16", "1:1")
    
    Returns:
        Edited image bytes (PNG format) with EXACT aspect ratio
    """
    
    if not PROJECT_ID or not client:
        raise Exception("VERTEX_PROJECT_ID not set in environment")
    
    print(f"[Vertex AI Edit] Editing image")
    print(f"[Vertex AI Edit] Prompt: {prompt}")
    print(f"[Vertex AI Edit] Aspect ratio: {aspect_ratio} (NATIVE)")
    print(f"[Vertex AI Edit] Image bytes size: {len(image_bytes)}")
    
    if len(image_bytes) == 0:
        raise Exception("Image bytes are empty!")
    
    # Convert to PIL Image
    try:
        pil_image = PILImage.open(io.BytesIO(image_bytes))
        print(f"[Vertex AI Edit] Input image: {pil_image.size}, mode: {pil_image.mode}")
    except Exception as e:
        raise Exception(f"Failed to open image: {str(e)}")
    
    try:
        # Use Vertex AI's edit_image API with native aspect_ratio
        response = client.models.edit_image(
            model="imagen-3.0-generate-001",
            prompt=prompt,
            reference_images=[
                types.RawReferenceImage(
                    referenceImage=pil_image
                )
            ],
            config=types.EditImageConfig(
                aspectRatio=aspect_ratio,
                numberOfImages=1,
                editMode=types.EditMode.EDIT_MODE_PRODUCT_IMAGE,  # Perfect for products!
                # Optional:
                # negativePrompt="blur, distortion",
                # guidanceScale=7.0,
            )
        )
        
        print(f"[Vertex AI Edit] Response received")
        
        # Extract edited image
        if not response.generated_images or len(response.generated_images) == 0:
            raise Exception("No images generated in response")
        
        # Get first image
        generated_image = response.generated_images[0]
        edited_pil_image = generated_image.image.as_image()
        
        print(f"[Vertex AI Edit] ✨ Image edited! Size: {edited_pil_image.size}")
        print(f"[Vertex AI Edit] ✨ Perfect {aspect_ratio} composition - no resize needed!")
        
        # Convert to bytes
        buffer = io.BytesIO()
        edited_pil_image.save(buffer, format='PNG', optimize=True)
        buffer.seek(0)
        return buffer.getvalue()
        
    except Exception as e:
        print(f"[Vertex AI Edit] ❌ Failed: {str(e)}")
        raise

