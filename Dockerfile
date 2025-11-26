FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY scraper/ ./scraper/
COPY scrape_site.py .
COPY analytics.py .
COPY schema.json .

# Make scripts executable
RUN chmod +x scrape_site.py analytics.py

# Default command
ENTRYPOINT ["python", "scrape_site.py"]

