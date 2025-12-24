# Hebrew Image Generator - מחולל תמונות בעברית

Image generation tool with Hebrew text overlay for Israeli e-commerce market using **Gemini 2.5 Flash Image (Nano Banana)**.

## Features

- 🎨 **text2img** - Generate product images from text descriptions
- 🖼️ **img2img** - Edit existing photos (change backgrounds, modify images)
- Upload product photo OR write text prompt
- Choose format: 16:9 (horizontal) or 9:16 (vertical)
- Add Hebrew text overlay with visual editor
- AI-suggested Hebrew marketing texts (coming soon)
- Smart text positioning
- Export high-quality images

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Google AI Studio Setup

#### Get API Key:
1. Go to https://aistudio.google.com/
2. Click "Get API Key"
3. Create new API key or use existing
4. Copy the API key

### 3. Environment Variables

Create `.env` file:
```env
GOOGLE_API_KEY=your-google-ai-studio-api-key-here
PORT=8000
```

**For Railway deployment:**
Add `GOOGLE_API_KEY` environment variable in Railway dashboard.

**Optional (for AI text suggestions):**
```env
OPENAI_API_KEY=your-openai-key
```

### 4. Run Server

```bash
cd backend
python main.py
```

Visit: http://localhost:8000

## API Endpoints

- `POST /api/generate-image` - Generate image with Imagen
- `POST /api/suggest-texts` - Generate Hebrew marketing texts
- `POST /api/add-text` - Add Hebrew text overlay
- `GET /api/download/{image_id}` - Download final image

## Tech Stack

- **Backend:** FastAPI (Python)
- **Image Generation:** Gemini 2.5 Flash Image (Nano Banana)
- **Text Overlay:** Pillow (PIL)
- **Text Generation:** GPT-4 (optional)
- **Frontend:** Vanilla HTML/CSS/JS
- **Deployment:** Railway

## Costs (Estimated)

### Gemini 2.5 Flash Image (Nano Banana):
- ~$0.039 per image (1290 tokens/image)
- Supports both text2img and img2img modes

### Example:
- 1,000 images/month: ~$39
- 10,000 images/month: ~$390

Much cheaper than video generation!

## Workflow

### Mode 1: Generate from text (text2img)
```
1. Write prompt: "red sneakers on white background"
    ↓
2. Select format (16:9 or 9:16)
    ↓
3. Gemini 2.5 Flash generates image
    ↓
4. Add Hebrew text overlay
    ↓
5. Export final image
```

### Mode 2: Edit existing photo (img2img)
```
1. Upload product photo (e.g., sneakers)
    ↓
2. Write edit instruction: "change background to modern shop"
    ↓
3. Select format (16:9 or 9:16)
    ↓
4. Gemini 2.5 Flash edits image (keeps product, changes background)
    ↓
5. Add Hebrew text overlay
    ↓
6. Export final image
```

## Features TODO

- [ ] Drag-and-drop text positioning
- [ ] Multiple text layers
- [ ] Custom Hebrew fonts
- [ ] Templates library
- [ ] Batch processing
- [ ] User authentication

## Troubleshooting

### Error: "GOOGLE_PROJECT_ID not set"
- Check `.env` file has `GOOGLE_PROJECT_ID=your-actual-project-id`
- Copy Project ID from Google Cloud Console dashboard

### Error: "Vertex AI API not enabled"
- Go to Google Cloud Console
- Enable Vertex AI API
- Wait 2-3 minutes for activation

### Hebrew text not displaying
- System needs Hebrew font support
- Will add custom Hebrew font file in next update

## License

Commercial use allowed.



