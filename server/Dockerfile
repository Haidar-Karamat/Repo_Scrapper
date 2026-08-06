# -----------------------------------------------
# Stage 1: Build Dependencies
# -----------------------------------------------
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements (context: ./server)
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# -----------------------------------------------
# Stage 2: Runtime Environment
# -----------------------------------------------
FROM python:3.11-slim AS runner

WORKDIR /app

# Non-root user for security
RUN useradd -m -u 1000 appuser

# Copy installed dependencies from builder stage
COPY --from=builder /root/.local /home/appuser/.local

# Copy FastAPI application code to /app/app
COPY --chown=appuser:appuser ./app ./app

ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

USER appuser

EXPOSE 8000

# Start Uvicorn from /app context targeting app.main:app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]