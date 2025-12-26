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
    try:
        import google.genai as genai_module
        sdk_version = getattr(genai_module, '__version__', 'unknown')
        print(f"[Google AI Studio] API configured successfully (SDK version: {sdk_version})")
    except:
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
                
                # Check actual image dimensions from API
                try:
                    pil_img = PILImage.open(io.BytesIO(image_bytes))
                    api_width, api_height = pil_img.size
                    api_ratio = api_width / api_height
                    print(f"[Nano Banana] Image from API: {api_width}x{api_height} (ratio: {api_ratio:.2f})")
                    
                    # Define target ratios
                    target_ratios = {
                        "16:9": 16/9,    # ~1.78
                        "9:16": 9/16,    # ~0.56
                        "1:1": 1.0       # 1.0
                    }
                    
                    target_ratio = target_ratios[aspect_ratio]
                    
                    # Check if API returned correct aspect ratio (tolerance 0.1)
                    if abs(api_ratio - target_ratio) > 0.1:
                        print(f"[WARNING] API ignored aspectRatio! Expected {aspect_ratio} ({target_ratio:.2f}), got {api_ratio:.2f}")
                        print(f"[Fallback] Applying post-processing to fix aspect ratio...")
                        
                        # Apply post-processing to fix aspect ratio
                        target_dims = {
                            "16:9": (1920, 1080),
                            "9:16": (1080, 1920),
                            "1:1": (1024, 1024)
                        }
                        target_width, target_height = target_dims[aspect_ratio]
                        
                        # Crop to target aspect ratio
                        if api_ratio > target_ratio:
                            # Wider - crop width
                            new_width = int(api_height * target_ratio)
                            left = (api_width - new_width) // 2
                            pil_img = pil_img.crop((left, 0, left + new_width, api_height))
                        else:
                            # Taller - crop height
                            new_height = int(api_width / target_ratio)
                            top = (api_height - new_height) // 2
                            pil_img = pil_img.crop((0, top, api_width, top + new_height))
                        
                        # Resize to target dimensions
                        pil_img = pil_img.resize((target_width, target_height), PILImage.LANCZOS)
                        
                        # Convert back to bytes
                        buffer = io.BytesIO()
                        pil_img.save(buffer, format='PNG')
                        buffer.seek(0)
                        image_bytes = buffer.getvalue()
                        
                        print(f"[Fallback] Fixed dimensions: {pil_img.size}")
                    else:
                        print(f"[SUCCESS] API returned correct aspect ratio!")
                    
                except Exception as e:
                    print(f"[WARNING] Could not verify dimensions: {e}")
                
                print(f"[Nano Banana] Final image size: {len(image_bytes)} bytes")
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
                
                # Check actual image dimensions from API
                try:
                    pil_img = PILImage.open(io.BytesIO(image_bytes))
                    api_width, api_height = pil_img.size
                    api_ratio = api_width / api_height
                    print(f"[Nano Banana] Edited image from API: {api_width}x{api_height} (ratio: {api_ratio:.2f})")
                    
                    # Define target ratios
                    target_ratios = {
                        "16:9": 16/9,    # ~1.78
                        "9:16": 9/16,    # ~0.56
                        "1:1": 1.0       # 1.0
                    }
                    
                    target_ratio = target_ratios[aspect_ratio]
                    
                    # Check if API returned correct aspect ratio (tolerance 0.1)
                    if abs(api_ratio - target_ratio) > 0.1:
                        print(f"[WARNING] API ignored aspectRatio! Expected {aspect_ratio} ({target_ratio:.2f}), got {api_ratio:.2f}")
                        print(f"[Fallback] Applying post-processing to fix aspect ratio...")
                        
                        # Apply post-processing to fix aspect ratio
                        target_dims = {
                            "16:9": (1920, 1080),
                            "9:16": (1080, 1920),
                            "1:1": (1024, 1024)
                        }
                        target_width, target_height = target_dims[aspect_ratio]
                        
                        # Crop to target aspect ratio
                        if api_ratio > target_ratio:
                            # Wider - crop width
                            new_width = int(api_height * target_ratio)
                            left = (api_width - new_width) // 2
                            pil_img = pil_img.crop((left, 0, left + new_width, api_height))
                        else:
                            # Taller - crop height
                            new_height = int(api_width / target_ratio)
                            top = (api_height - new_height) // 2
                            pil_img = pil_img.crop((0, top, api_width, top + new_height))
                        
                        # Resize to target dimensions
                        pil_img = pil_img.resize((target_width, target_height), PILImage.LANCZOS)
                        
                        # Convert back to bytes
                        buffer = io.BytesIO()
                        pil_img.save(buffer, format='PNG')
                        buffer.seek(0)
                        image_bytes = buffer.getvalue()
                        
                        print(f"[Fallback] Fixed dimensions: {pil_img.size}")
                    else:
                        print(f"[SUCCESS] API returned correct aspect ratio!")
                    
                except Exception as e:
                    print(f"[WARNING] Could not verify dimensions: {e}")
                
                print(f"[Nano Banana] Final edited image size: {len(image_bytes)} bytes")
                return image_bytes
        
        raise Exception("No image found in response parts")
        
    except Exception as e:
        import traceback
        raise Exception(f"Failed to extract image: {str(e)}\n\nTraceback: {traceback.format_exc()}")



