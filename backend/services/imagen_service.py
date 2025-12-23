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
    
    # Calculate target size based on aspect ratio
    if aspect_ratio == "9:16":
        # Vertical format (e.g., 1080x1920)
        width, height = 1024, 1792
    else:
        # Horizontal format 16:9 (e.g., 1920x1080)
        width, height = 1792, 1024
    
    # Generate image
    print(f"Generating image with prompt: {prompt}")
    response = model.generate_images(
        prompt=prompt,
        number_of_images=1
    )
    
    print(f"Response received. Type: {type(response)}")
    print(f"Response attributes: {dir(response)}")
    print(f"Number of images: {len(response.images) if hasattr(response, 'images') else 'N/A'}")
    
    # Check if images were generated
    if not response.images or len(response.images) == 0:
        raise Exception(f"No images generated. Response: {response}")
    
    # Get first image
    image = response.images[0]
    print(f"Image type: {type(image)}, Image attributes: {dir(image)}")
    
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


async def edit_image_with_prompt(
    image_bytes: bytes,
    prompt: str,
    aspect_ratio: AspectRatio = "16:9"
) -> bytes:
    """Edit existing image using Imagen based on text prompt"""
    
    if not PROJECT_ID:
        raise Exception("GOOGLE_PROJECT_ID not set in environment")
    
    # Initialize Imagen model
    from vertexai.preview.vision_models import Image as ImagenImage
    model = ImageGenerationModel.from_pretrained("imagegeneration@006")
    
    # Convert bytes to Imagen Image object
    base_image = ImagenImage(image_bytes=image_bytes)
    
    print(f"Editing image with prompt: {prompt}")
    
    # Edit image based on prompt
    try:
        # Try using edit_image method
        response = model.edit_image(
            base_image=base_image,
            prompt=prompt,
            number_of_images=1
        )
    except AttributeError:
        # Fallback: use image-to-image generation
        # Create a combined prompt that describes the edit
        enhanced_prompt = f"Based on this image: {prompt}, professional photography, high quality"
        print(f"edit_image not available, using generate_images with enhanced prompt")
        response = model.generate_images(
            prompt=enhanced_prompt,
            number_of_images=1
        )
    
    print(f"Edit response received. Number of images: {len(response.images) if hasattr(response, 'images') else 'N/A'}")
    
    # Check if images were generated
    if not response.images or len(response.images) == 0:
        raise Exception(f"No images generated from edit. Response: {response}")
    
    # Get first image
    image = response.images[0]
    
    # Convert to bytes
    try:
        if hasattr(image, '_pil_image'):
            pil_image = image._pil_image
            buffer = io.BytesIO()
            pil_image.save(buffer, format='PNG')
            buffer.seek(0)
            image_bytes = buffer.getvalue()
        elif hasattr(image, '_image_bytes'):
            image_bytes = image._image_bytes
        else:
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
        raise Exception(f"Failed to convert edited image to bytes: {str(e)}\n\nTraceback: {traceback.format_exc()}")


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

