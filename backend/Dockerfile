FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for PostgreSQL and PDF processing
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create uploads directory
RUN mkdir -p /app/uploads

# Expose port (Railway uses PORT env variable)
EXPOSE 8000

# Set default port
ENV PORT=8000

# Run the application with shell to expand $PORT
CMD uvicorn src.main:app --host 0.0.0.0 --port $PORT
