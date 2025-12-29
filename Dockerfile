FROM python:3.12-slim

# Install system dependencies and fonts
RUN apt-get update && apt-get install -y \
    fonts-dejavu \
    fonts-liberation \
    fontconfig \
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

# Make start script executable
RUN chmod +x start.sh

# Expose port
EXPOSE 8000

# Run the application
CMD ["./start.sh"]

