# ── Stage 1: Build admin panel ────────────────────────────────────────────────
FROM node:22-alpine AS frontend-builder

WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# ── Stage 2: Build TMA (Mini App) ─────────────────────────────────────────────
FROM node:22-alpine AS tma-builder

WORKDIR /tma
COPY tma/package*.json ./
RUN npm ci
COPY tma/ .
RUN npm run build

# ── Stage 3: Python application ───────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# System deps: curl for healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        default-mysql-client \
        fonts-liberation \
        fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY . .

# Copy built frontends (served by FastAPI)
COPY --from=frontend-builder /frontend/dist ./frontend/dist
COPY --from=tma-builder      /tma/dist      ./tma/dist

# Ensure persistent data directories exist
RUN mkdir -p \
    data/images/questions \
    data/images/answers \
    data/images/users \
    data/temp \
    data/temp/work_pdfs \
    data/uploads \
    data/excel_templates \
    flet_apps/assets/users_photos

# Default command: Telegram bot
# Override in docker-compose for API service
CMD ["python", "tgbot/start.py"]
