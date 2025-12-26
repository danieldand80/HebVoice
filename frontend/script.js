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
    
    // Reset current image data
    currentImageId = null;
    currentImageData = null;
    
    hideMessages();
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

