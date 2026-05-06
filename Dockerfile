FROM python:3.12-slim

WORKDIR /app

# Install system dependencies (fonts + build deps for ReportLab C extensions)
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-dejavu libfreetype6-dev gcc && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py models.py pdf_generator.py ./
COPY templates/ templates/
COPY static/ static/

# Create directories for persistent data
RUN mkdir -p data uploads/documents

EXPOSE 5000

CMD ["python", "app.py"]
