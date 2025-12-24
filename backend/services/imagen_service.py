from google import genai
import os
import base64
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
    
    # Generate image from text using new SDK
    response = client.models.generate_content(
        model='gemini-2.5-flash-image',
        contents=prompt,
        config={
            'response_modalities': ['IMAGE'],
            'response_mime_type': 'image/png'
        }
    )
    
    print(f"[Nano Banana] Response received. Type: {type(response)}")
    
    # Extract image bytes from response
    try:
        # Check if response has parts
        if not hasattr(response, 'parts') or not response.parts or len(response.parts) == 0:
            raise Exception(f"No parts in response: {response}")
        
        part = response.parts[0]
        
        # Get image data (base64 encoded)
        if hasattr(part, 'inline_data') and part.inline_data:
            image_data_base64 = part.inline_data.data
            # Decode base64 to bytes
            image_bytes = base64.b64decode(image_data_base64)
            print(f"[Nano Banana] Image generated successfully! Size: {len(image_bytes)} bytes")
            return image_bytes
        else:
            raise Exception(f"No inline_data in part: {part}")
        
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
    
    # Convert image bytes to base64 for API
    image_data_base64 = base64.b64encode(image_bytes).decode('utf-8')
    
    # Create multimodal content with image + text instruction
    contents = [
        {
            'mime_type': 'image/jpeg',
            'data': image_data_base64
        },
        prompt  # Instruction like "change background to modern shop"
    ]
    
    # Generate edited image using new SDK
    response = client.models.generate_content(
        model='gemini-2.5-flash-image',
        contents=contents,
        config={
            'response_modalities': ['IMAGE'],
            'response_mime_type': 'image/png'
        }
    )
    
    print(f"[Nano Banana] Edit response received. Type: {type(response)}")
    
    # Extract image bytes from response
    try:
        if not hasattr(response, 'parts') or not response.parts or len(response.parts) == 0:
            raise Exception(f"No parts in response: {response}")
        
        part = response.parts[0]
        
        # Get image data (base64 encoded)
        if hasattr(part, 'inline_data') and part.inline_data:
            image_data_base64 = part.inline_data.data
            # Decode base64 to bytes
            image_bytes = base64.b64decode(image_data_base64)
            print(f"[Nano Banana] Image edited successfully! Size: {len(image_bytes)} bytes")
            return image_bytes
        else:
            raise Exception(f"No inline_data in part: {part}")
        
    except Exception as e:
        import traceback
        raise Exception(f"Failed to extract edited image from Gemini response: {str(e)}\n\nTraceback: {traceback.format_exc()}")


async def enhance_product_image(
    image_path: str,
    prompt: str,
    aspect_ratio: AspectRatio = "16:9"
) -> bytes:
    """Enhance product image using Gemini img2img"""
    
    if not GOOGLE_API_KEY:
        raise Exception("GOOGLE_API_KEY not set in environment")
    
    # Read image bytes
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
    
    # Use edit function with prompt
    return await edit_image_with_prompt(image_bytes, prompt, aspect_ratio)

