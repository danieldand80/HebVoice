let currentImageId = null;
let currentImageData = null;
let currentLang = 'he'; // Default Hebrew

// Translations
const translations = {
    en: {
        errorGenerateImage: 'Error generating image',
        imageCreatedSuccess: 'Image created successfully!',
        imageDownloaded: 'Image downloaded successfully!'
    },
    he: {
        errorGenerateImage: 'שגיאה ביצירת התמונה',
        imageCreatedSuccess: 'התמונה נוצרה בהצלחה!',
        imageDownloaded: 'התמונה הורדה בהצלחה!'
    }
};

// Get translated text
function t(key) {
    return translations[currentLang][key] || key;
}

// Elements
const imageForm = document.getElementById('imageForm');
const imageInput = document.getElementById('image');
const imagePreview = document.getElementById('imagePreview');
const removeImageBtn = document.getElementById('removeImageBtn');
const generateBtn = document.getElementById('generateBtn');
const generateBtnText = document.getElementById('generateBtnText');
const generateLoader = document.getElementById('generateLoader');

const step1 = document.getElementById('step1');
const step2 = document.getElementById('step2');

const generatedImage = document.getElementById('generatedImage');

const editBtn = document.getElementById('editBtn');
const downloadBtn = document.getElementById('downloadBtn');
const startOverBtn = document.getElementById('startOverBtn');
const backToGridBtn = document.getElementById('backToGridBtn');

const errorDiv = document.getElementById('error');
const successDiv = document.getElementById('success');

// Image preview
imageInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            imagePreview.innerHTML = `<img src="${e.target.result}" alt="Preview" style="max-width: 300px; border-radius: 8px; margin-top: 10px;">`;
            removeImageBtn.style.display = 'flex';
        };
        reader.readAsDataURL(file);
    } else {
        imagePreview.innerHTML = '';
        removeImageBtn.style.display = 'none';
    }
});

// Remove image
removeImageBtn.addEventListener('click', () => {
    imageInput.value = '';
    imagePreview.innerHTML = '';
    removeImageBtn.style.display = 'none';
});

// Generate image
imageForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    // Validate: either prompt or image must be provided
    const promptValue = document.getElementById('prompt').value.trim();
    const imageFile = imageInput.files[0];
    
    if (!promptValue && !imageFile) {
        const errorMsg = currentLang === 'en' 
            ? 'Please provide either a description or upload an image'
            : 'נא להזין תיאור או להעלות תמונה';
        showError(errorMsg);
        return;
    }
    
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
        
        // Check if multiple images or single image
        if (data.images && data.images.length > 0) {
            // Multiple images - show grid
            displayImagesGrid(data.images);
        } else {
            // Legacy single image support
            currentImageId = data.image_id;
            currentImageData = data;
            
            // Show step 2
            step1.style.display = 'none';
            step2.style.display = 'block';
            
            // Display generated image
            generatedImage.src = data.image_base64;
        }
        
        showSuccess(t('imageCreatedSuccess'));
        
    } catch (error) {
        showError(error.message);
    } finally {
        generateBtn.disabled = false;
        generateBtnText.style.display = 'inline';
        generateLoader.style.display = 'none';
    }
});

// Edit prompt - return to step 1 with selected image
editBtn.addEventListener('click', async () => {
    if (!currentImageId || !currentImageData) {
        showError(currentLang === 'en' ? 'No image selected' : 'לא נבחרה תמונה');
        return;
    }
    
    // Download selected image and set it as uploaded image
    try {
        const response = await fetch(`/api/download/${currentImageId}`);
        const blob = await response.blob();
        
        // Create File from blob
        const file = new File([blob], `${currentImageId}.png`, { type: 'image/png' });
        
        // Create DataTransfer to set files
        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(file);
        imageInput.files = dataTransfer.files;
        
        // Show preview
        const reader = new FileReader();
        reader.onload = (e) => {
            imagePreview.innerHTML = `<img src="${e.target.result}" alt="Preview" style="max-width: 300px; border-radius: 8px; margin-top: 10px;">`;
            removeImageBtn.style.display = 'flex';
        };
        reader.readAsDataURL(file);
        
        // Return to step 1
        step2.style.display = 'none';
        step1.style.display = 'block';
        hideMessages();
        
        // Hide grid if it exists
        const grid = document.getElementById('imagesGrid');
        if (grid) {
            grid.style.display = 'none';
        }
        
    } catch (error) {
        console.error('Failed to load image for editing:', error);
        // Fallback: just return to step 1
        step2.style.display = 'none';
        step1.style.display = 'block';
        hideMessages();
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
    // Reset form
    imageForm.reset();
    imagePreview.innerHTML = '';
    removeImageBtn.style.display = 'none';
    
    // Hide step 2, show step 1
    step2.style.display = 'none';
    step1.style.display = 'block';
    
    // Hide grid if exists
    const grid = document.getElementById('imagesGrid');
    if (grid) {
        grid.style.display = 'none';
        grid.innerHTML = '';
    }
    
    // Show single image again
    generatedImage.style.display = 'block';
    
    // Hide back to grid button
    backToGridBtn.style.display = 'none';
    
    // Reset current image data
    currentImageId = null;
    currentImageData = null;
    
    hideMessages();
});

// Back to grid
backToGridBtn.addEventListener('click', () => {
    // Return to step 1 where grid is visible
    step2.style.display = 'none';
    step1.style.display = 'block';
    
    // Scroll to grid
    const grid = document.getElementById('imagesGrid');
    if (grid) {
        grid.scrollIntoView({ behavior: 'smooth' });
    }
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

// Display multiple images in grid
function displayImagesGrid(images) {
    // Hide step 1, show step 2
    step1.style.display = 'none';
    step2.style.display = 'block';
    
    // Check if grid exists, if not create it
    let grid = document.getElementById('imagesGrid');
    if (!grid) {
        // Create grid container before the single image
        grid = document.createElement('div');
        grid.id = 'imagesGrid';
        grid.className = 'images-grid';
        generatedImage.parentNode.insertBefore(grid, generatedImage);
        
        // Hide single image display
        generatedImage.style.display = 'none';
    }
    
    // Clear grid
    grid.innerHTML = '';
    
    // Add each image to grid
    images.forEach((img, index) => {
        const imageItem = document.createElement('div');
        imageItem.className = 'image-item';
        imageItem.dataset.imageId = img.image_id;
        imageItem.dataset.imageData = JSON.stringify(img);
        
        const imgElement = document.createElement('img');
        imgElement.src = img.image_base64;
        imgElement.alt = `Generated image ${index + 1}`;
        
        const badge = document.createElement('div');
        badge.className = 'select-badge';
        badge.textContent = currentLang === 'en' ? 'Selected' : 'נבחר';
        
        imageItem.appendChild(imgElement);
        imageItem.appendChild(badge);
        
        // Click handler to select image
        imageItem.addEventListener('click', () => selectImage(imageItem));
        
        grid.appendChild(imageItem);
    });
    
    // Auto-select first image
    if (images.length > 0) {
        const firstItem = grid.querySelector('.image-item');
        selectImage(firstItem);
    }
    
    // Show back to grid button if multiple images
    if (images.length > 1) {
        backToGridBtn.style.display = 'inline-block';
    } else {
        backToGridBtn.style.display = 'none';
    }
    
    // Show grid
    grid.style.display = 'grid';
}

// Select an image from grid
function selectImage(imageItem) {
    // Remove selected class from all items
    document.querySelectorAll('.image-item').forEach(item => {
        item.classList.remove('selected');
    });
    
    // Add selected class to clicked item
    imageItem.classList.add('selected');
    
    // Update current image data
    const imageData = JSON.parse(imageItem.dataset.imageData);
    currentImageId = imageData.image_id;
    currentImageData = imageData;
    
    // Also update the single image display (hidden but used for download/edit)
    generatedImage.src = imageData.image_base64;
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

// ============================================
// TEXT EDITOR FUNCTIONALITY
// ============================================

const textEditorModal = document.getElementById('textEditorModal');
const addTextBtn = document.getElementById('addTextBtn');
const closeTextEditor = document.getElementById('closeTextEditor');
const cancelTextBtn = document.getElementById('cancelTextBtn');
const applyTextBtn = document.getElementById('applyTextBtn');
const suggestTextBtn = document.getElementById('suggestTextBtn');

const textCanvas = document.getElementById('textCanvas');
const textDragElement = document.getElementById('textDragElement');
const textPreview = document.getElementById('textPreview');
const textInput = document.getElementById('textInput');
const fontFamily = document.getElementById('fontFamily');
const fontSize = document.getElementById('fontSize');
const fontSizeValue = document.getElementById('fontSizeValue');
const boldFont = document.getElementById('boldFont');
const textColor = document.getElementById('textColor');
const outlineColor = document.getElementById('outlineColor');
const outlineWidth = document.getElementById('outlineWidth');
const outlineWidthValue = document.getElementById('outlineWidthValue');
const textSuggestions = document.getElementById('textSuggestions');

let canvasCtx = null;
let currentImage = null;
let textPosition = { x: 100, y: 100 };
let isDragging = false;
let dragOffset = { x: 0, y: 0 };
let canvasScale = 1;

// Open text editor
addTextBtn.addEventListener('click', () => {
    if (!currentImageId || !currentImageData) {
        showError(currentLang === 'en' ? 'Please select an image first' : 'אנא בחר תמונה תחילה');
        return;
    }
    
    openTextEditor();
});

// Close text editor
closeTextEditor.addEventListener('click', closeTextEditorModal);
cancelTextBtn.addEventListener('click', closeTextEditorModal);

function openTextEditor() {
    textEditorModal.style.display = 'block';
    
    // Load image onto canvas
    loadImageToCanvas(currentImageData.image_base64);
    
    // Reset text input
    textInput.value = '';
    textPosition = { x: 100, y: 100 };
    updateTextPreview();
}

function closeTextEditorModal() {
    textEditorModal.style.display = 'none';
}

function loadImageToCanvas(imageSrc) {
    const img = new Image();
    img.onload = () => {
        currentImage = img;
        
        // Set canvas size to image size
        const maxWidth = textCanvas.parentElement.clientWidth - 40;
        canvasScale = maxWidth / img.width;
        
        textCanvas.width = img.width;
        textCanvas.height = img.height;
        textCanvas.style.maxWidth = maxWidth + 'px';
        
        canvasCtx = textCanvas.getContext('2d');
        
        // Position text in center initially
        textPosition = {
            x: img.width / 2,
            y: img.height / 4
        };
        
        // Draw everything
        redrawCanvas();
    };
    img.src = imageSrc;
}

function redrawCanvas() {
    if (!canvasCtx || !currentImage) return;
    
    // Clear canvas
    canvasCtx.clearRect(0, 0, textCanvas.width, textCanvas.height);
    
    // Draw image
    canvasCtx.drawImage(currentImage, 0, 0);
    
    // Draw text on canvas
    drawTextOnCanvas();
}

function drawTextOnCanvas() {
    if (!canvasCtx) return;
    
    const text = textInput.value || '';
    if (!text) return;
    
    const size = parseInt(fontSize.value);
    const bold = boldFont.checked;
    const font = fontFamily.value;
    const color = textColor.value;
    const oColor = outlineColor.value;
    const oWidth = parseInt(outlineWidth.value);
    const align = document.querySelector('input[name="textAlign"]:checked')?.value || 'right';
    
    // Set font
    canvasCtx.font = `${bold ? 'bold' : 'normal'} ${size}px ${font}`;
    canvasCtx.textBaseline = 'top';
    
    // Calculate text position based on alignment RELATIVE TO IMAGE
    const metrics = canvasCtx.measureText(text);
    const textWidth = metrics.width;
    
    let drawX;
    if (align === 'left') {
        // Left align: X position is from left edge of canvas
        drawX = textPosition.x;
    } else if (align === 'center') {
        // Center align: center the text on canvas, Y is free position
        drawX = (textCanvas.width - textWidth) / 2;
    } else if (align === 'right') {
        // Right align: X position is from right edge of canvas
        drawX = textCanvas.width - textPosition.x - textWidth;
    }
    
    // Draw outline (stroke)
    if (oWidth > 0) {
        canvasCtx.strokeStyle = oColor;
        canvasCtx.lineWidth = oWidth * 2;
        canvasCtx.lineJoin = 'round';
        canvasCtx.strokeText(text, drawX, textPosition.y);
    }
    
    // Draw text
    canvasCtx.fillStyle = color;
    canvasCtx.fillText(text, drawX, textPosition.y);
}

// Update text preview when inputs change
textInput.addEventListener('input', redrawCanvas);
fontFamily.addEventListener('change', redrawCanvas);
fontSize.addEventListener('input', (e) => {
    fontSizeValue.textContent = e.target.value + 'px';
    redrawCanvas();
});
boldFont.addEventListener('change', redrawCanvas);
textColor.addEventListener('input', redrawCanvas);
outlineColor.addEventListener('input', redrawCanvas);
outlineWidth.addEventListener('input', (e) => {
    outlineWidthValue.textContent = e.target.value + 'px';
    redrawCanvas();
});

// Update text alignment
document.querySelectorAll('input[name="textAlign"]').forEach(radio => {
    radio.addEventListener('change', redrawCanvas);
});

// Drag and drop text positioning on canvas
textCanvas.addEventListener('mousedown', startDrag);
textCanvas.addEventListener('touchstart', startDrag);

function startDrag(e) {
    isDragging = true;
    
    const canvasRect = textCanvas.getBoundingClientRect();
    const scale = canvasRect.width / textCanvas.width;
    
    const clientX = e.type === 'touchstart' ? e.touches[0].clientX : e.clientX;
    const clientY = e.type === 'touchstart' ? e.touches[0].clientY : e.clientY;
    
    // Get position relative to canvas
    let x = (clientX - canvasRect.left) / scale;
    let y = (clientY - canvasRect.top) / scale;
    
    // Constrain to canvas bounds
    x = Math.max(0, Math.min(x, textCanvas.width));
    y = Math.max(0, Math.min(y, textCanvas.height));
    
    textPosition = { x, y };
    redrawCanvas();
    
    e.preventDefault();
}

document.addEventListener('mousemove', drag);
document.addEventListener('touchmove', drag);

function drag(e) {
    if (!isDragging) return;
    
    const canvasRect = textCanvas.getBoundingClientRect();
    const scale = canvasRect.width / textCanvas.width;
    
    const clientX = e.type === 'touchmove' ? e.touches[0].clientX : e.clientX;
    const clientY = e.type === 'touchmove' ? e.touches[0].clientY : e.clientY;
    
    let x = (clientX - canvasRect.left) / scale;
    let y = (clientY - canvasRect.top) / scale;
    
    // Constrain to canvas bounds
    x = Math.max(0, Math.min(x, textCanvas.width));
    y = Math.max(0, Math.min(y, textCanvas.height));
    
    textPosition = { x, y };
    redrawCanvas();
    
    e.preventDefault();
}

document.addEventListener('mouseup', stopDrag);
document.addEventListener('touchend', stopDrag);

function stopDrag() {
    isDragging = false;
}

// Suggest text using AI (Gemini vision analysis)
suggestTextBtn.addEventListener('click', async () => {
    if (!currentImageId) {
        showError(currentLang === 'en' ? 'No image selected' : 'לא נבחרה תמונה');
        return;
    }
    
    const prompt = document.getElementById('prompt').value || '';
    
    suggestTextBtn.disabled = true;
    suggestTextBtn.textContent = currentLang === 'en' ? 'Analyzing image...' : 'מנתח תמונה...';
    
    try {
        const formData = new FormData();
        formData.append('image_id', currentImageId);
        formData.append('product_description', prompt);
        formData.append('language', currentLang); // Pass current UI language
        
        const response = await fetch('/api/suggest-texts', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('Failed to generate suggestions');
        }
        
        const data = await response.json();
        
        // Display suggestions
        textSuggestions.innerHTML = '';
        if (data.texts && data.texts.length > 0) {
            data.texts.forEach(text => {
                const suggestionEl = document.createElement('span');
                suggestionEl.className = 'text-suggestion-item';
                suggestionEl.textContent = text;
                suggestionEl.addEventListener('click', () => {
                    textInput.value = text;
                    redrawCanvas(); // Redraw canvas with new text
                    textSuggestions.style.display = 'none';
                });
                textSuggestions.appendChild(suggestionEl);
            });
            textSuggestions.style.display = 'flex';
        } else {
            showError(currentLang === 'en' ? 'No suggestions available' : 'אין הצעות זמינות');
        }
        
    } catch (error) {
        showError(currentLang === 'en' ? 'Failed to generate text suggestions' : 'נכשל ביצירת הצעות טקסט');
    } finally {
        suggestTextBtn.disabled = false;
        const btnText = currentLang === 'en' ? '💡 AI Analyze Image' : '💡 ניתוח AI של התמונה';
        suggestTextBtn.innerHTML = `<span data-en="💡 AI Analyze Image" data-he="💡 ניתוח AI של התמונה">${btnText}</span>`;
    }
});

// Apply text to image
applyTextBtn.addEventListener('click', async () => {
    const text = textInput.value.trim();
    
    if (!text) {
        showError(currentLang === 'en' ? 'Please enter some text' : 'אנא הכנס טקסט');
        return;
    }
    
    if (!currentImageId) {
        showError(currentLang === 'en' ? 'No image selected' : 'לא נבחרה תמונה');
        return;
    }
    
    applyTextBtn.disabled = true;
    applyTextBtn.textContent = currentLang === 'en' ? 'Applying...' : 'מחיל...';
    
    try {
        // Get text alignment
        const align = document.querySelector('input[name="textAlign"]:checked')?.value || 'right';
        const font = fontFamily.value || 'Arial';
        
        // Convert hex colors to RGBA
        const fontRGBA = hexToRGBA(textColor.value, 255);
        const strokeRGBA = hexToRGBA(outlineColor.value, 255);
        
        const formData = new FormData();
        formData.append('image_id', currentImageId);
        formData.append('text', text);
        formData.append('x', Math.round(textPosition.x));
        formData.append('y', Math.round(textPosition.y));
        formData.append('font_size', fontSize.value);
        formData.append('font_color', fontRGBA);
        formData.append('stroke_color', strokeRGBA);
        formData.append('stroke_width', outlineWidth.value);
        formData.append('bold', boldFont.checked);
        formData.append('align', align);
        
        const response = await fetch('/api/add-text', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to add text');
        }
        
        const data = await response.json();
        
        console.log('[Apply Text] Success:', data);
        
        // Update current image with text version
        currentImageId = data.image_id;
        currentImageData = data;
        
        // Update main result image
        generatedImage.src = data.image_base64;
        generatedImage.style.display = 'block';
        
        // Hide grid and show single image with text
        const grid = document.getElementById('imagesGrid');
        if (grid) {
            grid.style.display = 'none';
        }
        
        // Update the selected image in grid data (but keep it hidden)
        const selectedImageItem = document.querySelector('.image-item.selected');
        if (selectedImageItem) {
            const img = selectedImageItem.querySelector('img');
            if (img) {
                img.src = data.image_base64;
                // Update data attribute
                const imageData = JSON.parse(selectedImageItem.dataset.imageData);
                imageData.image_base64 = data.image_base64;
                imageData.image_id = data.image_id;
                selectedImageItem.dataset.imageData = JSON.stringify(imageData);
            }
        }
        
        // Close modal
        closeTextEditorModal();
        
        // Ensure step 2 is visible with result
        step1.style.display = 'none';
        step2.style.display = 'block';
        
        // Scroll to result
        generatedImage.scrollIntoView({ behavior: 'smooth', block: 'center' });
        
        showSuccess(currentLang === 'en' ? 'Text added successfully!' : 'הטקסט נוסף בהצלחה!');
        
    } catch (error) {
        showError(error.message);
    } finally {
        applyTextBtn.disabled = false;
        applyTextBtn.innerHTML = currentLang === 'en' ? '✅ Apply Text' : '✅ החל טקסט';
    }
});

// Helper function to convert hex to RGBA string
function hexToRGBA(hex, alpha) {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return `${r},${g},${b},${alpha}`;
}

// Close modal when clicking outside
window.addEventListener('click', (e) => {
    if (e.target === textEditorModal) {
        closeTextEditorModal();
    }
});

