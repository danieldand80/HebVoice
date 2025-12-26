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
    
    # Use generate_images API (NOT generate_content) for native aspect_ratio support
    response = client.models.generate_images(
        model='imagen-3.0-generate-001',
        prompt=prompt,
        config=types.GenerateImagesConfig(
            aspectRatio=aspect_ratio,
            numberOfImages=1
        )
    )
    
    print(f"[Nano Banana] Response received. Type: {type(response)}")
    
    # Extract image from GenerateImagesResponse
    try:
        if not response.generated_images or len(response.generated_images) == 0:
            raise Exception("No images generated in response")
        
        generated_image = response.generated_images[0]
        
        # Get PIL Image
        if hasattr(generated_image, 'image'):
            pil_img = generated_image.image
            
            # Convert PIL to bytes
            buffer = io.BytesIO()
            pil_img.save(buffer, format='PNG')
            buffer.seek(0)
            image_bytes = buffer.getvalue()
            
            print(f"[Nano Banana] Image generated! Size: {len(image_bytes)} bytes, dimensions: {pil_img.size}")
            return image_bytes
        else:
            raise Exception("No image found in generated_image")
        
    except Exception as e:
        import traceback
        raise Exception(f"Failed to extract image from generate_images response: {str(e)}\n\nTraceback: {traceback.format_exc()}")


async def edit_image_with_prompt(
    image_bytes: bytes,
    prompt: str,
    aspect_ratio: AspectRatio = "16:9"
) -> bytes:
    """Edit existing image using Imagen API - img2img
    
    This function takes an existing image and modifies it based on text prompt.
    For example: "change background to modern shop" - keeps product, changes background.
    """
    
    if not GOOGLE_API_KEY or not client:
        raise Exception("GOOGLE_API_KEY not set in environment")
    
    print(f"[Imagen] Editing image (img2img) with prompt: {prompt}")
    print(f"[Imagen] Aspect ratio: {aspect_ratio}")
    print(f"[Imagen] Image bytes size: {len(image_bytes)}")
    
    if len(image_bytes) == 0:
        raise Exception("Image bytes are empty! Cannot edit empty image.")
    
    # Convert image bytes to PIL Image
    try:
        pil_image = PILImage.open(io.BytesIO(image_bytes))
    except Exception as e:
        raise Exception(f"Failed to open image with PIL: {str(e)}")
    
    print(f"[Imagen] PIL Image loaded: {pil_image.size}, mode: {pil_image.mode}")
    
    # Use edit_image API (NOT generate_content) for native aspect_ratio support
    response = client.models.edit_image(
        model='imagen-3.0-capability-001',
        prompt=prompt,
        reference_images=[
            types.RawReferenceImage(
                referenceImage=pil_image,
                referenceType='RAW'
            )
        ],
        config=types.EditImageConfig(
            aspectRatio=aspect_ratio,
            numberOfImages=1,
            editMode='EDIT_MODE_INPAINT_INSERTION'
        )
    )
    
    print(f"[Imagen] Edit response received. Type: {type(response)}")
    
    # Extract image from EditImageResponse
    try:
        if not response.generated_images or len(response.generated_images) == 0:
            raise Exception("No images generated in edit response")
        
        generated_image = response.generated_images[0]
        
        # Get PIL Image
        if hasattr(generated_image, 'image'):
            pil_img = generated_image.image
            
            # Convert PIL to bytes
            buffer = io.BytesIO()
            pil_img.save(buffer, format='PNG')
            buffer.seek(0)
            image_bytes = buffer.getvalue()
            
            print(f"[Imagen] Image edited! Size: {len(image_bytes)} bytes, dimensions: {pil_img.size}")
            return image_bytes
        else:
            raise Exception("No image found in generated_image")
        
    except Exception as e:
        import traceback
        raise Exception(f"Failed to extract image from edit_image response: {str(e)}\n\nTraceback: {traceback.format_exc()}")



