"""
Improved Imagen service with native aspect_ratio support using generate_images API.
Falls back to old method if new API is unavailable.
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


def resize_to_aspect_ratio(image_bytes: bytes, aspect_ratio: AspectRatio) -> bytes:
    """Resize image to match target aspect ratio by cropping and scaling (FALLBACK method)"""
    
    # Target dimensions for each aspect ratio
    target_dimensions = {
        "16:9": (1920, 1080),   # Horizontal
        "9:16": (1080, 1920),   # Vertical
        "1:1": (1024, 1024)     # Square
    }
    
    target_width, target_height = target_dimensions[aspect_ratio]
    
    # Load image
    img = PILImage.open(io.BytesIO(image_bytes))
    original_width, original_height = img.size
    
    print(f"[Resize] Original: {original_width}x{original_height} -> Target: {target_width}x{target_height}")
    
    # Calculate ratios
    target_ratio = target_width / target_height
    current_ratio = original_width / original_height
    
    # Crop to target aspect ratio first
    if abs(current_ratio - target_ratio) > 0.01:  # Need to crop
        if current_ratio > target_ratio:
            # Wider than needed - crop width
            new_width = int(original_height * target_ratio)
            left = (original_width - new_width) // 2
            img = img.crop((left, 0, left + new_width, original_height))
        else:
            # Taller than needed - crop height
            new_height = int(original_width / target_ratio)
            top = (original_height - new_height) // 2
            img = img.crop((0, top, original_width, top + new_height))
    
    # Resize to target dimensions
    if img.size != (target_width, target_height):
        img = img.resize((target_width, target_height), PILImage.LANCZOS)
    
    print(f"[Resize] Final: {img.size}")
    
    # Convert to bytes
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer.getvalue()


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


async def generate_image_with_old_api(
    prompt: str,
    aspect_ratio: AspectRatio = "16:9"
) -> bytes:
    """
    Generate image using OLD generate_content API (gemini-2.5-flash-image).
    
    This method does NOT support native aspect_ratio, so we:
    1. Add aspect ratio hints to the prompt
    2. Crop and resize after generation
    """
    
    if not GOOGLE_API_KEY or not client:
        raise Exception("GOOGLE_API_KEY not set in environment")
    
    # Add aspect ratio hints to prompt
    aspect_hints = {
        "16:9": "horizontal widescreen composition, landscape orientation, wide format",
        "9:16": "vertical portrait composition, tall format, portrait orientation",
        "1:1": "square composition, centered subject, equal width and height"
    }
    
    enhanced_prompt = f"{prompt}, {aspect_hints[aspect_ratio]}"
    
    print(f"[Old API] Generating image (gemini-2.5-flash-image)")
    print(f"[Old API] Enhanced prompt: {enhanced_prompt}")
    print(f"[Old API] Target aspect ratio: {aspect_ratio}")
    
    # Generate image from text
    response = client.models.generate_content(
        model='gemini-2.5-flash-image',
        contents=[enhanced_prompt],
        config=types.GenerateContentConfig(
            response_modalities=['IMAGE']
        )
    )
    
    print(f"[Old API] Response received")
    
    # Extract image
    try:
        if not hasattr(response, 'candidates') or not response.candidates:
            raise Exception(f"No candidates in response")
        
        candidate = response.candidates[0]
        
        if hasattr(candidate, 'finish_reason'):
            print(f"[DEBUG] finish_reason: {candidate.finish_reason}")
        
        if not hasattr(candidate, 'content') or not candidate.content:
            error_msg = f"No content in candidate. Finish reason: {getattr(candidate, 'finish_reason', 'unknown')}"
            if hasattr(candidate, 'safety_ratings'):
                error_msg += f"\nSafety ratings: {candidate.safety_ratings}"
            raise Exception(error_msg)
        
        if not hasattr(candidate.content, 'parts') or not candidate.content.parts:
            raise Exception(f"No parts in content")
        
        for part in candidate.content.parts:
            if part.inline_data:
                image_bytes = part.inline_data.data
                print(f"[Old API] Image generated! Size: {len(image_bytes)} bytes")
                
                # Apply aspect ratio through post-processing (crop + resize)
                image_bytes = resize_to_aspect_ratio(image_bytes, aspect_ratio)
                return image_bytes
        
        raise Exception(f"No image found in response parts")
        
    except Exception as e:
        import traceback
        raise Exception(f"Failed to extract image: {str(e)}\n\nTraceback: {traceback.format_exc()}")


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

