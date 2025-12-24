import google.generativeai as genai
import os
import base64
import io
from typing import Literal
from PIL import Image as PILImage

# Initialize Google AI Studio API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
    print("[Google AI Studio] API configured successfully")
else:
    print("WARNING: GOOGLE_API_KEY not set in environment")

AspectRatio = Literal["9:16", "16:9"]

async def generate_image_from_prompt(
    prompt: str,
    aspect_ratio: AspectRatio = "16:9"
) -> bytes:
    """Generate image using Gemini 2.5 Flash Image (Nano Banana) - text2img"""
    
    if not GOOGLE_API_KEY:
        raise Exception("GOOGLE_API_KEY not set in environment")
    
    # Initialize Gemini 2.5 Flash Image model (Nano Banana)
    model = genai.GenerativeModel("gemini-2.5-flash-image")
    
    print(f"[Nano Banana] Generating image (text2img) with prompt: {prompt}")
    print(f"[Nano Banana] Aspect ratio: {aspect_ratio}")
    
    # Generate image from text
    response = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            response_modalities=["IMAGE"],
            response_mime_type="image/png"
        )
    )
    
    print(f"[Nano Banana] Response received. Type: {type(response)}")
    
    # Extract image bytes from response
    try:
        # Check if response has parts
        if not response.parts or len(response.parts) == 0:
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
    
    if not GOOGLE_API_KEY:
        raise Exception("GOOGLE_API_KEY not set in environment")
    
    # Initialize Gemini 2.5 Flash Image model (Nano Banana)
    model = genai.GenerativeModel("gemini-2.5-flash-image")
    
    print(f"[Nano Banana] Editing image (img2img) with prompt: {prompt}")
    print(f"[Nano Banana] Aspect ratio: {aspect_ratio}")
    
    # Convert image bytes to PIL Image
    pil_image = PILImage.open(io.BytesIO(image_bytes))
    
    # Create multimodal prompt with image + text instruction
    contents = [
        pil_image,
        prompt  # Instruction like "change background to modern shop"
    ]
    
    # Generate edited image
    response = model.generate_content(
        contents,
        generation_config=genai.GenerationConfig(
            response_modalities=["IMAGE"],
            response_mime_type="image/png"
        )
    )
    
    print(f"[Nano Banana] Edit response received. Type: {type(response)}")
    
    # Extract image bytes from response
    try:
        if not response.parts or len(response.parts) == 0:
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
    """Enhance product image using Imagen edit capabilities"""
    
    if not PROJECT_ID:
        raise Exception("GOOGLE_PROJECT_ID not set in environment")
    
    # Read image bytes
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
    
    # Use edit function with prompt
    return await edit_image_with_prompt(image_bytes, prompt, aspect_ratio)

