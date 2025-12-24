from vertexai.generative_models import GenerativeModel, Part, Image as GeminiImage
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
    """Generate image using Gemini 2.5 Flash Image (Nano Banana) - text2img"""
    
    if not PROJECT_ID:
        raise Exception("GOOGLE_PROJECT_ID not set in environment")
    
    # Initialize Gemini 2.5 Flash Image model (Nano Banana)
    model = GenerativeModel("gemini-2.5-flash-image")
    
    # Format aspect ratio for Gemini
    aspect_ratio_str = aspect_ratio  # "9:16" or "16:9"
    
    # Create generation config with correct parameters
    generation_config = {
        "responseModalities": ["IMAGE"],  # Correct parameter name (capital letters)
        "responseMimeType": "image/png"
    }
    
    print(f"[Nano Banana] Generating image (text2img) with prompt: {prompt}")
    print(f"[Nano Banana] Aspect ratio: {aspect_ratio_str}")
    
    # Generate image from text
    response = model.generate_content(
        prompt,
        generation_config=generation_config
    )
    
    print(f"[Nano Banana] Response received. Type: {type(response)}")
    
    # Extract image bytes from response
    try:
        # Gemini returns image in response.candidates[0].content.parts[0].inline_data.data
        if not response.candidates or len(response.candidates) == 0:
            raise Exception(f"No candidates in response: {response}")
        
        candidate = response.candidates[0]
        if not candidate.content.parts or len(candidate.content.parts) == 0:
            raise Exception(f"No parts in candidate: {candidate}")
        
        part = candidate.content.parts[0]
        
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
    
    if not PROJECT_ID:
        raise Exception("GOOGLE_PROJECT_ID not set in environment")
    
    # Initialize Gemini 2.5 Flash Image model (Nano Banana)
    model = GenerativeModel("gemini-2.5-flash-image")
    
    # Create generation config with correct parameters
    generation_config = {
        "responseModalities": ["IMAGE"],  # Correct parameter name
        "responseMimeType": "image/png"
    }
    
    print(f"[Nano Banana] Editing image (img2img) with prompt: {prompt}")
    print(f"[Nano Banana] Aspect ratio: {aspect_ratio}")
    
    # Create image part from bytes
    image_part = Part.from_data(
        data=image_bytes,
        mime_type="image/jpeg"
    )
    
    # Create multimodal prompt with image + text instruction
    contents = [
        image_part,
        prompt  # Instruction like "change background to modern shop"
    ]
    
    # Generate edited image
    response = model.generate_content(
        contents,
        generation_config=generation_config
    )
    
    print(f"[Nano Banana] Edit response received. Type: {type(response)}")
    
    # Extract image bytes from response
    try:
        if not response.candidates or len(response.candidates) == 0:
            raise Exception(f"No candidates in response: {response}")
        
        candidate = response.candidates[0]
        if not candidate.content.parts or len(candidate.content.parts) == 0:
            raise Exception(f"No parts in candidate: {candidate}")
        
        part = candidate.content.parts[0]
        
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

