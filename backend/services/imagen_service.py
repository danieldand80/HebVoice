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


async def generate_image_from_prompt(
    prompt: str,
    aspect_ratio: AspectRatio = "16:9"
) -> bytes:
    """Generate image using Gemini 2.5 Flash Image (Nano Banana) - text2img"""
    
    if not GOOGLE_API_KEY or not client:
        raise Exception("GOOGLE_API_KEY not set in environment")
    
    print(f"[Nano Banana] Generating image (text2img) with prompt: {prompt}")
    print(f"[Nano Banana] Aspect ratio: {aspect_ratio}")
    
    # Use generate_content with imageConfig for native aspect_ratio support (SDK 1.56.0+)
    response = client.models.generate_content(
        model='gemini-2.5-flash-image',
        contents=[prompt],
        config=types.GenerateContentConfig(
            imageConfig=types.ImageConfig(
                aspectRatio=aspect_ratio
            )
        )
    )
    
    print(f"[Nano Banana] Response received. Type: {type(response)}")
    
    # Extract image from response
    try:
        if not hasattr(response, 'candidates') or not response.candidates:
            raise Exception("No candidates in response")
        
        candidate = response.candidates[0]
        
        if hasattr(candidate, 'finish_reason'):
            print(f"[DEBUG] finish_reason: {candidate.finish_reason}")
        if hasattr(candidate, 'safety_ratings'):
            print(f"[DEBUG] safety_ratings: {candidate.safety_ratings}")
        
        if not hasattr(candidate, 'content') or not candidate.content:
            error_msg = f"No content. Finish reason: {getattr(candidate, 'finish_reason', 'unknown')}"
            if hasattr(candidate, 'safety_ratings'):
                error_msg += f"\nSafety ratings: {candidate.safety_ratings}"
            raise Exception(error_msg)
        
        if not hasattr(candidate.content, 'parts') or not candidate.content.parts:
            raise Exception("No parts in content")
        
        for part in candidate.content.parts:
            if part.inline_data:
                image_bytes = part.inline_data.data
                print(f"[Nano Banana] Image generated! Size: {len(image_bytes)} bytes")
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
    """Edit existing image using Gemini 2.5 Flash Image (Nano Banana) - img2img
    
    This function takes an existing image and modifies it based on text prompt.
    For example: "change background to modern shop" - keeps product, changes background.
    """
    
    if not GOOGLE_API_KEY or not client:
        raise Exception("GOOGLE_API_KEY not set in environment")
    
    print(f"[Nano Banana] Editing image (img2img) with prompt: {prompt}")
    print(f"[Nano Banana] Aspect ratio: {aspect_ratio}")
    print(f"[Nano Banana] Image bytes size: {len(image_bytes)}")
    
    if len(image_bytes) == 0:
        raise Exception("Image bytes are empty!")
    
    # Convert to PIL Image
    try:
        pil_image = PILImage.open(io.BytesIO(image_bytes))
    except Exception as e:
        raise Exception(f"Failed to open image: {str(e)}")
    
    print(f"[Nano Banana] PIL Image loaded: {pil_image.size}, mode: {pil_image.mode}")
    
    # Use generate_content with image + prompt and imageConfig (SDK 1.56.0+)
    response = client.models.generate_content(
        model='gemini-2.5-flash-image',
        contents=[prompt, pil_image],
        config=types.GenerateContentConfig(
            imageConfig=types.ImageConfig(
                aspectRatio=aspect_ratio
            )
        )
    )
    
    print(f"[Nano Banana] Edit response received. Type: {type(response)}")
    
    # Extract image from response
    try:
        if not hasattr(response, 'candidates') or not response.candidates:
            raise Exception("No candidates in response")
        
        candidate = response.candidates[0]
        
        if hasattr(candidate, 'finish_reason'):
            print(f"[DEBUG] finish_reason: {candidate.finish_reason}")
        if hasattr(candidate, 'safety_ratings'):
            print(f"[DEBUG] safety_ratings: {candidate.safety_ratings}")
        
        if not hasattr(candidate, 'content') or not candidate.content:
            error_msg = f"No content. Finish reason: {getattr(candidate, 'finish_reason', 'unknown')}"
            if hasattr(candidate, 'safety_ratings'):
                error_msg += f"\nSafety ratings: {candidate.safety_ratings}"
            raise Exception(error_msg)
        
        if not hasattr(candidate.content, 'parts') or not candidate.content.parts:
            raise Exception("No parts in content")
        
        for part in candidate.content.parts:
            if part.inline_data:
                image_bytes = part.inline_data.data
                print(f"[Nano Banana] Image edited! Size: {len(image_bytes)} bytes")
                return image_bytes
        
        raise Exception("No image found in response parts")
        
    except Exception as e:
        import traceback
        raise Exception(f"Failed to extract image: {str(e)}\n\nTraceback: {traceback.format_exc()}")



