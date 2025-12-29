FROM python:3.12-slim

# Install system dependencies and fonts
RUN apt-get update && apt-get install -y \
    fonts-dejavu \
    fonts-liberation \
    fontconfig \
    libraqm0 \
    libraqm-dev \
    && fc-cache -f -v \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set Python path to include backend directory
ENV PYTHONPATH=/app/backend:$PYTHONPATH

# Expose port
EXPOSE 8000

# Run the application using Python entrypoint
CMD ["python", "entrypoint.py"]

