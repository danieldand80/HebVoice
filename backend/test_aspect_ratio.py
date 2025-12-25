"""
Test script to check if aspect_ratio works with generate_images API
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load .env from project root
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

def test_generate_images_api():
    """Test new generate_images API with aspect_ratio"""
    print("\n=== Testing generate_images API with aspect_ratio ===")
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("[ERROR] GOOGLE_API_KEY not set")
        return False
    
    client = genai.Client(api_key=api_key)
    
    # Test different aspect ratios
    test_cases = [
        ("16:9", "A red sports car on a highway, horizontal composition"),
        ("9:16", "A tall skyscraper in a modern city, vertical composition"),
        ("1:1", "A cute cat portrait, square composition")
    ]
    
    for aspect_ratio, prompt in test_cases:
        print(f"\n--- Testing aspect_ratio: {aspect_ratio} ---")
        print(f"Prompt: {prompt}")
        
        try:
            # Try new generate_images API
            response = client.models.generate_images(
                model="imagen-3.0-generate-001",  # Imagen 3.0 model
                prompt=prompt,
                config=types.GenerateImagesConfig(
                    aspectRatio=aspect_ratio,
                    numberOfImages=1
                )
            )
            
            print(f"[OK] Response received")
            print(f"[OK] Generated images: {len(response.generated_images)}")
            
            for idx, img in enumerate(response.generated_images):
                # Save image
                pil_image = img.image.as_image()
                filename = f"test_output_{aspect_ratio.replace(':', 'x')}.png"
                pil_image.save(filename)
                print(f"[OK] Image saved: {filename}, size: {pil_image.size}")
            
        except Exception as e:
            print(f"[ERROR] Failed with imagen-3.0-generate-001: {str(e)}")
            print("Trying with gemini-2.5-flash-image...")
            
            try:
                # Fallback to gemini-2.5-flash-image
                response = client.models.generate_images(
                    model="gemini-2.5-flash-image",
                    prompt=prompt,
                    config=types.GenerateImagesConfig(
                        aspectRatio=aspect_ratio,
                        numberOfImages=1
                    )
                )
                
                print(f"[OK] Response received from gemini-2.5-flash-image")
                print(f"[OK] Generated images: {len(response.generated_images)}")
                
                for idx, img in enumerate(response.generated_images):
                    pil_image = img.image.as_image()
                    filename = f"test_output_{aspect_ratio.replace(':', 'x')}_gemini.png"
                    pil_image.save(filename)
                    print(f"[OK] Image saved: {filename}, size: {pil_image.size}")
                    
            except Exception as e2:
                print(f"[ERROR] Also failed with gemini-2.5-flash-image: {str(e2)}")
                import traceback
                traceback.print_exc()
                return False
    
    return True


def test_old_api_with_aspect_ratio():
    """Test if old generate_content API supports aspect_ratio somehow"""
    print("\n=== Testing generate_content API (old method) ===")
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("[ERROR] GOOGLE_API_KEY not set")
        return False
    
    client = genai.Client(api_key=api_key)
    
    prompt = "A red sports car on a highway"
    
    try:
        # Check if GenerateContentConfig has any image-related parameters
        print(f"GenerateContentConfig parameters: {types.GenerateContentConfig.__annotations__}")
        
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=['IMAGE']
            )
        )
        
        for part in response.parts:
            if part.inline_data:
                pil_image = part.as_image()
                print(f"[OK] Old API generated image: {pil_image.size}")
                pil_image.save("test_output_old_api.png")
                print(f"[INFO] Old API doesn't support aspect_ratio parameter")
                return True
        
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 70)
    print("Testing aspect_ratio support in Google Gemini/Imagen APIs")
    print("=" * 70)
    
    # Test 1: New generate_images API
    test1 = test_generate_images_api()
    
    # Test 2: Old generate_content API
    test2 = test_old_api_with_aspect_ratio()
    
    print("\n" + "=" * 70)
    print("Summary:")
    print("=" * 70)
    print(f"generate_images API: {'WORKS' if test1 else 'FAILED'}")
    print(f"generate_content API: {'WORKS (no aspect_ratio)' if test2 else 'FAILED'}")

