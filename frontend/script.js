let currentImageId = null;
let currentImageData = null;
let textPosition = { x: 0, y: 0 };
let currentLang = 'he'; // Default Hebrew

// Translations
const translations = {
    en: {
        errorGenerateImage: 'Error generating image',
        imageCreatedSuccess: 'Image created successfully! Now add Hebrew text',
        enterProductDescription: 'Please enter product description first',
        errorGenerateTexts: 'Error generating texts',
        suggestingTexts: '⏳ Generating...',
        suggestTextsBtn: '💡 Suggest Texts',
        positionSelected: 'Position selected',
        enterHebrewText: 'Please enter Hebrew text',
        createImageFirst: 'Please create image first',
        addingText: '⏳ Adding text...',
        addTextBtn: '➕ Add Text',
        textAddedSuccess: 'Text added successfully! You can add more text or download',
        errorAddingText: 'Error adding text',
        imageDownloaded: 'Image downloaded successfully!',
        top: 'Top',
        center: 'Center',
        bottom: 'Bottom',
        topLeft: 'Top Left',
        topRight: 'Top Right',
        bottomLeft: 'Bottom Left',
        bottomRight: 'Bottom Right'
    },
    he: {
        errorGenerateImage: 'שגיאה ביצירת התמונה',
        imageCreatedSuccess: 'התמונה נוצרה בהצלחה! עכשיו הוסף טקסט בעברית',
        enterProductDescription: 'נא להזין תיאור מוצר תחילה',
        errorGenerateTexts: 'שגיאה ביצירת טקסטים',
        suggestingTexts: '⏳ מייצר...',
        suggestTextsBtn: '💡 הצע טקסטים',
        positionSelected: 'מיקום נבחר',
        enterHebrewText: 'נא להזין טקסט בעברית',
        createImageFirst: 'נא ליצור תמונה תחילה',
        addingText: '⏳ מוסיף טקסט...',
        addTextBtn: '➕ הוסף טקסט',
        textAddedSuccess: 'הטקסט נוסף בהצלחה! תוכל להוסיף טקסט נוסף או להוריד',
        errorAddingText: 'שגיאה בהוספת טקסט',
        imageDownloaded: 'התמונה הורדה בהצלחה!',
        top: 'למעלה',
        center: 'מרכז',
        bottom: 'למטה',
        topLeft: 'שמאל למעלה',
        topRight: 'ימין למעלה',
        bottomLeft: 'שמאל למטה',
        bottomRight: 'ימין למטה'
    }
};

// Get translated text
function t(key) {
    return translations[currentLang][key] || key;
}

// Translate position names
function translatePosition(name) {
    const posMap = {
        'Top': 'top',
        'Center': 'center',
        'Bottom': 'bottom',
        'Top Left': 'topLeft',
        'Top Right': 'topRight',
        'Bottom Left': 'bottomLeft',
        'Bottom Right': 'bottomRight'
    };
    const key = posMap[name];
    return key ? t(key) : name;
}

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
            throw new Error(error.detail || t('errorGenerateImage'));
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
        
        showSuccess(t('imageCreatedSuccess'));
        
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
        showError(t('enterProductDescription'));
        return;
    }
    
    suggestTextsBtn.disabled = true;
    suggestTextsBtn.textContent = t('suggestingTexts');
    
    try {
        const formData = new FormData();
        formData.append('product_description', prompt);
        
        const response = await fetch('/api/suggest-texts', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(t('errorGenerateTexts'));
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
        suggestTextsBtn.textContent = t('suggestTextsBtn');
    }
});

// Display suggested positions
function displaySuggestedPositions(positions) {
    suggestedPositions.innerHTML = '';
    
    positions.forEach(pos => {
        const btn = document.createElement('button');
        btn.className = 'position-btn';
        const translatedName = translatePosition(pos.name);
        btn.textContent = `${translatedName} (${pos.x}, ${pos.y})`;
        btn.onclick = () => {
            textPosition = { x: pos.x, y: pos.y };
            showSuccess(`${t('positionSelected')}: ${translatedName}`);
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
        showError(t('enterHebrewText'));
        return;
    }
    
    if (!currentImageId) {
        showError(t('createImageFirst'));
        return;
    }
    
    addTextBtn.disabled = true;
    addTextBtn.textContent = t('addingText');
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
            throw new Error(error.detail || t('errorAddingText'));
        }
        
        const data = await response.json();
        
        // Update image
        generatedImage.src = data.image_base64;
        
        // Show download button
        downloadBtn.style.display = 'block';
        
        showSuccess(t('textAddedSuccess'));
        
    } catch (error) {
        showError(error.message);
    } finally {
        addTextBtn.disabled = false;
        addTextBtn.textContent = t('addTextBtn');
    }
});

// Download image
downloadBtn.addEventListener('click', () => {
    if (currentImageId) {
        window.open(`/api/download/${currentImageId}`, '_blank');
        showSuccess(t('imageDownloaded'));
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

// Language switching
function toggleLanguage() {
    currentLang = currentLang === 'he' ? 'en' : 'he';
    
    // Update HTML lang and dir
    document.documentElement.lang = currentLang;
    document.documentElement.dir = currentLang === 'he' ? 'rtl' : 'ltr';
    
    // Update all elements with translations
    document.querySelectorAll('[data-en][data-he]').forEach(el => {
        const text = currentLang === 'en' ? el.getAttribute('data-en') : el.getAttribute('data-he');
        if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
            el.placeholder = text;
        } else {
            el.textContent = text;
        }
    });
    
    // Update placeholders
    document.querySelectorAll('[data-placeholder-en][data-placeholder-he]').forEach(el => {
        const placeholder = currentLang === 'en' ? el.getAttribute('data-placeholder-en') : el.getAttribute('data-placeholder-he');
        el.placeholder = placeholder;
    });
    
    // Update language button
    document.getElementById('langText').textContent = currentLang === 'he' ? 'EN' : 'HE';
    
    // Update dynamic button texts
    if (!suggestTextsBtn.disabled) {
        suggestTextsBtn.innerHTML = `<span data-en="💡 Suggest Texts" data-he="💡 הצע טקסטים">${t('suggestTextsBtn')}</span>`;
    }
    if (!addTextBtn.disabled) {
        addTextBtn.innerHTML = `<span data-en="➕ Add Text" data-he="➕ הוסף טקסט">${t('addTextBtn')}</span>`;
    }
    
    // Re-render position buttons if they exist
    if (currentImageData && currentImageData.suggested_positions) {
        displaySuggestedPositions(currentImageData.suggested_positions);
    }
    
    // Save preference
    localStorage.setItem('language', currentLang);
}

// Load saved language preference
window.addEventListener('DOMContentLoaded', () => {
    const savedLang = localStorage.getItem('language');
    if (savedLang && savedLang !== currentLang) {
        toggleLanguage();
    }
});

