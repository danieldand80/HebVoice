"""
Text overlay service for adding text to images with Hebrew support
"""

from PIL import Image, ImageDraw, ImageFont
import io
import os
from typing import Tuple, Optional


# Default font settings
DEFAULT_FONT_SIZE = 48
DEFAULT_FONT_COLOR = (255, 255, 255, 255)  # White with full opacity
DEFAULT_STROKE_COLOR = (0, 0, 0, 255)  # Black outline
DEFAULT_STROKE_WIDTH = 2

# Try to find system fonts that support Hebrew
HEBREW_FONTS = [
    # Windows fonts
    "C:\\Windows\\Fonts\\arial.ttf",
    "C:\\Windows\\Fonts\\arialbd.ttf",
    "C:\\Windows\\Fonts\\calibri.ttf",
    "C:\\Windows\\Fonts\\calibrib.ttf",
    "C:\\Windows\\Fonts\\tahoma.ttf",
    "C:\\Windows\\Fonts\\tahomabd.ttf",
    "C:\\Windows\\Fonts\\verdana.ttf",
    "C:\\Windows\\Fonts\\verdanab.ttf",
    # macOS fonts
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/Library/Fonts/Arial.ttf",
    # Linux fonts
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
]


def get_hebrew_font(font_size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Get a font that supports Hebrew characters"""
    
    # Try to find an available font
    for font_path in HEBREW_FONTS:
        if os.path.exists(font_path):
            try:
                if bold and "bold" not in font_path.lower() and "bd" not in font_path.lower():
                    # Skip non-bold fonts if bold requested
                    continue
                font = ImageFont.truetype(font_path, font_size)
                print(f"[Text Overlay] Using font: {font_path}")
                return font
            except Exception as e:
                print(f"[Text Overlay] Failed to load font {font_path}: {e}")
                continue
    
    # Fallback to default font (might not support Hebrew well)
    print("[Text Overlay] WARNING: Using default font (Hebrew support may be limited)")
    return ImageFont.load_default()


def add_text_to_image(
    image_bytes: bytes,
    text: str,
    position: Tuple[int, int],
    font_size: int = DEFAULT_FONT_SIZE,
    font_color: Tuple[int, int, int, int] = DEFAULT_FONT_COLOR,
    stroke_color: Optional[Tuple[int, int, int, int]] = DEFAULT_STROKE_COLOR,
    stroke_width: int = DEFAULT_STROKE_WIDTH,
    bold: bool = False,
    align: str = "right"  # "left", "center", "right" (right for Hebrew)
) -> bytes:
    """
    Add text overlay to an image with Hebrew support
    
    Args:
        image_bytes: Original image bytes
        text: Text to add (supports Hebrew RTL)
        position: (x, y) position for text (top-left corner)
        font_size: Font size in pixels
        font_color: RGBA color tuple for text
        stroke_color: RGBA color tuple for text outline (None for no outline)
        stroke_width: Width of text outline
        bold: Use bold font variant
        align: Text alignment ("left", "center", "right")
    
    Returns:
        Modified image bytes
    """
    
    try:
        # Load image
        img = Image.open(io.BytesIO(image_bytes))
        
        # Convert to RGBA for transparency support
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # Create a transparent overlay for text
        txt_layer = Image.new('RGBA', img.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(txt_layer)
        
        # Get font
        font = get_hebrew_font(font_size, bold)
        
        # Get text bounding box for positioning
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Adjust position based on alignment RELATIVE TO IMAGE
        x_offset, y = position
        
        if align == "left":
            # Left align: x_offset is from left edge
            x = x_offset
        elif align == "center":
            # Center align: center the text on image, x_offset is ignored
            x = (img.width - text_width) // 2
        elif align == "right":
            # Right align: x_offset is from right edge (margin)
            x = img.width - x_offset - text_width
        else:
            # Default to left
            x = x_offset
        
        # Ensure text is within image bounds
        x = max(0, min(x, img.width - text_width))
        y = max(0, min(y, img.height - text_height))
        
        # Draw text with outline (stroke) if specified
        if stroke_color and stroke_width > 0:
            draw.text(
                (x, y),
                text,
                font=font,
                fill=font_color,
                stroke_fill=stroke_color,
                stroke_width=stroke_width
            )
        else:
            draw.text(
                (x, y),
                text,
                font=font,
                fill=font_color
            )
        
        # Composite the text layer onto the original image
        img = Image.alpha_composite(img, txt_layer)
        
        # Convert back to RGB if needed
        if img.mode == 'RGBA':
            # Create white background
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])  # Use alpha channel as mask
            img = background
        
        # Save to bytes
        output = io.BytesIO()
        img.save(output, format='PNG')
        output.seek(0)
        
        print(f"[Text Overlay] Added text '{text}' at position {position}")
        return output.getvalue()
    
    except Exception as e:
        print(f"[Text Overlay] Error: {e}")
        raise Exception(f"Failed to add text to image: {str(e)}")


def preview_text_positions(
    image_bytes: bytes,
    text: str,
    font_size: int = DEFAULT_FONT_SIZE
) -> list[dict]:
    """
    Suggest good positions for text based on image content
    Returns list of suggested positions with coordinates
    """
    
    try:
        img = Image.open(io.BytesIO(image_bytes))
        width, height = img.size
        
        # Get font to calculate text dimensions
        font = get_hebrew_font(font_size)
        draw = ImageDraw.Draw(img)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Suggest positions (avoid edges)
        margin = 50
        suggestions = [
            {"name": "Top Center", "position": [width // 2, margin + text_height]},
            {"name": "Top Right", "position": [width - margin, margin + text_height]},
            {"name": "Top Left", "position": [margin + text_width, margin + text_height]},
            {"name": "Center", "position": [width // 2, height // 2]},
            {"name": "Bottom Center", "position": [width // 2, height - margin - text_height]},
            {"name": "Bottom Right", "position": [width - margin, height - margin - text_height]},
            {"name": "Bottom Left", "position": [margin + text_width, height - margin - text_height]},
        ]
        
        return suggestions
    
    except Exception as e:
        print(f"[Text Overlay] Error previewing positions: {e}")
        return []
