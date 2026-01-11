# syntax=docker/dockerfile:1

FROM python:3.11-slim

# Basic runtime env
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps (ffmpeg is useful for voice/music; ca-certificates for HTTPS)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    ca-certificates \
  && rm -rf /var/lib/apt/lists/*

# Install Python deps first (better layer caching)
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -U pip \
  && pip install --no-cache-dir -r /app/requirements.txt

# Copy app code
COPY . /app

# Security: run as non-root user
RUN useradd -m -u 10001 appuser && chown -R appuser:appuser /app
USER appuser

# Start command is configurable via env (Coolify)
# Examples:
#   START_CMD="python -m bromeostriker"
#   START_CMD="python -m bromeoassist"
#   START_CMD="python bot.py"
ENV START_CMD="python -m bot"

CMD ["sh", "-lc", "$START_CMD"]
