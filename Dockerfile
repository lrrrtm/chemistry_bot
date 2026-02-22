# ── Stage 1: Build React frontend ─────────────────────────────────────────────
FROM node:22-alpine AS frontend-builder

WORKDIR /frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ .
RUN npm run build

# ── Stage 2: Python application ───────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# System deps: curl for healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        default-mysql-client \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY . .

# Copy built React frontend (served by FastAPI on /api prefix)
COPY --from=frontend-builder /frontend/dist ./frontend/dist

# Ensure persistent data directories exist
RUN mkdir -p \
    data/questions_images \
    data/answers_images \
    data/users_photos \
    data/temp \
    data/uploads \
    data/excel_templates \
    flet_apps/assets/users_photos

# Default command: Telegram bot
# Override in docker-compose for API service
CMD ["python", "tgbot/start.py"]
