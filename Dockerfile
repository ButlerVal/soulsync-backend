# 1. Use an official Python runtime as a parent image
FROM python:3.12-slim

# 2. Set the working directory in the container
WORKDIR /code

# 3. Set environment variables to prevent Python from writing pyc files
# and to ensure output is sent straight to logs
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 4. Install system dependencies (psycopg2-binary needs some)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 5. Install Python dependencies
# Copy only requirements.txt first to leverage Docker cache
COPY requirements.txt /code/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 6. Copy the rest of the application code into the container
COPY . /code/

# 7. Define the command to run the application
# We use Gunicorn with Uvicorn workers, binding to 0.0.0.0
# Hugging Face Spaces provides a $PORT env var (defaulting to 7860)
# We will use 1 worker to be safe on free/low-memory tiers.
CMD ["gunicorn", "-w", "1", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:7860", "app.main:app"]
