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
from services.text_overlay_service import add_hebrew_text_to_image, suggest_text_positions
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
    prompt: str = Form(...),
    aspect_ratio: str = Form(default="16:9"),
    image: UploadFile = File(None)
):
    """Generate image using Imagen (Nano Banana)"""
    try:
        # Check if Imagen is configured
        if not os.getenv("GOOGLE_PROJECT_ID"):
            raise HTTPException(status_code=500, detail="GOOGLE_PROJECT_ID not configured")
        
        job_id = str(uuid.uuid4())
        
        # Generate image
        if image:
            # User uploaded image - read bytes directly
            uploaded_image_bytes = await image.read()
            
            if prompt and prompt.strip():
                # Edit the uploaded image based on prompt
                image_bytes = await edit_image_with_prompt(uploaded_image_bytes, prompt, aspect_ratio)
            else:
                # No prompt - use uploaded image as-is
                image_bytes = uploaded_image_bytes
        else:
            # No image uploaded - generate new image from prompt
            if not prompt or not prompt.strip():
                raise HTTPException(status_code=400, detail="Either image or prompt is required")
            
            image_bytes = await generate_image_from_prompt(prompt, aspect_ratio)
        
        # Save generated image
        output_path = OUTPUT_DIR / f"{job_id}.png"
        with open(output_path, "wb") as f:
            f.write(image_bytes)
        
        # Get image dimensions for text positioning
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(image_bytes))
        width, height = img.size
        
        # Suggest text positions
        positions = await suggest_text_positions(width, height, aspect_ratio)
        
        # Return image as base64 for preview
        image_base64 = base64.b64encode(image_bytes).decode()
        
        return {
            "success": True,
            "image_id": job_id,
            "image_url": f"/api/image/{job_id}",
            "image_base64": f"data:image/png;base64,{image_base64}",
            "width": width,
            "height": height,
            "suggested_positions": positions
        }
        
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        print(f"ERROR: {error_detail}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/suggest-texts")
async def suggest_texts(
    product_description: str = Form(...)
):
    """Generate Hebrew marketing text suggestions"""
    try:
        texts = await generate_hebrew_marketing_text(product_description)
        
        return {
            "success": True,
            "texts": texts
        }
        
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        print(f"ERROR: {error_detail}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/add-text")
async def add_text_to_image(
    image_id: str = Form(...),
    text: str = Form(...),
    x: int = Form(...),
    y: int = Form(...),
    font_size: int = Form(default=60),
    color: str = Form(default="#FFFFFF"),
    stroke_color: str = Form(default="#000000"),
    stroke_width: int = Form(default=2)
):
    """Add Hebrew text to generated image"""
    try:
        # Load original image
        image_path = OUTPUT_DIR / f"{image_id}.png"
        if not image_path.exists():
            raise HTTPException(status_code=404, detail="Image not found")
        
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        
        # Add text overlay
        result_bytes = await add_hebrew_text_to_image(
            image_bytes=image_bytes,
            text=text,
            x=x,
            y=y,
            font_size=font_size,
            color=color,
            stroke_color=stroke_color,
            stroke_width=stroke_width
        )
        
        # Save result
        result_path = OUTPUT_DIR / f"{image_id}_final.png"
        with open(result_path, "wb") as f:
            f.write(result_bytes)
        
        # Return as base64
        result_base64 = base64.b64encode(result_bytes).decode()
        
        return {
            "success": True,
            "image_url": f"/api/image/{image_id}_final",
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
    uvicorn.run(app, host="0.0.0.0", port=port)

