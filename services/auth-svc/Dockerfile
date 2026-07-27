FROM python:3.11-slim

WORKDIR /app

# Install deps first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Then the app
COPY app/ ./app/
COPY pyproject.toml .

EXPOSE 8000

# Redis connection. Set REDIS_URL at deploy time (issue #4 AC-1.4 owns
# the production wiring). Example: redis://redis:6379/0. The Python
# wrapper falls back to REDIS_URL=redis://localhost:6379/0 if unset,
# so the image boots cleanly in dev. We intentionally do NOT install
# redis-tools: the runtime only needs the redis-py client (already in
# requirements.txt); the server is external.
#
# ENV REDIS_URL=redis://redis:6379/0

# Healthcheck for local Docker verification
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD python -c "import httpx; httpx.get('http://localhost:8000/healthz').raise_for_status()" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
