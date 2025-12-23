from PIL import Image, ImageDraw, ImageFont
import io
from typing import List, Dict, Tuple

class TextOverlay:
    def __init__(self, image_bytes: bytes):
        """Initialize with image bytes"""
        self.image = Image.open(io.BytesIO(image_bytes)).convert('RGBA')
        self.width, self.height = self.image.size
    
    def add_text(
        self,
        text: str,
        position: Tuple[int, int],
        font_size: int = 60,
        color: str = "#FFFFFF",
        stroke_color: str = "#000000",
        stroke_width: int = 2,
        font_path: str = None
    ) -> None:
        """Add Hebrew text to image"""
        
        # Create drawing context
        draw = ImageDraw.Draw(self.image)
        
        # Load font (you'll need to add Hebrew font file)
        try:
            if font_path:
                font = ImageFont.truetype(font_path, font_size)
            else:
                # Try to use system font
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
        except:
            # Fallback to default
            font = ImageFont.load_default()
        
        # Reverse Hebrew text for proper RTL display
        # Note: PIL handles this automatically for most Hebrew fonts
        
        # Draw text with stroke (outline)
        x, y = position
        
        if stroke_width > 0:
            # Draw stroke
            for adj_x in range(-stroke_width, stroke_width + 1):
                for adj_y in range(-stroke_width, stroke_width + 1):
                    draw.text((x + adj_x, y + adj_y), text, font=font, fill=stroke_color)
        
        # Draw main text
        draw.text((x, y), text, font=font, fill=color)
    
    def get_image_bytes(self, format: str = "PNG") -> bytes:
        """Export image as bytes"""
        output = io.BytesIO()
        
        # Convert RGBA to RGB if saving as JPEG
        if format.upper() == "JPEG":
            rgb_image = Image.new('RGB', self.image.size, (255, 255, 255))
            rgb_image.paste(self.image, mask=self.image.split()[3] if self.image.mode == 'RGBA' else None)
            rgb_image.save(output, format=format, quality=95)
        else:
            self.image.save(output, format=format)
        
        return output.getvalue()


async def add_hebrew_text_to_image(
    image_bytes: bytes,
    text: str,
    x: int,
    y: int,
    font_size: int = 60,
    color: str = "#FFFFFF",
    stroke_color: str = "#000000",
    stroke_width: int = 2
) -> bytes:
    """Add Hebrew text overlay to image"""
    
    overlay = TextOverlay(image_bytes)
    overlay.add_text(
        text=text,
        position=(x, y),
        font_size=font_size,
        color=color,
        stroke_color=stroke_color,
        stroke_width=stroke_width
    )
    
    return overlay.get_image_bytes()


async def suggest_text_positions(
    width: int,
    height: int,
    aspect_ratio: str
) -> List[Dict]:
    """Suggest smart text positions based on image size"""
    
    if aspect_ratio == "9:16":
        # Vertical format - suggest top, middle, bottom
        positions = [
            {"name": "top", "x": width // 2, "y": 100},
            {"name": "middle", "x": width // 2, "y": height // 2},
            {"name": "bottom", "x": width // 2, "y": height - 200}
        ]
    else:
        # Horizontal format
        positions = [
            {"name": "top_left", "x": 100, "y": 100},
            {"name": "top_center", "x": width // 2, "y": 100},
            {"name": "center", "x": width // 2, "y": height // 2},
            {"name": "bottom_center", "x": width // 2, "y": height - 150}
        ]
    
    return positions

