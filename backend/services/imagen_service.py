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
    
    # Generate image from text using official SDK method with image_config
    response = client.models.generate_content(
        model='gemini-2.5-flash-image',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=['IMAGE'],
            image_config=types.ImageConfig(
                aspect_ratio=aspect_ratio,
                image_size="2K"
            )
        )
    )
    
    print(f"[Nano Banana] Response received. Type: {type(response)}")
    
    # Extract image using as_image() method from documentation
    try:
        # Access parts through candidates[0].content.parts
        if not hasattr(response, 'candidates') or not response.candidates:
            raise Exception(f"No candidates in response")
        
        candidate = response.candidates[0]
        
        # Debug: log finish_reason and safety_ratings
        if hasattr(candidate, 'finish_reason'):
            print(f"[DEBUG] finish_reason: {candidate.finish_reason}")
        if hasattr(candidate, 'safety_ratings'):
            print(f"[DEBUG] safety_ratings: {candidate.safety_ratings}")
        
        if not hasattr(candidate, 'content') or not candidate.content:
            # Check if blocked by safety filters
            error_msg = f"No content in candidate. Finish reason: {getattr(candidate, 'finish_reason', 'unknown')}"
            if hasattr(candidate, 'safety_ratings'):
                error_msg += f"\nSafety ratings: {candidate.safety_ratings}"
            raise Exception(error_msg)
        
        if not hasattr(candidate.content, 'parts') or not candidate.content.parts:
            raise Exception(f"No parts in content")
        
        for part in candidate.content.parts:
            if part.inline_data:
                # Extract image bytes directly from inline_data
                image_bytes = part.inline_data.data
                
                print(f"[Nano Banana] Image generated successfully! Size: {len(image_bytes)} bytes")
                return image_bytes
        
        raise Exception(f"No image found in response parts")
        
    except Exception as e:
        import traceback
        raise Exception(f"Failed to extract image from Gemini response: {str(e)}\n\nTraceback: {traceback.format_exc()}")


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
        raise Exception("Image bytes are empty! Cannot edit empty image.")
    
    # Convert image bytes to PIL Image (according to documentation)
    try:
        pil_image = PILImage.open(io.BytesIO(image_bytes))
    except Exception as e:
        raise Exception(f"Failed to open image with PIL: {str(e)}")
    
    print(f"[Nano Banana] PIL Image loaded: {pil_image.size}, mode: {pil_image.mode}")
    
    # Create multimodal content: [prompt, image] as per documentation
    contents = [prompt, pil_image]
    
    # Generate edited image using official SDK method with image_config
    response = client.models.generate_content(
        model='gemini-2.5-flash-image',
        contents=contents,
        config=types.GenerateContentConfig(
            response_modalities=['IMAGE'],
            image_config=types.ImageConfig(
                aspect_ratio=aspect_ratio,
                image_size="2K"
            )
        )
    )
    
    print(f"[Nano Banana] Edit response received. Type: {type(response)}")
    
    # Extract image using as_image() method from documentation
    try:
        # Access parts through candidates[0].content.parts
        if not hasattr(response, 'candidates') or not response.candidates:
            raise Exception(f"No candidates in response")
        
        candidate = response.candidates[0]
        
        # Debug: log finish_reason and safety_ratings
        if hasattr(candidate, 'finish_reason'):
            print(f"[DEBUG] finish_reason: {candidate.finish_reason}")
        if hasattr(candidate, 'safety_ratings'):
            print(f"[DEBUG] safety_ratings: {candidate.safety_ratings}")
        
        if not hasattr(candidate, 'content') or not candidate.content:
            # Check if blocked by safety filters
            error_msg = f"No content in candidate. Finish reason: {getattr(candidate, 'finish_reason', 'unknown')}"
            if hasattr(candidate, 'safety_ratings'):
                error_msg += f"\nSafety ratings: {candidate.safety_ratings}"
            raise Exception(error_msg)
        
        if not hasattr(candidate.content, 'parts') or not candidate.content.parts:
            raise Exception(f"No parts in content")
        
        for part in candidate.content.parts:
            if part.inline_data:
                # Extract image bytes directly from inline_data
                image_bytes = part.inline_data.data
                
                print(f"[Nano Banana] Image edited successfully! Size: {len(image_bytes)} bytes")
                return image_bytes
        
        raise Exception(f"No image found in response parts")
        
    except Exception as e:
        import traceback
        raise Exception(f"Failed to extract edited image from Gemini response: {str(e)}\n\nTraceback: {traceback.format_exc()}")



