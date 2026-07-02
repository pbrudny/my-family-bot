# --- Frontend build ---
FROM node:20-alpine AS frontend
WORKDIR /app
COPY frontend/package.json .
RUN npm install
COPY frontend/ .
RUN npx vite build

# --- Backend ---
FROM python:3.12-slim
WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml .
RUN uv pip install --system --no-cache .

COPY backend/app/ ./app/
COPY --from=frontend /app/dist ./static/

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
