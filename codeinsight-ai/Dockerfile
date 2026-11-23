FROM node:22-bookworm-slim AS frontend
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
ENV CODEGUARD_STATIC_EXPORT=1 NEXT_PUBLIC_API_URL="" NEXT_TELEMETRY_DISABLED=1
RUN npm run build

FROM python:3.12-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PUBLIC_SITE_DIR=/opt/codeguard/site
WORKDIR /opt/codeguard/backend
COPY backend/requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt
COPY backend/alembic.ini ./
COPY backend/alembic ./alembic
COPY backend/app ./app
COPY --from=frontend /build/out /opt/codeguard/site
USER 65534:65534
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
