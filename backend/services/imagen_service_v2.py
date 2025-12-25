"""
Imagen service with native aspect_ratio support using NEW API ONLY.
- text2img: generate_images API with aspectRatio
- img2img: edit_image API with aspectRatio
NO fallback, NO resize, NO crop.
"""

from google import genai
from google.genai import types
import os
import io
from typing import Literal
from PIL import Image as PILImage

# Initialize Google AI Studio API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if GOOGLE_API_KEY:
    client = genai.Client(api_key=GOOGLE_API_KEY)
    print("[Google AI Studio] API configured successfully")
else:
    print("WARNING: GOOGLE_API_KEY not set in environment")
    client = None

AspectRatio = Literal["9:16", "16:9", "1:1"]


async def generate_image_with_new_api(
    prompt: str,
    aspect_ratio: AspectRatio = "16:9",
    model: str = "imagen-3.0-generate-001"
) -> bytes:
    """
    Generate image using NEW generate_images API with NATIVE aspect_ratio support.
    
    This method uses the new API that properly supports aspect ratios,
    so the model knows the target proportions during generation.
    """
    
    if not GOOGLE_API_KEY or not client:
        raise Exception("GOOGLE_API_KEY not set in environment")
    
    print(f"[New API] Generating image with model: {model}")
    print(f"[New API] Prompt: {prompt}")
    print(f"[New API] Aspect ratio: {aspect_ratio}")
    
    try:
        response = client.models.generate_images(
            model=model,
            prompt=prompt,
            config=types.GenerateImagesConfig(
                aspectRatio=aspect_ratio,
                numberOfImages=1
            )
        )
        
        print(f"[New API] Response received")
        
        # Extract image
        if not response.generated_images or len(response.generated_images) == 0:
            raise Exception("No images generated in response")
        
        # Get first image
        generated_image = response.generated_images[0]
        pil_image = generated_image.image.as_image()
        
        print(f"[New API] Image generated! Size: {pil_image.size}")
        
        # Convert to bytes
        buffer = io.BytesIO()
        pil_image.save(buffer, format='PNG')
        buffer.seek(0)
        return buffer.getvalue()
        
    except Exception as e:
        print(f"[New API] Failed: {str(e)}")
        raise


async def generate_image_from_prompt(
    prompt: str,
    aspect_ratio: AspectRatio = "16:9"
) -> bytes:
    """
    Generate image with NATIVE aspect_ratio support using NEW API ONLY.
    
    Uses generate_images API with native aspectRatio parameter.
    No fallback, no resize.
    
    Args:
        prompt: Text description of the image
        aspect_ratio: Target aspect ratio ("16:9", "9:16", "1:1")
    
    Returns:
        Image bytes (PNG format)
    """
    
    # ONLY new API - no fallback
    return await generate_image_with_new_api(prompt, aspect_ratio)


async def edit_image_with_prompt(
    image_bytes: bytes,
    prompt: str,
    aspect_ratio: AspectRatio = "16:9"
) -> bytes:
    """
    Edit existing image using NEW edit_image API with NATIVE aspect_ratio support.
    
    Uses edit_image API with native aspectRatio parameter.
    No resize, no crop.
    """
    
    if not GOOGLE_API_KEY or not client:
        raise Exception("GOOGLE_API_KEY not set in environment")
    
    print(f"[New API Edit] Editing image with prompt: {prompt}")
    print(f"[New API Edit] Aspect ratio: {aspect_ratio}")
    print(f"[New API Edit] Image bytes size: {len(image_bytes)}")
    
    if len(image_bytes) == 0:
        raise Exception("Image bytes are empty!")
    
    # Convert to PIL Image
    try:
        pil_image = PILImage.open(io.BytesIO(image_bytes))
        print(f"[New API Edit] Input image: {pil_image.size}, mode: {pil_image.mode}")
    except Exception as e:
        raise Exception(f"Failed to open image: {str(e)}")
    
    try:
        # Use NEW edit_image API with reference image
        response = client.models.edit_image(
            model="imagen-3.0-generate-001",
            prompt=prompt,
            reference_images=[
                types.RawReferenceImage(
                    reference_image=pil_image,
                    reference_type="RAW"
                )
            ],
            config=types.EditImageConfig(
                aspectRatio=aspect_ratio,
                numberOfImages=1,
                editMode=types.EditMode.EDIT_MODE_PRODUCT_IMAGE  # Product image editing mode
            )
        )
        
        print(f"[New API Edit] Response received")
        
        # Extract edited image
        if not response.generated_images or len(response.generated_images) == 0:
            raise Exception("No images generated in response")
        
        # Get first image
        generated_image = response.generated_images[0]
        edited_pil_image = generated_image.image.as_image()
        
        print(f"[New API Edit] Image edited! Size: {edited_pil_image.size}")
        
        # Convert to bytes
        buffer = io.BytesIO()
        edited_pil_image.save(buffer, format='PNG')
        buffer.seek(0)
        return buffer.getvalue()
        
    except Exception as e:
        print(f"[New API Edit] Failed: {str(e)}")
        raise

