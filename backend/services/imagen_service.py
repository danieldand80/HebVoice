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


def get_user_friendly_error(finish_reason, safety_ratings=None, context="generate"):
    """Convert API errors to user-friendly messages"""
    
    if 'SAFETY' in str(finish_reason):
        return "Please use English language in your prompt and avoid inappropriate content"
    elif finish_reason == 'MAX_TOKENS':
        return "Prompt is too long. Please use a shorter description"
    elif finish_reason == 'STOP':
        # Normal finish but no image - likely non-English prompt
        return "Please write your prompt in English only (not Hebrew/Russian/etc)"
    else:
        return f"Could not {context} image. Please use English language in your prompt"


async def generate_image_from_prompt(
    prompt: str,
    aspect_ratio: AspectRatio = "16:9",
    num_images: int = 1
) -> list[bytes]:
    """Generate images using Gemini 2.5 Flash Image (Nano Banana) - text2img
    
    Args:
        prompt: Text description in English
        aspect_ratio: Image aspect ratio (16:9, 9:16, 1:1)
        num_images: Number of images to generate (1-4)
    
    Returns:
        List of image bytes
    """
    
    if not GOOGLE_API_KEY or not client:
        raise Exception("GOOGLE_API_KEY not set in environment")
    
    # Validate prompt
    if not prompt or prompt.strip() == "":
        raise Exception("Please write a prompt in English to generate image")
    
    # Validate num_images
    if num_images < 1 or num_images > 4:
        num_images = 1
    
    print(f"[Nano Banana] Generating {num_images} image(s) (text2img) with prompt: {prompt}")
    print(f"[Nano Banana] Aspect ratio: {aspect_ratio}")
    
    # Generate multiple images in parallel
    import asyncio
    
    async def generate_single():
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
        return response
    
    # Generate all images in parallel
    responses = await asyncio.gather(*[generate_single() for _ in range(num_images)])
    
    print(f"[Nano Banana] {len(responses)} responses received")
    
    # Extract images from all responses
    all_images = []
    
    for idx, response in enumerate(responses):
        print(f"[Nano Banana] Processing response {idx+1}/{len(responses)}. Type: {type(response)}")
        
        # Extract image from response
        try:
            if not hasattr(response, 'candidates') or not response.candidates:
                print(f"[WARNING] Response {idx+1}: No candidates, skipping")
                continue
            
            candidate = response.candidates[0]
            
            finish_reason = getattr(candidate, 'finish_reason', 'unknown')
            safety_ratings = getattr(candidate, 'safety_ratings', None)
            
            if hasattr(candidate, 'finish_reason'):
                print(f"[DEBUG] Response {idx+1} finish_reason: {candidate.finish_reason}")
            if hasattr(candidate, 'safety_ratings'):
                print(f"[DEBUG] Response {idx+1} safety_ratings: {candidate.safety_ratings}")
            
            if not hasattr(candidate, 'content') or not candidate.content:
                print(f"[WARNING] Response {idx+1}: No content (reason: {finish_reason}), skipping")
                continue
            
            if not hasattr(candidate.content, 'parts') or not candidate.content.parts:
                print(f"[WARNING] Response {idx+1}: No parts, skipping")
                continue
            
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
                
                print(f"[Nano Banana] Image {idx+1} final size: {len(image_bytes)} bytes")
                all_images.append(image_bytes)
                break  # Found image in this response
        
        except Exception as e:
            print(f"[WARNING] Response {idx+1} failed: {e}")
            continue
    
    # Check if we got at least one image
    if len(all_images) == 0:
        raise Exception("Please write your prompt in English only (Hebrew/Russian/other languages are not supported)")
    
    print(f"[Nano Banana] Successfully generated {len(all_images)}/{num_images} image(s)")
    return all_images


async def edit_image_with_prompt(
    image_bytes: bytes,
    prompt: str,
    aspect_ratio: AspectRatio = "16:9",
    num_images: int = 1
) -> list[bytes]:
    """Edit existing image using Gemini 2.5 Flash Image (Nano Banana) - img2img
    
    This function takes an existing image and modifies it based on text prompt.
    For example: "change background to modern shop" - keeps product, changes background.
    
    Args:
        image_bytes: Original image bytes
        prompt: Edit instruction in English
        aspect_ratio: Output aspect ratio (16:9, 9:16, 1:1)
        num_images: Number of variations to generate (1-4)
    
    Returns:
        List of edited image bytes
    """
    
    if not GOOGLE_API_KEY or not client:
        raise Exception("GOOGLE_API_KEY not set in environment")
    
    # Validate prompt
    if not prompt or prompt.strip() == "":
        raise Exception("Please write a prompt in English to edit image")
    
    if len(image_bytes) == 0:
        raise Exception("Please upload an image")
    
    # Validate num_images
    if num_images < 1 or num_images > 4:
        num_images = 1
    
    print(f"[Nano Banana] Editing image (img2img) - generating {num_images} variation(s)")
    print(f"[Nano Banana] Prompt: {prompt}")
    print(f"[Nano Banana] Aspect ratio: {aspect_ratio}")
    print(f"[Nano Banana] Image bytes size: {len(image_bytes)}")
    
    # Convert to PIL Image
    try:
        pil_image = PILImage.open(io.BytesIO(image_bytes))
    except Exception as e:
        raise Exception(f"Failed to open image: {str(e)}")
    
    print(f"[Nano Banana] PIL Image loaded: {pil_image.size}, mode: {pil_image.mode}")
    
    # Generate multiple variations in parallel
    import asyncio
    
    async def edit_single():
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
        return response
    
    # Generate all variations in parallel
    responses = await asyncio.gather(*[edit_single() for _ in range(num_images)])
    
    print(f"[Nano Banana] {len(responses)} edit responses received")
    
    # Extract images from all responses
    all_images = []
    
    for idx, response in enumerate(responses):
        print(f"[Nano Banana] Processing edit response {idx+1}/{len(responses)}. Type: {type(response)}")
        
        # Extract image from response
        try:
            if not hasattr(response, 'candidates') or not response.candidates:
                print(f"[WARNING] Response {idx+1}: No candidates, skipping")
                continue
            
            candidate = response.candidates[0]
            
            finish_reason = getattr(candidate, 'finish_reason', 'unknown')
            safety_ratings = getattr(candidate, 'safety_ratings', None)
            
            if hasattr(candidate, 'finish_reason'):
                print(f"[DEBUG] Response {idx+1} finish_reason: {candidate.finish_reason}")
            if hasattr(candidate, 'safety_ratings'):
                print(f"[DEBUG] Response {idx+1} safety_ratings: {candidate.safety_ratings}")
            
            if not hasattr(candidate, 'content') or not candidate.content:
                print(f"[WARNING] Response {idx+1}: No content (reason: {finish_reason}), skipping")
                continue
            
            if not hasattr(candidate.content, 'parts') or not candidate.content.parts:
                print(f"[WARNING] Response {idx+1}: No parts, skipping")
                continue
            
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
                
                print(f"[Nano Banana] Edited image {idx+1} final size: {len(image_bytes)} bytes")
                all_images.append(image_bytes)
                break  # Found image in this response
        
        except Exception as e:
            print(f"[WARNING] Response {idx+1} failed: {e}")
            continue
    
    # Check if we got at least one image
    if len(all_images) == 0:
        raise Exception("Please write your prompt in English only (Hebrew/Russian/other languages are not supported)")
    
    print(f"[Nano Banana] Successfully edited {len(all_images)}/{num_images} variation(s)")
    return all_images



