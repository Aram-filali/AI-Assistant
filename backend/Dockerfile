# === Build stage ===
FROM python:3.11-slim AS builder

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# === Runtime stage ===
FROM python:3.11-slim

WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY . .

# Set PATH
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

# Run entrypoint which initializes database and starts the app
# Initialize DB then start the app - all in one command
CMD sh -c 'python -c "from app.core.init_db import init_database; init_database()" && exec uvicorn app.main:app --host 0.0.0.0 --port 8000'
