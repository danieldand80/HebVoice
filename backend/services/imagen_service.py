from vertexai.preview.vision_models import ImageGenerationModel
import vertexai
import os
import base64
import json
import tempfile
import io
from typing import Literal
from PIL import Image as PILImage

# Initialize Vertex AI
PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID")
LOCATION = os.getenv("GOOGLE_LOCATION", "us-central1")

# Handle credentials from env or file (for Railway deployment)
credentials_json_str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
credentials = None

if credentials_json_str:
    try:
        # Parse JSON from env variable
        credentials_dict = json.loads(credentials_json_str)
        
        # Create temporary credentials file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(credentials_dict, f)
            credentials_path = f.name
        
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
        
        # Also create credentials object directly
        from google.oauth2 import service_account
        credentials = service_account.Credentials.from_service_account_info(credentials_dict)
        
    except Exception as e:
        print(f"WARNING: Failed to load credentials from JSON: {e}")
        # Will try to use default credentials

if PROJECT_ID:
    vertexai.init(
        project=PROJECT_ID, 
        location=LOCATION,
        credentials=credentials
    )

AspectRatio = Literal["9:16", "16:9"]

async def generate_image_from_prompt(
    prompt: str,
    aspect_ratio: AspectRatio = "16:9"
) -> bytes:
    """Generate image using Google Imagen (Nano Banana)"""
    
    if not PROJECT_ID:
        raise Exception("GOOGLE_PROJECT_ID not set in environment")
    
    # Initialize Imagen model
    model = ImageGenerationModel.from_pretrained("imagegeneration@006")
    
    # Map aspect ratios to Imagen format
    imagen_aspect_ratio = "16:9" if aspect_ratio == "16:9" else "9:16"
    
    # Generate image
    response = model.generate_images(
        prompt=prompt,
        number_of_images=1,
        aspect_ratio=imagen_aspect_ratio,
        safety_filter_level="block_some",
        person_generation="allow_adult"
    )
    
    # Get first image
    image = response.images[0]
    
    # Convert to bytes - use _pil_image attribute
    try:
        # Imagen returns object with _pil_image attribute
        if hasattr(image, '_pil_image'):
            pil_image = image._pil_image
            buffer = io.BytesIO()
            pil_image.save(buffer, format='PNG')
            buffer.seek(0)
            image_bytes = buffer.getvalue()
        elif hasattr(image, '_image_bytes'):
            # Direct bytes attribute
            image_bytes = image._image_bytes
        else:
            # Last resort: save to temp file and read
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                image.save(location=tmp.name)
                tmp.seek(0)
                with open(tmp.name, 'rb') as f:
                    image_bytes = f.read()
                os.unlink(tmp.name)
        
        return image_bytes
        
    except Exception as e:
        import traceback
        raise Exception(f"Failed to convert Imagen image to bytes: {str(e)}\n\nTraceback: {traceback.format_exc()}\n\nAvailable attributes: {dir(image)}")


async def enhance_product_image(
    image_path: str,
    prompt: str,
    aspect_ratio: AspectRatio = "16:9"
) -> bytes:
    """Enhance product image using Imagen edit capabilities"""
    
    if not PROJECT_ID:
        raise Exception("GOOGLE_PROJECT_ID not set in environment")
    
    # For MVP, we'll generate new image based on prompt
    # In future can add actual image-to-image editing
    
    enhanced_prompt = f"Professional product photography: {prompt}, high quality, clean background, commercial advertising style"
    
    return await generate_image_from_prompt(enhanced_prompt, aspect_ratio)

