"""
Text overlay service for adding text to images with Hebrew support
"""

from PIL import Image, ImageDraw, ImageFont
import io
import os
import glob
from typing import Tuple, Optional


# Default font settings
DEFAULT_FONT_SIZE = 48
DEFAULT_FONT_COLOR = (255, 255, 255, 255)  # White with full opacity
DEFAULT_STROKE_COLOR = (0, 0, 0, 255)  # Black outline
DEFAULT_STROKE_WIDTH = 2

# Try to find system fonts that support Hebrew
HEBREW_FONTS = [
    # Linux fonts (Railway uses Linux)
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/nix/store/*/share/fonts/truetype/DejaVuSans.ttf",
    "/nix/store/*/share/fonts/truetype/DejaVuSans-Bold.ttf",
    # Windows fonts (for local dev)
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
]


def get_hebrew_font(font_size: int, font_family: str = "Arial", bold: bool = False) -> ImageFont.FreeTypeFont:
    """Get a font that supports Hebrew characters"""
    
    # Expand glob patterns in font paths
    expanded_fonts = []
    for font_path in HEBREW_FONTS:
        if '*' in font_path:
            # Expand glob pattern
            expanded_fonts.extend(glob.glob(font_path))
        else:
            expanded_fonts.append(font_path)
    
    # Map font family names to possible font file patterns
    font_patterns = {
        "Arial": ["arial", "liberation"],
        "Arial Black": ["ariblk", "liberation"],
        "Calibri": ["dejavu", "liberation"],  # Fallback to DejaVu/Liberation
        "Tahoma": ["dejavu", "liberation"],
        "Verdana": ["dejavu", "liberation"],
        "Impact": ["dejavu", "liberation"]
    }
    
    # Get patterns for requested font family
    patterns = font_patterns.get(font_family, ["dejavu", "liberation", "arial"])
    
    print(f"[Font Search] Looking for: {font_family} (bold: {bold}, size: {font_size})")
    
    # Try to find font matching family and bold
    for font_path in expanded_fonts:
        if not os.path.exists(font_path):
            continue
            
        font_path_lower = font_path.lower()
        
        # Check if this font matches the requested family
        matches_family = any(pattern.lower() in font_path_lower for pattern in patterns)
        if not matches_family:
            continue
        
        # Check bold requirement (be flexible)
        is_bold_font = "bold" in font_path_lower or "bd" in font_path_lower or "black" in font_path_lower
        if bold and not is_bold_font:
            continue
        if not bold and is_bold_font:
            continue
        
        try:
            font = ImageFont.truetype(font_path, font_size)
            print(f"[Font Search] ✓ Using font: {font_path}")
            return font
        except Exception as e:
            print(f"[Font Search] ✗ Failed to load {font_path}: {e}")
            continue
    
    # Fallback: try ANY TrueType font (ignore family/bold requirements)
    print(f"[Font Search] Could not find {font_family} (bold: {bold}), trying any font...")
    for font_path in expanded_fonts:
        if not os.path.exists(font_path):
            continue
        try:
            font = ImageFont.truetype(font_path, font_size)
            print(f"[Font Search] ✓ Using fallback font: {font_path}")
            return font
        except Exception as e:
            continue
    
    # LAST RESORT: Create a large default font
    print("[Font Search] ERROR: No TrueType fonts found! Using PIL default (will be tiny)")
    # Default font ignores size, but at least return something
    return ImageFont.load_default()


def add_text_to_image(
    image_bytes: bytes,
    text: str,
    position: Tuple[int, int],
    font_family: str = "Arial",
    font_size: int = DEFAULT_FONT_SIZE,
    font_color: Tuple[int, int, int, int] = DEFAULT_FONT_COLOR,
    stroke_color: Optional[Tuple[int, int, int, int]] = DEFAULT_STROKE_COLOR,
    stroke_width: int = DEFAULT_STROKE_WIDTH,
    bold: bool = False
) -> bytes:
    """
    Add text overlay to an image with Hebrew support
    
    Args:
        image_bytes: Original image bytes
        text: Text to add (supports Hebrew RTL)
        position: (x, y) position for text - exact position where user clicked
        font_family: Font family name
        font_size: Font size in pixels
        font_color: RGBA color tuple for text
        stroke_color: RGBA color tuple for text outline (None for no outline)
        stroke_width: Width of text outline
        bold: Use bold font variant
    
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
        font = get_hebrew_font(font_size, font_family, bold)
        
        # Use exact position from user click - NO alignment calculations
        x, y = position
        
        # Ensure text is within image bounds (minimal bounds check)
        x = max(0, min(x, img.width - 10))
        y = max(0, min(y, img.height - 10))
        
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
