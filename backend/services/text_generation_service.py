from openai import AsyncOpenAI
import os

client = None
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if OPENAI_API_KEY:
    client = AsyncOpenAI(api_key=OPENAI_API_KEY)

async def generate_hebrew_marketing_text(
    product_description: str,
    style: str = "promotional"
) -> list[str]:
    """Generate Hebrew marketing text suggestions using GPT-4"""
    
    if not client:
        # Fallback templates if no OpenAI key
        return [
            "מבצע מיוחד!",
            "הזדמנות אחרונה",
            "קנה עכשיו",
            "המוצר הכי טוב",
            "מחיר מיוחד"
        ]
    
    prompt = f"""Generate 5 short Hebrew marketing texts for this product: {product_description}

Style: {style}
Requirements:
- Short (2-5 words in Hebrew)
- Catchy and promotional
- Suitable for social media ads
- Native Hebrew, proper grammar

Return only the Hebrew texts, one per line."""

    try:
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a Hebrew marketing copywriter."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        
        texts = response.choices[0].message.content.strip().split('\n')
        texts = [t.strip() for t in texts if t.strip()]
        
        return texts[:5]
    
    except Exception as e:
        # Fallback on error
        return [
            "מבצע מיוחד!",
            "הזדמנות אחרונה",
            "קנה עכשיו"
        ]







