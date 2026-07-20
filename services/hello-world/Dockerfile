FROM python:3.11-slim

WORKDIR /app

# Install deps first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Then the app
COPY app/ ./app/
COPY pyproject.toml .

EXPOSE 8000

# Healthcheck for local Docker verification
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD python -c "import httpx; httpx.get('http://localhost:8000/healthz').raise_for_status()" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
