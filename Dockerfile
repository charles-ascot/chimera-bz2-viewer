# Use official Python runtime as a parent image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy app files
COPY app.py .
COPY static/ static/
COPY templates/ templates/
COPY credentials.json . 2>/dev/null || true

# Expose port
EXPOSE 8080

# Set environment
ENV PORT=8080

# Run with Gunicorn
CMD exec gunicorn --bind :$PORT --workers 4 --threads 2 --worker-class gthread --timeout 3600 app:app
