# -----------------------------------------------
# Stage 1: Build Dependencies
# -----------------------------------------------
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and build wheels
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# -----------------------------------------------
# Stage 2: Runtime Environment
# -----------------------------------------------
FROM python:3.11-slim AS runner

WORKDIR /app

# Create a non-root user for security (DevOps Best Practice)
RUN useradd -m -u 1000 appuser

# Copy installed packages from builder stage
COPY --from=builder /root/.local /home/appuser/.local
COPY --from=builder /app /app

# Copy application source code
COPY ./app /app/app

# Set PATH to include user-installed binaries
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

# Switch to non-root user
USER appuser

EXPOSE 8000

# Start Uvicorn server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]