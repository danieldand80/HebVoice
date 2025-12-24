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

AspectRatio = Literal["9:16", "16:9"]

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
        if not hasattr(response, 'parts') or not response.parts or len(response.parts) == 0:
            raise Exception(f"No parts in response: {response}")
        
        for part in response.parts:
            if part.inline_data:
                # Use as_image() method from official documentation
                pil_image = part.as_image()
                
                # Convert PIL Image to bytes
                buffer = io.BytesIO()
                pil_image.save(buffer, format='PNG')
                buffer.seek(0)
                image_bytes = buffer.getvalue()
                
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
        if not hasattr(response, 'parts') or not response.parts or len(response.parts) == 0:
            raise Exception(f"No parts in response: {response}")
        
        for part in response.parts:
            if part.inline_data:
                # Use as_image() method from official documentation
                edited_pil_image = part.as_image()
                
                # Convert PIL Image to bytes
                buffer = io.BytesIO()
                edited_pil_image.save(buffer, format='PNG')
                buffer.seek(0)
                image_bytes = buffer.getvalue()
                
                print(f"[Nano Banana] Image edited successfully! Size: {len(image_bytes)} bytes")
                return image_bytes
        
        raise Exception(f"No image found in response parts")
        
    except Exception as e:
        import traceback
        raise Exception(f"Failed to extract edited image from Gemini response: {str(e)}\n\nTraceback: {traceback.format_exc()}")



