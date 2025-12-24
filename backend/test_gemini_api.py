"""
Simple test script to verify Gemini 2.5 Flash Image API is working correctly.
Based on official Google documentation: https://ai.google.dev/gemini-api/docs/image-generation
"""

import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image
import io

load_dotenv()

def test_text_to_image():
    """Test text-to-image generation (text2img)"""
    print("\n=== Testing Text-to-Image Generation ===")
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("[ERROR] GOOGLE_API_KEY not set in .env file")
        return False
    
    print(f"[OK] API Key found: {api_key[:10]}...")
    
    try:
        client = genai.Client(api_key=api_key)
        print("[OK] Client initialized")
        
        prompt = "Create a picture of a futuristic banana with neon lights in a cyberpunk city."
        print(f"[OK] Generating image with prompt: '{prompt}'")
        
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=['IMAGE']
            )
        )
        
        print(f"[OK] Response received. Parts: {len(response.parts)}")
        
        # Extract image
        for part in response.parts:
            if part.inline_data:
                print("[OK] Image found in response")
                
                # Use as_image() method from official documentation
                pil_image = part.as_image()
                print(f"[OK] Image extracted: {pil_image.size}, mode: {pil_image.mode}")
                
                # Save test image
                pil_image.save("test_output.png")
                print("[OK] Image saved to test_output.png")
                
                return True
        
        print("[ERROR] No image found in response")
        return False
        
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_image_to_image():
    """Test image-to-image editing (img2img)"""
    print("\n=== Testing Image-to-Image Editing ===")
    
    # First check if test_output.png exists
    if not os.path.exists("test_output.png"):
        print("[SKIP] Skipping img2img test - no test image available")
        print("       Run text-to-image test first to generate test_output.png")
        return True
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("[ERROR] GOOGLE_API_KEY not set in .env file")
        return False
    
    try:
        client = genai.Client(api_key=api_key)
        print("[OK] Client initialized")
        
        # Load test image
        pil_image = Image.open("test_output.png")
        print(f"[OK] Test image loaded: {pil_image.size}, mode: {pil_image.mode}")
        
        prompt = "Make the background pink instead of dark"
        print(f"[OK] Editing image with prompt: '{prompt}'")
        
        # Edit image using multimodal content: [prompt, image]
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=[prompt, pil_image],
            config=types.GenerateContentConfig(
                response_modalities=['IMAGE']
            )
        )
        
        print(f"[OK] Response received. Parts: {len(response.parts)}")
        
        # Extract edited image
        for part in response.parts:
            if part.inline_data:
                print("[OK] Edited image found in response")
                
                # Use as_image() method
                edited_image = part.as_image()
                print(f"[OK] Image extracted: {edited_image.size}, mode: {edited_image.mode}")
                
                # Save edited image
                edited_image.save("test_output_edited.png")
                print("[OK] Edited image saved to test_output_edited.png")
                
                return True
        
        print("[ERROR] No image found in response")
        return False
        
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Gemini 2.5 Flash Image API Test")
    print("=" * 60)
    
    # Test 1: Text-to-Image
    text2img_success = test_text_to_image()
    
    # Test 2: Image-to-Image
    img2img_success = test_image_to_image()
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary:")
    print("=" * 60)
    print(f"Text-to-Image: {'PASS' if text2img_success else 'FAIL'}")
    print(f"Image-to-Image: {'PASS' if img2img_success else 'FAIL'}")
    print()
    
    if text2img_success and img2img_success:
        print("[SUCCESS] All tests passed! API is working correctly.")
    else:
        print("[WARNING] Some tests failed. Check the error messages above.")

