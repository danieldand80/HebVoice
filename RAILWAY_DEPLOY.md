# Railway Deployment Guide

## Шаги для деплоя на Railway:

### 1. Создай проект на Railway

1. Зайди: https://railway.app
2. **New Project** → **Deploy from GitHub repo**
3. Выбери: `danieldand80/HebVoice`
4. Railway автоматически определит Python

### 2. Настрой Environment Variables

В Railway dashboard → **Variables** → добавь:

```bash
GOOGLE_PROJECT_ID=твой-project-id
GOOGLE_LOCATION=us-central1
PORT=8000
```

**ВАЖНО - Credentials:**

```bash
GOOGLE_APPLICATION_CREDENTIALS_JSON={"type":"service_account","project_id":"...","private_key_id":"...","private_key":"...","client_email":"...","client_id":"...","auth_uri":"...","token_uri":"...","auth_provider_x509_cert_url":"...","client_x509_cert_url":"..."}
```

Скопируй **ВСЁ содержимое** твоего `google-credentials.json` файла (без переносов строк) в эту переменную.

### 3. (Опционально) GPT-4 для генерации текстов

```bash
OPENAI_API_KEY=sk-...
```

### 4. Deploy

Railway автоматически задеплоит после:
- Push в GitHub
- Изменения Environment Variables

### 5. Получи URL

После деплоя Railway выдаст URL типа:
```
https://hebvoice-production.up.railway.app
```

---

## Как получить GOOGLE_APPLICATION_CREDENTIALS_JSON:

### На Windows:
```powershell
Get-Content google-credentials.json -Raw | Set-Clipboard
```

### На Mac/Linux:
```bash
cat google-credentials.json | pbcopy
```

Потом вставь в Railway Variables.

---

## Альтернатива: Render.com

Если Railway не работает, можно использовать Render:

1. https://render.com → **New Web Service**
2. Connect GitHub repo
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `cd backend && python main.py`
5. Добавь те же Environment Variables

---

## Проверка после деплоя:

```bash
curl https://твой-url.railway.app/health
```

Должен вернуть: `{"status":"ok"}`

---

## Troubleshooting:

### Ошибка "GOOGLE_PROJECT_ID not set"
- Проверь что Variables сохранились в Railway
- Перезапусти деплой

### Ошибка с credentials
- Убедись что JSON скопирован полностью (без переносов строк)
- Должен начинаться с `{` и заканчиваться `}`

### Ошибка "No module named 'vertexai'"
- Railway должен автоматом установить из requirements.txt
- Проверь что requirements.txt в корне проекта

