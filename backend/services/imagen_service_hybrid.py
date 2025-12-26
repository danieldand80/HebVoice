"""
Hybrid Imagen service: supports both AI Studio and Vertex AI.
Automatically chooses best available option.
"""

from google import genai
from google.genai import types
import os
import io
from typing import Literal
from PIL import Image as PILImage

# Configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")  # AI Studio
VERTEX_PROJECT_ID = os.getenv("VERTEX_PROJECT_ID")  # Vertex AI
VERTEX_LOCATION = os.getenv("VERTEX_LOCATION", "us-central1")

# Initialize clients
ai_studio_client = None
vertex_client = None

if VERTEX_PROJECT_ID:
    # Vertex AI (BEST - native aspect_ratio)
    try:
        vertex_client = genai.Client(
            vertexai=True,
            project=VERTEX_PROJECT_ID,
            location=VERTEX_LOCATION
        )
        print(f"[Hybrid] ✅ Vertex AI initialized: {VERTEX_PROJECT_ID}")
    except Exception as e:
        print(f"[Hybrid] ⚠️  Vertex AI failed to initialize: {e}")

if GOOGLE_API_KEY:
    # AI Studio (FALLBACK - crop/resize)
    ai_studio_client = genai.Client(api_key=GOOGLE_API_KEY)
    print(f"[Hybrid] ✅ AI Studio initialized")

# Determine which client to use
USE_VERTEX = vertex_client is not None
USE_AI_STUDIO = ai_studio_client is not None

if not USE_VERTEX and not USE_AI_STUDIO:
    print("[Hybrid] ❌ ERROR: No API configured!")
elif USE_VERTEX:
    print("[Hybrid] 🌟 Using Vertex AI (NATIVE aspect_ratio)")
else:
    print("[Hybrid] ⚙️  Using AI Studio (smart crop/resize)")

AspectRatio = Literal["9:16", "16:9", "1:1"]


def smart_crop_and_resize(image_bytes: bytes, aspect_ratio: AspectRatio) -> bytes:
    """Smart crop/resize for AI Studio fallback"""
    target_dimensions = {
        "16:9": (1920, 1080),
        "9:16": (1080, 1920),
        "1:1": (1024, 1024)
    }
    
    target_width, target_height = target_dimensions[aspect_ratio]
    img = PILImage.open(io.BytesIO(image_bytes))
    original_width, original_height = img.size
    
    print(f"[Smart Resize] {original_width}x{original_height} → {target_width}x{target_height}")
    
    target_ratio = target_width / target_height
    current_ratio = original_width / original_height
    
    if abs(current_ratio - target_ratio) > 0.01:
        if current_ratio > target_ratio:
            new_width = int(original_height * target_ratio)
            left = (original_width - new_width) // 2
            img = img.crop((left, 0, left + new_width, original_height))
        else:
            new_height = int(original_width / target_ratio)
            top = (original_height - new_height) // 2
            img = img.crop((0, top, original_width, top + new_height))
    
    if img.size != (target_width, target_height):
        img = img.resize((target_width, target_height), PILImage.LANCZOS)
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG', optimize=True)
    buffer.seek(0)
    return buffer.getvalue()


async def generate_image_from_prompt(
    prompt: str,
    aspect_ratio: AspectRatio = "16:9"
) -> bytes:
    """Generate image - uses Vertex AI if available, falls back to AI Studio"""
    
    if USE_VERTEX:
        return await _generate_vertex(prompt, aspect_ratio)
    elif USE_AI_STUDIO:
        return await _generate_ai_studio(prompt, aspect_ratio)
    else:
        raise Exception("No API configured! Set VERTEX_PROJECT_ID or GOOGLE_API_KEY")


async def _generate_vertex(prompt: str, aspect_ratio: AspectRatio) -> bytes:
    """Vertex AI: NATIVE aspect_ratio support"""
    print(f"[Vertex AI] Generating with NATIVE {aspect_ratio}")
    
    response = vertex_client.models.generate_images(
        model="imagen-3.0-generate-001",
        prompt=prompt,
        config=types.GenerateImagesConfig(
            aspectRatio=aspect_ratio,
            numberOfImages=1
        )
    )
    
    if not response.generated_images:
        raise Exception("No images generated")
    
    pil_image = response.generated_images[0].image.as_image()
    print(f"[Vertex AI] ✨ Perfect {aspect_ratio}: {pil_image.size}")
    
    buffer = io.BytesIO()
    pil_image.save(buffer, format='PNG', optimize=True)
    buffer.seek(0)
    return buffer.getvalue()


async def _generate_ai_studio(prompt: str, aspect_ratio: AspectRatio) -> bytes:
    """AI Studio: Smart prompts + crop/resize"""
    aspect_hints = {
        "16:9": "HORIZONTAL WIDESCREEN composition, 16:9 aspect ratio, landscape orientation",
        "9:16": "VERTICAL PORTRAIT composition, 9:16 aspect ratio, portrait orientation",
        "1:1": "SQUARE composition, 1:1 aspect ratio, centered subject"
    }
    
    enhanced_prompt = f"{prompt}\n\nCOMPOSITION: {aspect_hints[aspect_ratio]}"
    print(f"[AI Studio] Generating with smart prompts")
    
    response = ai_studio_client.models.generate_content(
        model='gemini-2.5-flash-image',
        contents=[enhanced_prompt],
        config=types.GenerateContentConfig(response_modalities=['IMAGE'])
    )
    
    for part in response.candidates[0].content.parts:
        if part.inline_data:
            image_bytes = part.inline_data.data
            print(f"[AI Studio] Generated, applying smart resize...")
            return smart_crop_and_resize(image_bytes, aspect_ratio)
    
    raise Exception("No image in response")


async def edit_image_with_prompt(
    image_bytes: bytes,
    prompt: str,
    aspect_ratio: AspectRatio = "16:9"
) -> bytes:
    """Edit image - uses Vertex AI if available, falls back to AI Studio"""
    
    if USE_VERTEX:
        return await _edit_vertex(image_bytes, prompt, aspect_ratio)
    elif USE_AI_STUDIO:
        return await _edit_ai_studio(image_bytes, prompt, aspect_ratio)
    else:
        raise Exception("No API configured! Set VERTEX_PROJECT_ID or GOOGLE_API_KEY")


async def _edit_vertex(image_bytes: bytes, prompt: str, aspect_ratio: AspectRatio) -> bytes:
    """Vertex AI: NATIVE aspect_ratio with edit_image"""
    pil_image = PILImage.open(io.BytesIO(image_bytes))
    print(f"[Vertex AI Edit] Editing with NATIVE {aspect_ratio}")
    
    response = vertex_client.models.edit_image(
        model="imagen-3.0-generate-001",
        prompt=prompt,
        reference_images=[types.RawReferenceImage(referenceImage=pil_image)],
        config=types.EditImageConfig(
            aspectRatio=aspect_ratio,
            numberOfImages=1,
            editMode=types.EditMode.EDIT_MODE_PRODUCT_IMAGE
        )
    )
    
    if not response.generated_images:
        raise Exception("No images generated")
    
    edited_image = response.generated_images[0].image.as_image()
    print(f"[Vertex AI Edit] ✨ Perfect {aspect_ratio}: {edited_image.size}")
    
    buffer = io.BytesIO()
    edited_image.save(buffer, format='PNG', optimize=True)
    buffer.seek(0)
    return buffer.getvalue()


async def _edit_ai_studio(image_bytes: bytes, prompt: str, aspect_ratio: AspectRatio) -> bytes:
    """AI Studio: Multimodal + crop/resize"""
    pil_image = PILImage.open(io.BytesIO(image_bytes))
    
    aspect_hints = {
        "16:9": "Edit for HORIZONTAL 16:9 format",
        "9:16": "Edit for VERTICAL 9:16 format",
        "1:1": "Edit for SQUARE 1:1 format"
    }
    
    enhanced_prompt = f"{prompt}\n\nCOMPOSITION: {aspect_hints[aspect_ratio]}"
    print(f"[AI Studio Edit] Editing with smart prompts")
    
    response = ai_studio_client.models.generate_content(
        model='gemini-2.5-flash-image',
        contents=[enhanced_prompt, pil_image],
        config=types.GenerateContentConfig(response_modalities=['IMAGE'])
    )
    
    for part in response.candidates[0].content.parts:
        if part.inline_data:
            image_bytes = part.inline_data.data
            print(f"[AI Studio Edit] Edited, applying smart resize...")
            return smart_crop_and_resize(image_bytes, aspect_ratio)
    
    raise Exception("No image in response")



