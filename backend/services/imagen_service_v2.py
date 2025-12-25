"""
Imagen service for Google AI Studio API with smart aspect_ratio handling.

IMPORTANT: Google AI Studio API does NOT support native aspect_ratio control.
- generate_images (Imagen 3.0) - Vertex AI only
- edit_image - Vertex AI only
- gemini-2.5-flash-image - No native aspect_ratio support

Solution: Smart prompts + intelligent crop/resize for best results.
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


def smart_crop_and_resize(image_bytes: bytes, aspect_ratio: AspectRatio) -> bytes:
    """
    Intelligently crop and resize image to target aspect ratio.
    Tries to preserve the center/important parts of the image.
    """
    
    # Target dimensions optimized for quality
    target_dimensions = {
        "16:9": (1920, 1080),   # Full HD horizontal
        "9:16": (1080, 1920),   # Full HD vertical
        "1:1": (1024, 1024)     # Square
    }
    
    target_width, target_height = target_dimensions[aspect_ratio]
    
    # Load image
    img = PILImage.open(io.BytesIO(image_bytes))
    original_width, original_height = img.size
    
    print(f"[Smart Resize] Original: {original_width}x{original_height}")
    print(f"[Smart Resize] Target: {target_width}x{target_height} ({aspect_ratio})")
    
    # Calculate aspect ratios
    target_ratio = target_width / target_height
    current_ratio = original_width / original_height
    
    # Smart crop to target aspect ratio (preserves center)
    if abs(current_ratio - target_ratio) > 0.01:
        if current_ratio > target_ratio:
            # Wider than needed - crop width (center crop)
            new_width = int(original_height * target_ratio)
            left = (original_width - new_width) // 2
            img = img.crop((left, 0, left + new_width, original_height))
            print(f"[Smart Resize] Cropped width: {original_width} → {new_width}")
        else:
            # Taller than needed - crop height (center crop)
            new_height = int(original_width / target_ratio)
            top = (original_height - new_height) // 2
            img = img.crop((0, top, original_width, top + new_height))
            print(f"[Smart Resize] Cropped height: {original_height} → {new_height}")
    
    # High-quality resize
    if img.size != (target_width, target_height):
        img = img.resize((target_width, target_height), PILImage.LANCZOS)
    
    print(f"[Smart Resize] Final: {img.size}")
    
    # Convert to bytes
    buffer = io.BytesIO()
    img.save(buffer, format='PNG', optimize=True)
    buffer.seek(0)
    return buffer.getvalue()


async def generate_image_from_prompt(
    prompt: str,
    aspect_ratio: AspectRatio = "16:9"
) -> bytes:
    """
    Generate image using gemini-2.5-flash-image (Google AI Studio API).
    
    Since native aspect_ratio is not supported, we:
    1. Add detailed aspect ratio hints to the prompt
    2. Generate image
    3. Smart crop and resize to exact dimensions
    
    Args:
        prompt: Text description of the image
        aspect_ratio: Target aspect ratio ("16:9", "9:16", "1:1")
    
    Returns:
        Image bytes (PNG format)
    """
    
    if not GOOGLE_API_KEY or not client:
        raise Exception("GOOGLE_API_KEY not set in environment")
    
    # Enhanced prompts with detailed composition guidance
    aspect_hints = {
        "16:9": "Create a HORIZONTAL WIDESCREEN composition, landscape orientation, 16:9 aspect ratio. Compose the scene with horizontal layout in mind. Wide cinematic framing.",
        "9:16": "Create a VERTICAL PORTRAIT composition, tall format, 9:16 aspect ratio. Compose the scene with vertical layout in mind. Portrait orientation, suitable for mobile/stories.",
        "1:1": "Create a SQUARE composition, 1:1 aspect ratio, equal width and height. Center the subject perfectly for square format. Balanced composition."
    }
    
    # Combine user prompt with aspect ratio guidance
    enhanced_prompt = f"{prompt}\n\nCOMPOSITION: {aspect_hints[aspect_ratio]}"
    
    print(f"[Gemini 2.5 Flash] Generating image")
    print(f"[Gemini 2.5 Flash] Target aspect ratio: {aspect_ratio}")
    print(f"[Gemini 2.5 Flash] Enhanced prompt: {enhanced_prompt[:100]}...")
    
    # Generate image
    response = client.models.generate_content(
        model='gemini-2.5-flash-image',
        contents=[enhanced_prompt],
        config=types.GenerateContentConfig(
            response_modalities=['IMAGE']
        )
    )
    
    print(f"[Gemini 2.5 Flash] Response received")
    
    # Extract image
    try:
        if not hasattr(response, 'candidates') or not response.candidates:
            raise Exception("No candidates in response")
        
        candidate = response.candidates[0]
        
        if hasattr(candidate, 'finish_reason'):
            print(f"[DEBUG] finish_reason: {candidate.finish_reason}")
        
        if not hasattr(candidate, 'content') or not candidate.content:
            error_msg = f"No content in candidate. Finish reason: {getattr(candidate, 'finish_reason', 'unknown')}"
            if hasattr(candidate, 'safety_ratings'):
                error_msg += f"\nSafety ratings: {candidate.safety_ratings}"
            raise Exception(error_msg)
        
        if not hasattr(candidate.content, 'parts') or not candidate.content.parts:
            raise Exception("No parts in content")
        
        for part in candidate.content.parts:
            if part.inline_data:
                image_bytes = part.inline_data.data
                print(f"[Gemini 2.5 Flash] Image generated! Size: {len(image_bytes)} bytes")
                
                # Smart crop and resize to target aspect ratio
                image_bytes = smart_crop_and_resize(image_bytes, aspect_ratio)
                return image_bytes
        
        raise Exception("No image found in response parts")
        
    except Exception as e:
        import traceback
        raise Exception(f"Failed to extract image: {str(e)}\n\nTraceback: {traceback.format_exc()}")


async def edit_image_with_prompt(
    image_bytes: bytes,
    prompt: str,
    aspect_ratio: AspectRatio = "16:9"
) -> bytes:
    """
    Edit existing image using gemini-2.5-flash-image (img2img).
    
    Since native aspect_ratio is not supported, we:
    1. Add aspect ratio context to the prompt
    2. Send multimodal request (prompt + image)
    3. Smart crop and resize result to exact dimensions
    
    Args:
        image_bytes: Original image bytes
        prompt: Edit instruction
        aspect_ratio: Target aspect ratio ("16:9", "9:16", "1:1")
    
    Returns:
        Edited image bytes (PNG format)
    """
    
    if not GOOGLE_API_KEY or not client:
        raise Exception("GOOGLE_API_KEY not set in environment")
    
    print(f"[Gemini Img2Img] Editing image")
    print(f"[Gemini Img2Img] Target aspect ratio: {aspect_ratio}")
    print(f"[Gemini Img2Img] Image bytes size: {len(image_bytes)}")
    
    if len(image_bytes) == 0:
        raise Exception("Image bytes are empty!")
    
    # Convert to PIL Image
    try:
        pil_image = PILImage.open(io.BytesIO(image_bytes))
        print(f"[Gemini Img2Img] Input image: {pil_image.size}, mode: {pil_image.mode}")
    except Exception as e:
        raise Exception(f"Failed to open image: {str(e)}")
    
    # Enhanced prompts with composition preservation/adjustment
    aspect_hints = {
        "16:9": "Edit the image and adjust composition for HORIZONTAL WIDESCREEN format (16:9). Maintain subject but optimize for landscape orientation.",
        "9:16": "Edit the image and adjust composition for VERTICAL PORTRAIT format (9:16). Maintain subject but optimize for portrait orientation.",
        "1:1": "Edit the image and adjust composition for SQUARE format (1:1). Maintain subject but center perfectly for square frame."
    }
    
    enhanced_prompt = f"{prompt}\n\nCOMPOSITION: {aspect_hints[aspect_ratio]}"
    
    print(f"[Gemini Img2Img] Enhanced prompt: {enhanced_prompt[:100]}...")
    
    # Create multimodal content (prompt + image)
    contents = [enhanced_prompt, pil_image]
    
    # Generate edited image
    response = client.models.generate_content(
        model='gemini-2.5-flash-image',
        contents=contents,
        config=types.GenerateContentConfig(
            response_modalities=['IMAGE']
        )
    )
    
    print(f"[Gemini Img2Img] Response received")
    
    # Extract image
    try:
        if not hasattr(response, 'candidates') or not response.candidates:
            raise Exception("No candidates in response")
        
        candidate = response.candidates[0]
        
        if hasattr(candidate, 'finish_reason'):
            print(f"[DEBUG] finish_reason: {candidate.finish_reason}")
        
        if not hasattr(candidate, 'content') or not candidate.content:
            error_msg = f"No content in candidate. Finish reason: {getattr(candidate, 'finish_reason', 'unknown')}"
            if hasattr(candidate, 'safety_ratings'):
                error_msg += f"\nSafety ratings: {candidate.safety_ratings}"
            raise Exception(error_msg)
        
        if not hasattr(candidate.content, 'parts') or not candidate.content.parts:
            raise Exception("No parts in content")
        
        for part in candidate.content.parts:
            if part.inline_data:
                image_bytes = part.inline_data.data
                print(f"[Gemini Img2Img] Image edited! Size: {len(image_bytes)} bytes")
                
                # Smart crop and resize to target aspect ratio
                image_bytes = smart_crop_and_resize(image_bytes, aspect_ratio)
                return image_bytes
        
        raise Exception("No image found in response parts")
        
    except Exception as e:
        import traceback
        raise Exception(f"Failed to extract edited image: {str(e)}\n\nTraceback: {traceback.format_exc()}")
