# Hebrew Image Generator - מחולל תמונות בעברית

Image generation tool with Hebrew text overlay for Israeli e-commerce market using Google Imagen (Nano Banana).

## Features

- Generate product images with Google Imagen (Nano Banana)
- Upload product photo OR write text prompt
- Choose format: 16:9 (horizontal) or 9:16 (vertical)
- Add Hebrew text overlay with visual editor
- AI-suggested Hebrew marketing texts
- Smart text positioning
- Export high-quality images

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Google Cloud Setup

#### Enable Vertex AI API:
1. Go to https://console.cloud.google.com
2. Select your project (LironHebVoice)
3. APIs & Services → Library
4. Search: "Vertex AI API" → Enable
5. Use same `google-credentials.json` from TTS setup

#### Get Project ID:
1. Google Cloud Console → Dashboard
2. Copy "Project ID"
3. Add to `.env` file

### 3. Environment Variables

Create `.env` file:
```env
GOOGLE_APPLICATION_CREDENTIALS=google-credentials.json
GOOGLE_PROJECT_ID=your-project-id-here
GOOGLE_LOCATION=us-central1
PORT=8000
```

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
- **Image Generation:** Google Imagen 3 (Nano Banana)
- **Text Overlay:** Pillow (PIL)
- **Text Generation:** GPT-4 (optional)
- **Frontend:** Vanilla HTML/CSS/JS

## Costs (Estimated)

### Google Imagen (Nano Banana):
- 1024x1024 image: ~$0.02-0.04
- Higher resolution: ~$0.08

### Example:
- 1,000 images/month: $20-40
- 10,000 images/month: $200-400

Much cheaper than video generation!

## Workflow

```
1. User uploads product photo OR writes prompt
    ↓
2. Select format (16:9 or 9:16)
    ↓
3. Imagen generates clean product image
    ↓
4. AI suggests Hebrew marketing texts (optional)
    ↓
5. User picks/edits Hebrew text
    ↓
6. Visual editor: position text on image
    ↓
7. Export final image with Hebrew text
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

