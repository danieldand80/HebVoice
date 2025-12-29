"""
Text generation service using Gemini to analyze images and suggest Hebrew text
"""

import os
import base64
from google import genai
from google.genai import types

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
client = None

if GOOGLE_API_KEY:
    client = genai.Client(api_key=GOOGLE_API_KEY)

async def generate_hebrew_marketing_text(
    image_bytes: bytes,
    product_description: str = "",
    style: str = "promotional"
) -> list[str]:
    """
    Generate Hebrew marketing text suggestions using Gemini vision model
    Analyzes the image to suggest relevant text overlays
    """
    
    if not client or not GOOGLE_API_KEY:
        # Fallback templates if no API key
        return [
            "מבצע מיוחד!",
            "הזדמנות אחרונה",
            "קנה עכשיו",
            "חדש!",
            "מחיר מיוחד"
        ]
    
    try:
        # Prepare prompt for Gemini
        context = f"Product context: {product_description}" if product_description else ""
        
        prompt = f"""Analyze this product image and suggest 5 short Hebrew marketing texts that would work well as overlays on this image.

{context}

Requirements:
- Very short (2-5 words in Hebrew)
- Catchy and promotional
- Suitable for social media ads and product images
- Native Hebrew, proper grammar
- Consider the image content, colors, and composition
- Texts should stand out on the image

Return ONLY the Hebrew texts, one per line, without numbers or bullets."""

        # Convert image to base64 for Gemini
        image_b64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # Call Gemini with vision
        response = client.models.generate_content(
            model='gemini-2.0-flash-exp',  # Use Gemini 2.0 Flash for vision
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_bytes(
                            data=image_bytes,
                            mime_type="image/png"
                        ),
                        types.Part.from_text(text=prompt)
                    ]
                )
            ]
        )
        
        # Parse response
        if response and response.text:
            texts = [line.strip() for line in response.text.strip().split('\n') if line.strip()]
            # Filter out any numbered or bulleted lines
            texts = [t.lstrip('0123456789.-*•● ') for t in texts]
            texts = [t for t in texts if t and len(t) > 0]
            
            print(f"[Gemini Text Suggestions] Generated {len(texts)} suggestions from image analysis")
            return texts[:5]
        
        # Fallback if no response
        return [
            "מבצע מיוחד!",
            "חדש!",
            "קנה עכשיו"
        ]
    
    except Exception as e:
        print(f"[Gemini Text Suggestions] Error: {e}")
        # Fallback on error
        return [
            "מבצע מיוחד!",
            "הזדמנות אחרונה",
            "קנה עכשיו",
            "חדש!",
            "מחיר מיוחד"
        ]










