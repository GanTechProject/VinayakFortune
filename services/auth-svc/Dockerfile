FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

EXPOSE 8000

# NOTE: the local subset has no HTTP server yet. This Dockerfile is the
# placeholder for the FastAPI service that the implementer adds in the
# follow-up design (see DESIGN.md §2 — "Out of scope").
CMD ["python", "-c", "from app.session_manager import InMemorySessionManager; print('auth-svc local subset: import OK')"]
