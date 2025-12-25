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
    """Resize image to match target aspect ratio"""
    
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
    
    print(f"[Resize] Original size: {original_width}x{original_height}")
    print(f"[Resize] Target size: {target_width}x{target_height}")
    
    # Calculate target aspect ratio
    target_ratio = target_width / target_height
    current_ratio = original_width / original_height
    
    # Crop to target aspect ratio first, then resize
    if current_ratio > target_ratio:
        # Image is wider than target, crop width
        new_width = int(original_height * target_ratio)
        left = (original_width - new_width) // 2
        img = img.crop((left, 0, left + new_width, original_height))
    elif current_ratio < target_ratio:
        # Image is taller than target, crop height
        new_height = int(original_width / target_ratio)
        top = (original_height - new_height) // 2
        img = img.crop((0, top, original_width, top + new_height))
    
    # Resize to target dimensions
    img = img.resize((target_width, target_height), PILImage.LANCZOS)
    
    print(f"[Resize] Final size: {img.size}")
    
    # Convert back to bytes
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer.getvalue()


async def generate_image_from_prompt(
    prompt: str,
    aspect_ratio: AspectRatio = "16:9"
) -> bytes:
    """Generate image using Gemini 2.5 Flash Image (Nano Banana) - text2img"""
    
    if not GOOGLE_API_KEY or not client:
        raise Exception("GOOGLE_API_KEY not set in environment")
    
    print(f"[Nano Banana] Generating image (text2img) with prompt: {prompt}")
    print(f"[Nano Banana] Aspect ratio: {aspect_ratio}")
    
    # Generate image from text using official SDK method
    response = client.models.generate_content(
        model='gemini-2.5-flash-image',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=['IMAGE']
        )
    )
    
    print(f"[Nano Banana] Response received. Type: {type(response)}")
    
    # Extract image using as_image() method from documentation
    try:
        # Access parts through candidates[0].content.parts
        if not hasattr(response, 'candidates') or not response.candidates:
            raise Exception(f"No candidates in response")
        
        candidate = response.candidates[0]
        if not hasattr(candidate, 'content') or not candidate.content:
            raise Exception(f"No content in candidate")
        
        if not hasattr(candidate.content, 'parts') or not candidate.content.parts:
            raise Exception(f"No parts in content")
        
        for part in candidate.content.parts:
            if part.inline_data:
                # Extract image bytes directly from inline_data
                image_bytes = part.inline_data.data
                
                print(f"[Nano Banana] Image generated successfully! Size: {len(image_bytes)} bytes")
                
                # Resize to target aspect ratio
                image_bytes = resize_to_aspect_ratio(image_bytes, aspect_ratio)
                
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
    
    # Generate edited image using official SDK method
    response = client.models.generate_content(
        model='gemini-2.5-flash-image',
        contents=contents,
        config=types.GenerateContentConfig(
            response_modalities=['IMAGE']
        )
    )
    
    print(f"[Nano Banana] Edit response received. Type: {type(response)}")
    
    # Extract image using as_image() method from documentation
    try:
        # Access parts through candidates[0].content.parts
        if not hasattr(response, 'candidates') or not response.candidates:
            raise Exception(f"No candidates in response")
        
        candidate = response.candidates[0]
        if not hasattr(candidate, 'content') or not candidate.content:
            raise Exception(f"No content in candidate")
        
        if not hasattr(candidate.content, 'parts') or not candidate.content.parts:
            raise Exception(f"No parts in content")
        
        for part in candidate.content.parts:
            if part.inline_data:
                # Extract image bytes directly from inline_data
                image_bytes = part.inline_data.data
                
                print(f"[Nano Banana] Image edited successfully! Size: {len(image_bytes)} bytes")
                
                # Resize to target aspect ratio
                image_bytes = resize_to_aspect_ratio(image_bytes, aspect_ratio)
                
                return image_bytes
        
        raise Exception(f"No image found in response parts")
        
    except Exception as e:
        import traceback
        raise Exception(f"Failed to extract edited image from Gemini response: {str(e)}\n\nTraceback: {traceback.format_exc()}")



