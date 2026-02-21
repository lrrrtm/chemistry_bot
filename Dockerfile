FROM python:3.11-slim

WORKDIR /app

# System deps: curl for healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY . .

# Ensure persistent data directories exist
RUN mkdir -p \
    data/questions_images \
    data/answers_images \
    data/users_photos \
    data/temp \
    data/uploads \
    data/excel_templates

# Default command: Telegram bot
# Override in docker-compose for API service
CMD ["python", "tgbot/start.py"]
