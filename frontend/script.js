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
        
        showSuccess(t('imageCreatedSuccess'));
        
    } catch (error) {
        showError(error.message);
    } finally {
        generateBtn.disabled = false;
        generateBtnText.style.display = 'inline';
        generateLoader.style.display = 'none';
    }
});

// Edit prompt - return to step 1
editBtn.addEventListener('click', () => {
    step2.style.display = 'none';
    step1.style.display = 'block';
    hideMessages();
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

