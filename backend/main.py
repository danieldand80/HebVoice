from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from pathlib import Path
import uuid
from dotenv import load_dotenv
import base64

from services.imagen_service import generate_image_from_prompt, edit_image_with_prompt
from services.text_overlay_service import add_text_to_image, preview_text_positions
from services.text_generation_service import generate_hebrew_marketing_text

load_dotenv()

app = FastAPI(title="Hebrew Image Generator")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directories
UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Serve frontend
from pathlib import Path
frontend_dir = Path(__file__).parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

@app.get("/")
async def root():
    return FileResponse(str(frontend_dir / "index.html"))

@app.post("/api/generate-image")
async def generate_image(
    prompt: str = Form(default=""),
    aspect_ratio: str = Form(default="16:9"),
    num_images: int = Form(default=4),
    image: UploadFile = File(None)
):
    """Generate image(s) using Imagen (Nano Banana) - Always generates 4 images"""
    try:
        # Check if Google AI API is configured
        if not os.getenv("GOOGLE_API_KEY"):
            raise HTTPException(status_code=500, detail="GOOGLE_API_KEY not configured")
        
        # Always generate 4 images
        num_images = 4
        
        # Validate: either prompt or image must be provided
        if not prompt.strip() and not image:
            raise HTTPException(status_code=400, detail="Either prompt or image must be provided")
        
        # Generate image
        if image and image.filename:
            # User uploaded image - read bytes directly
            try:
                # Reset file pointer to beginning
                await image.seek(0)
                uploaded_image_bytes = await image.read()
                
                print(f"[DEBUG] Uploaded image bytes size: {len(uploaded_image_bytes)}")
                print(f"[DEBUG] Image filename: {image.filename}")
                print(f"[DEBUG] Image content_type: {image.content_type}")
                
                if len(uploaded_image_bytes) == 0:
                    raise HTTPException(status_code=400, detail="Uploaded image is empty")
                
                # Validate it's actually an image
                from PIL import Image as PILImageValidation
                import io as io_validation
                try:
                    test_img = PILImageValidation.open(io_validation.BytesIO(uploaded_image_bytes))
                    print(f"[DEBUG] Image validated: {test_img.size}, mode: {test_img.mode}")
                except Exception as e:
                    raise HTTPException(status_code=400, detail=f"Invalid image file: {str(e)}")
                
                if prompt and prompt.strip():
                    # Edit the uploaded image based on prompt
                    print(f"[DEBUG] Editing image with prompt: {prompt[:50]}...")
                    image_list = await edit_image_with_prompt(uploaded_image_bytes, prompt, aspect_ratio, num_images)
                else:
                    # No prompt - use uploaded image as-is
                    print(f"[DEBUG] Using uploaded image as-is (no prompt)")
                    image_list = [uploaded_image_bytes]
            except HTTPException:
                raise
            except Exception as e:
                import traceback
                print(f"[ERROR] Failed to process uploaded image: {str(e)}\n{traceback.format_exc()}")
                raise HTTPException(status_code=400, detail=f"Failed to process uploaded image: {str(e)}")
        else:
            # No image uploaded - generate new image from prompt
            if not prompt or not prompt.strip():
                raise HTTPException(status_code=400, detail="Either image or prompt is required")
            
            image_list = await generate_image_from_prompt(prompt, aspect_ratio, num_images)
        
        # Save all generated images
        generated_images = []
        for idx, image_bytes in enumerate(image_list):
            image_id = f"{str(uuid.uuid4())[:8]}_{idx}"
            output_path = OUTPUT_DIR / f"{image_id}.png"
            
            with open(output_path, "wb") as f:
                f.write(image_bytes)
            
            # Get image dimensions
            from PIL import Image
            import io
            img = Image.open(io.BytesIO(image_bytes))
            width, height = img.size
            
            # Return image as base64 for preview
            image_base64 = base64.b64encode(image_bytes).decode()
            
            generated_images.append({
                "image_id": image_id,
                "image_url": f"/api/image/{image_id}",
                "image_base64": f"data:image/png;base64,{image_base64}",
                "width": width,
                "height": height
            })
        
        return {
            "success": True,
            "images": generated_images,
            "count": len(generated_images)
        }
        
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        print(f"ERROR: {error_detail}")
        
        # User-friendly error messages
        error_msg = str(e)
        if "No content in candidate" in error_msg or "NO_IMAGE" in error_msg:
            error_msg = "Failed to generate image. This may be due to:\n- Prompt being blocked by safety filters\n- Temporary API issues\n- Try a more specific and descriptive prompt"
        
        raise HTTPException(status_code=500, detail=error_msg)

@app.post("/api/suggest-texts")
async def suggest_texts(
    image_id: str = Form(...),
    product_description: str = Form(default=""),
    language: str = Form(default="he")
):
    """Generate marketing text suggestions based on image analysis"""
    try:
        # Load image
        image_path = OUTPUT_DIR / f"{image_id}.png"
        if not image_path.exists():
            raise HTTPException(status_code=404, detail="Image not found")
        
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        
        # Generate text suggestions using Gemini vision
        texts = await generate_hebrew_marketing_text(image_bytes, product_description, language=language)
        
        return {
            "success": True,
            "texts": texts
        }
        
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        print(f"ERROR: {error_detail}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/preview-text-positions")
async def get_text_positions(
    image_id: str = Form(...),
    text: str = Form(...),
    font_size: int = Form(default=48)
):
    """Get suggested text positions for an image"""
    try:
        # Load image
        image_path = OUTPUT_DIR / f"{image_id}.png"
        if not image_path.exists():
            raise HTTPException(status_code=404, detail="Image not found")
        
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        
        # Get position suggestions
        positions = preview_text_positions(image_bytes, text, font_size)
        
        return {
            "success": True,
            "positions": positions
        }
        
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        print(f"ERROR: {error_detail}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/add-text")
async def add_text_endpoint(
    image_id: str = Form(...),
    text: str = Form(...),
    x: int = Form(...),
    y: int = Form(...),
    font_family: str = Form(default="Arial"),
    font_size: int = Form(default=48),
    font_color: str = Form(default="255,255,255,255"),
    stroke_color: str = Form(default="0,0,0,255"),
    stroke_width: int = Form(default=2),
    bold: bool = Form(default=False),
    canvas_width: int = Form(default=0),
    canvas_height: int = Form(default=0)
):
    """Add Hebrew text to generated image"""
    try:
        # Load original image
        image_path = OUTPUT_DIR / f"{image_id}.png"
        if not image_path.exists():
            raise HTTPException(status_code=404, detail="Image not found")
        
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        
        # Parse color strings (R,G,B,A)
        try:
            font_rgba = tuple(int(c) for c in font_color.split(','))
            stroke_rgba = tuple(int(c) for c in stroke_color.split(',')) if stroke_color else None
        except:
            font_rgba = (255, 255, 255, 255)
            stroke_rgba = (0, 0, 0, 255)
        
        # Check actual image size
        from PIL import Image as PILImage
        import io
        img_check = PILImage.open(io.BytesIO(image_bytes))
        actual_width, actual_height = img_check.size
        
        print(f"[Text Overlay] ========== DEBUG ==========")
        print(f"[Text Overlay] Canvas (from frontend): {canvas_width}x{canvas_height}")
        print(f"[Text Overlay] Image (actual file): {actual_width}x{actual_height}")
        print(f"[Text Overlay] Font size: {font_size}px")
        print(f"[Text Overlay] Position from frontend: ({x}, {y})")
        print(f"[Text Overlay] Stroke width: {stroke_width}px")
        print(f"[Text Overlay] Text: '{text}'")
        print(f"[Text Overlay] Font family: {font_family}")
        
        # Canvas должен быть равен изображению - масштабирование НЕ нужно!
        # Если размеры не совпадают - это ошибка
        if canvas_width > 0 and abs(canvas_width - actual_width) > 10:
            print(f"[WARNING] Canvas size mismatch! This should not happen.")
        
        # Add text overlay
        result_bytes = add_text_to_image(
            image_bytes=image_bytes,
            text=text,
            position=(x, y),
            font_family=font_family,
            font_size=font_size,
            font_color=font_rgba,
            stroke_color=stroke_rgba,
            stroke_width=stroke_width,
            bold=bold
        )
        
        # Save result with new ID
        result_id = f"{image_id}_text"
        result_path = OUTPUT_DIR / f"{result_id}.png"
        with open(result_path, "wb") as f:
            f.write(result_bytes)
        
        # Return as base64
        result_base64 = base64.b64encode(result_bytes).decode()
        
        return {
            "success": True,
            "image_id": result_id,
            "image_url": f"/api/image/{result_id}",
            "image_base64": f"data:image/png;base64,{result_base64}"
        }
        
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        print(f"ERROR: {error_detail}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/image/{image_id}")
async def get_image(image_id: str):
    """Get generated image"""
    image_path = OUTPUT_DIR / f"{image_id}.png"
    
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    
    return FileResponse(
        image_path,
        media_type="image/png",
        filename=f"image_{image_id}.png"
    )

@app.get("/api/download/{image_id}")
async def download_image(image_id: str):
    """Download final image"""
    # Try final version first
    image_path = OUTPUT_DIR / f"{image_id}_final.png"
    
    if not image_path.exists():
        # Fallback to original
        image_path = OUTPUT_DIR / f"{image_id}.png"
    
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    
    return FileResponse(
        image_path,
        media_type="image/png",
        filename=f"product_image_{image_id}.png",
        headers={"Content-Disposition": f"attachment; filename=product_image_{image_id}.png"}
    )

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    print(f"Starting server on port {port}...")
    print(f"GOOGLE_API_KEY configured: {'Yes' if os.getenv('GOOGLE_API_KEY') else 'No'}")
    
    # List available fonts at startup
    import glob
    font_dirs = [
        "/usr/share/fonts/truetype/**/*.ttf",
        "/nix/store/*/share/fonts/**/*.ttf",
        "C:\\Windows\\Fonts\\*.ttf"
    ]
    print("\n[Font Check] Searching for available fonts...")
    found_fonts = []
    for pattern in font_dirs:
        found_fonts.extend(glob.glob(pattern, recursive=True))
    
    if found_fonts:
        print(f"[Font Check] Found {len(found_fonts)} fonts:")
        for font in found_fonts[:10]:  # Show first 10
            print(f"  - {font}")
        if len(found_fonts) > 10:
            print(f"  ... and {len(found_fonts) - 10} more")
    else:
        print("[Font Check] WARNING: No fonts found! Text overlay will use tiny default font.")
    print()
    
    uvicorn.run(app, host="0.0.0.0", port=port)

