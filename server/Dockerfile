FROM python:3.11-slim

WORKDIR /app

# Copy requirements file relative to root context
COPY server/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy all server code into /app inside the container
COPY server/ .

EXPOSE 8000

# Server run command (main.py ya app/main.py ke according adjust karein)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]