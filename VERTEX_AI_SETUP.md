# 🌟 Vertex AI Setup - Идеальное решение с нативным aspect_ratio

## Почему Vertex AI лучше?

| Функция | AI Studio (текущее) | Vertex AI (идеально) |
|---------|---------------------|----------------------|
| **aspect_ratio** | ❌ Crop/resize | ✅ Нативная поддержка |
| **Качество композиции** | ⭐⭐⭐⭐ Хорошо | ⭐⭐⭐⭐⭐ Идеально |
| **Модель** | gemini-2.5-flash-image | imagen-3.0-generate-001 |
| **edit_image для img2img** | ❌ НЕТ | ✅ ДА |
| **Стоимость** | ~$0.039/изображение | ~$0.02-0.04/изображение |
| **Enterprise features** | ❌ | ✅ |

---

## 🚀 Пошаговая инструкция

### Шаг 1: Google Cloud Console

1. **Создай проект:**
   - https://console.cloud.google.com/
   - **New Project** → Название: `LironHebVoice`
   - Запомни **Project ID**: `lironhebvoice-xxxxx`

2. **Включи Billing:**
   - **Billing** → Привяжи кредитную карту
   - Новые пользователи получают **$300 кредитов** (3+ месяца бесплатно)

3. **Включи API:**
   - **APIs & Services** → **Library**
   - Найди и включи:
     - ✅ **Vertex AI API**
     - ✅ **Imagen API**

---

### Шаг 2: Service Account

1. **IAM & Admin** → **Service Accounts** → **Create Service Account**

2. **Настройки:**
   - **Name:** `imagen-service`
   - **Role:** **Vertex AI User** (или **Vertex AI Administrator**)
   - ✅ **Create and continue**

3. **Создай ключ:**
   - Выбери созданный Service Account
   - **Keys** → **Add Key** → **Create new key**
   - **JSON** → скачается файл `service-account-key.json`

4. **Сохрани ключ:**
   ```bash
   # Положи в корень проекта
   mv ~/Downloads/service-account-key.json backend/vertex-credentials.json
   
   # Добавь в .gitignore (уже должно быть)
   echo "backend/vertex-credentials.json" >> .gitignore
   ```

---

### Шаг 3: Настройка проекта

#### **3.1 Обновить `.env`**

```env
# Vertex AI Configuration
VERTEX_PROJECT_ID=lironhebvoice-xxxxx  # Твой Project ID
VERTEX_LOCATION=us-central1            # Или europe-west1
GOOGLE_APPLICATION_CREDENTIALS=backend/vertex-credentials.json

# Старый AI Studio ключ (оставь для fallback)
GOOGLE_API_KEY=your-ai-studio-key
```

#### **3.2 Обновить `main.py`**

Замени импорт:

```python
# backend/main.py

# Было:
from services.imagen_service_v2 import generate_image_from_prompt, edit_image_with_prompt

# Стало (Vertex AI):
from services.imagen_service_vertex import generate_image_from_prompt, edit_image_with_prompt
```

#### **3.3 Обновить `requirements.txt`**

Уже готово:
```txt
google-genai>=1.4.0  # Поддерживает Vertex AI
```

---

### Шаг 4: Railway Configuration

1. **Переменные окружения в Railway:**
   ```
   VERTEX_PROJECT_ID=lironhebvoice-xxxxx
   VERTEX_LOCATION=us-central1
   ```

2. **Загрузить Service Account ключ:**
   
   **Вариант A (безопаснее):** Через переменную
   ```bash
   # Скопируй содержимое JSON в переменную
   GOOGLE_APPLICATION_CREDENTIALS_JSON={"type":"service_account","project_id":"..."}
   ```
   
   Затем в коде:
   ```python
   import json
   credentials_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
   if credentials_json:
       credentials = json.loads(credentials_json)
       # Use credentials
   ```

   **Вариант B (проще):** Через файл
   - Загрузи `vertex-credentials.json` в репозиторий (НЕ рекомендуется для продакшна)
   - Или используй Railway Secrets

---

### Шаг 5: Тестирование

#### **Локально:**

```bash
# Проверь что файл на месте
ls backend/vertex-credentials.json

# Запусти тест
cd backend
python -c "
from services.imagen_service_vertex import generate_image_from_prompt
import asyncio

async def test():
    result = await generate_image_from_prompt(
        'red sneakers on white background',
        '16:9'
    )
    print(f'Success! Generated {len(result)} bytes')

asyncio.run(test())
"
```

#### **На Railway:**

1. `git push` изменения
2. Railway автоматически обновится
3. Проверь логи:

```
[Vertex AI Imagen] Generating image
[Vertex AI Imagen] Aspect ratio: 9:16 (NATIVE)
[Vertex AI Imagen] ✨ Image generated! Size: (1080, 1920)
[Vertex AI Imagen] ✨ Perfect 9:16 composition - no resize needed!
```

---

## 💰 Стоимость

### Imagen 3.0 на Vertex AI:

- **Text-to-image:** ~$0.020 per image
- **Image-to-image:** ~$0.040 per image

### Сравнение с AI Studio:

| Операция | AI Studio | Vertex AI | Экономия |
|----------|-----------|-----------|----------|
| Generate | $0.039 | $0.020 | -49% ✅ |
| Edit | $0.039 | $0.040 | +2% |

**Плюс:**
- $300 бесплатных кредитов = ~10,000 изображений бесплатно
- Лучшее качество композиции

---

## 🎯 Преимущества Vertex AI

### 1. **Идеальная композиция**

**AI Studio (crop/resize):**
```
Генерирует: 1408x736
→ Обрезает: 1080x1920
Результат: Может отрезать важные части ❌
```

**Vertex AI (native):**
```
Сразу генерирует: 1080x1920
Результат: Идеальная композиция для 9:16 ✅
```

### 2. **Дополнительные параметры**

```python
config=types.GenerateImagesConfig(
    aspectRatio="9:16",
    negativePrompt="blurry, distorted",  # Что НЕ генерировать
    guidanceScale=7.0,                   # Точность (1-20)
    seed=42,                             # Воспроизводимость
    personGeneration="allow_adult"       # Контроль людей
)
```

### 3. **EditMode для продуктов**

```python
editMode=types.EditMode.EDIT_MODE_PRODUCT_IMAGE  # Идеально для e-commerce!
```

Другие режимы:
- `EDIT_MODE_BGSWAP` - замена фона
- `EDIT_MODE_INPAINT_REMOVAL` - удаление объектов
- `EDIT_MODE_STYLE` - стилизация

---

## 🔧 Troubleshooting

### Ошибка: "Permission denied"

**Решение:** Проверь роль Service Account:
```bash
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:imagen-service@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"
```

### Ошибка: "Billing not enabled"

**Решение:** Включи биллинг в Google Cloud Console

### Ошибка: "Imagen API not enabled"

**Решение:**
```bash
gcloud services enable aiplatform.googleapis.com
gcloud services enable imagen.googleapis.com
```

---

## 📊 Миграция: AI Studio → Vertex AI

### Постепенная миграция:

**1. Добавь Vertex AI как опцию:**

```python
# backend/main.py

USE_VERTEX_AI = os.getenv("USE_VERTEX_AI", "false").lower() == "true"

if USE_VERTEX_AI:
    from services.imagen_service_vertex import generate_image_from_prompt, edit_image_with_prompt
else:
    from services.imagen_service_v2 import generate_image_from_prompt, edit_image_with_prompt
```

**2. Тестируй на Railway:**
```
USE_VERTEX_AI=true  # Включи в Railway Variables
```

**3. Если всё работает → удали старый код**

---

## 🎉 Итого

### Что получишь с Vertex AI:

✅ **Идеальная композиция** - модель знает формат заранее  
✅ **Нет crop/resize** - точные размеры сразу  
✅ **Лучшее качество** - Imagen 3.0 > Gemini 2.5 Flash  
✅ **Больше контроля** - negativePrompt, guidanceScale, editMode  
✅ **Дешевле** - $0.020 vs $0.039 для text2img  
✅ **$300 кредитов** - ~10,000 бесплатных изображений  

### Минусы:

⚠️ **Сложнее настройка** - Service Account, Billing  
⚠️ **Требует Google Cloud** - не просто API ключ  

---

## 🚀 Готов начать?

1. Создай проект в Google Cloud
2. Включи Vertex AI API
3. Создай Service Account
4. Обнови код (замени импорт)
5. Profit! 🎉

**Документация Vertex AI:**
- https://cloud.google.com/vertex-ai/docs
- https://cloud.google.com/vertex-ai/generative-ai/docs/image/generate-images




