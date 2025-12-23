let currentImageId = null;
let currentImageData = null;
let textPosition = { x: 0, y: 0 };

// Elements
const imageForm = document.getElementById('imageForm');
const imageInput = document.getElementById('image');
const imagePreview = document.getElementById('imagePreview');
const generateBtn = document.getElementById('generateBtn');
const generateBtnText = document.getElementById('generateBtnText');
const generateLoader = document.getElementById('generateLoader');

const step1 = document.getElementById('step1');
const step2 = document.getElementById('step2');

const generatedImage = document.getElementById('generatedImage');
const hebrewTextInput = document.getElementById('hebrewText');
const fontSizeInput = document.getElementById('fontSize');
const fontSizeValue = document.getElementById('fontSizeValue');
const textColorInput = document.getElementById('textColor');
const strokeColorInput = document.getElementById('strokeColor');

const suggestTextsBtn = document.getElementById('suggestTextsBtn');
const textSuggestions = document.getElementById('textSuggestions');
const suggestedPositions = document.getElementById('suggestedPositions');

const addTextBtn = document.getElementById('addTextBtn');
const downloadBtn = document.getElementById('downloadBtn');
const startOverBtn = document.getElementById('startOverBtn');

const errorDiv = document.getElementById('error');
const successDiv = document.getElementById('success');

// Image preview
imageInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            imagePreview.innerHTML = `<img src="${e.target.result}" alt="Preview" style="max-width: 300px; border-radius: 8px; margin-top: 10px;">`;
        };
        reader.readAsDataURL(file);
    }
});

// Font size slider
fontSizeInput.addEventListener('input', (e) => {
    fontSizeValue.textContent = e.target.value;
});

// Generate image
imageForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = new FormData(imageForm);
    
    generateBtn.disabled = true;
    generateBtnText.style.display = 'none';
    generateLoader.style.display = 'inline-block';
    hideMessages();
    
    try {
        const response = await fetch('/api/generate-image', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'שגיאה ביצירת התמונה');
        }
        
        const data = await response.json();
        
        currentImageId = data.image_id;
        currentImageData = data;
        
        // Show step 2
        step1.style.display = 'none';
        step2.style.display = 'block';
        
        // Display generated image
        generatedImage.src = data.image_base64;
        
        // Show suggested positions
        displaySuggestedPositions(data.suggested_positions);
        
        showSuccess('התמונה נוצרה בהצלחה! עכשיו הוסף טקסט בעברית');
        
    } catch (error) {
        showError(error.message);
    } finally {
        generateBtn.disabled = false;
        generateBtnText.style.display = 'inline';
        generateLoader.style.display = 'none';
    }
});

// Suggest texts
suggestTextsBtn.addEventListener('click', async () => {
    const prompt = document.getElementById('prompt').value;
    
    if (!prompt) {
        showError('נא להזין תיאור מוצר תחילה');
        return;
    }
    
    suggestTextsBtn.disabled = true;
    suggestTextsBtn.textContent = '⏳ מייצר...';
    
    try {
        const formData = new FormData();
        formData.append('product_description', prompt);
        
        const response = await fetch('/api/suggest-texts', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('שגיאה ביצירת טקסטים');
        }
        
        const data = await response.json();
        
        // Display suggestions
        textSuggestions.innerHTML = '';
        data.texts.forEach(text => {
            const btn = document.createElement('button');
            btn.className = 'text-suggestion';
            btn.textContent = text;
            btn.onclick = () => {
                hebrewTextInput.value = text;
            };
            textSuggestions.appendChild(btn);
        });
        
    } catch (error) {
        showError(error.message);
    } finally {
        suggestTextsBtn.disabled = false;
        suggestTextsBtn.textContent = '💡 הצע טקסטים';
    }
});

// Display suggested positions
function displaySuggestedPositions(positions) {
    suggestedPositions.innerHTML = '';
    
    positions.forEach(pos => {
        const btn = document.createElement('button');
        btn.className = 'position-btn';
        btn.textContent = `${pos.name} (${pos.x}, ${pos.y})`;
        btn.onclick = () => {
            textPosition = { x: pos.x, y: pos.y };
            showSuccess(`מיקום נבחר: ${pos.name}`);
        };
        suggestedPositions.appendChild(btn);
    });
    
    // Set default position
    if (positions.length > 0) {
        textPosition = { x: positions[0].x, y: positions[0].y };
    }
}

// Add text to image
addTextBtn.addEventListener('click', async () => {
    const text = hebrewTextInput.value.trim();
    
    if (!text) {
        showError('נא להזין טקסט בעברית');
        return;
    }
    
    if (!currentImageId) {
        showError('נא ליצור תמונה תחילה');
        return;
    }
    
    addTextBtn.disabled = true;
    addTextBtn.textContent = '⏳ מוסיף טקסט...';
    hideMessages();
    
    try {
        const formData = new FormData();
        formData.append('image_id', currentImageId);
        formData.append('text', text);
        formData.append('x', textPosition.x);
        formData.append('y', textPosition.y);
        formData.append('font_size', fontSizeInput.value);
        formData.append('color', textColorInput.value);
        formData.append('stroke_color', strokeColorInput.value);
        formData.append('stroke_width', 2);
        
        const response = await fetch('/api/add-text', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'שגיאה בהוספת טקסט');
        }
        
        const data = await response.json();
        
        // Update image
        generatedImage.src = data.image_base64;
        
        // Show download button
        downloadBtn.style.display = 'block';
        
        showSuccess('הטקסט נוסף בהצלחה! תוכל להוסיף טקסט נוסף או להוריד');
        
    } catch (error) {
        showError(error.message);
    } finally {
        addTextBtn.disabled = false;
        addTextBtn.textContent = '➕ הוסף טקסט';
    }
});

// Download image
downloadBtn.addEventListener('click', () => {
    if (currentImageId) {
        window.open(`/api/download/${currentImageId}`, '_blank');
        showSuccess('התמונה הורדה בהצלחה!');
    }
});

// Start over
startOverBtn.addEventListener('click', () => {
    location.reload();
});

// Helper functions
function showError(message) {
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
    successDiv.style.display = 'none';
    
    setTimeout(() => {
        errorDiv.style.display = 'none';
    }, 5000);
}

function showSuccess(message) {
    successDiv.textContent = message;
    successDiv.style.display = 'block';
    errorDiv.style.display = 'none';
    
    setTimeout(() => {
        successDiv.style.display = 'none';
    }, 5000);
}

function hideMessages() {
    errorDiv.style.display = 'none';
    successDiv.style.display = 'none';
}

