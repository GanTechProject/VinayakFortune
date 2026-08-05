FROM python:3.11-slim

WORKDIR /app

# Copy requirements from the agent-runtime package
COPY services/agent_runtime/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire services tree (needed for cross-service imports)
COPY services/ ./services/

# Set up so 'services' is importable (the monorepo root is on sys.path)
ENV PYTHONPATH=/app

EXPOSE 8000

# Healthcheck for local Docker verification
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD python -c "import httpx; httpx.get('http://localhost:8000/healthz').raise_for_status()" || exit 1

CMD ["uvicorn", "services.agent_runtime.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
