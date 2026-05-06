FROM python:3.7-slim

WORKDIR /app

# Install system dependencies (fonts required by ReportLab PDF generator)
RUN apt-get update && apt-get install -y --no-install-recommends fonts-dejavu && rm -rf /var/lib/apt/lists/*

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
