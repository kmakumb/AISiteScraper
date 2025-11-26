# Quick Start Guide

## Installation

```bash
pip install -r requirements.txt
```

## Basic Usage

```bash
# Scrape a website
python scrape_site.py --start-url=https://quotes.toscrape.com --max-pages=50

# Analyze the results
python analytics.py output.jsonl

# Run tests
python -m unittest discover tests
```

## Example Output

The scraper produces a JSONL file where each line is a JSON document:

```json
{
  "doc_id": "abc123...",
  "url": "https://example.com/page",
  "title": "Page Title",
  "body_text": "Clean main content...",
  "metadata": {
    "fetched_at": "2024-01-15T10:30:00+00:00",
    "language": "en",
    "content_type": "article",
    "word_count": 450,
    "char_count": 2800,
    "reading_time_minutes": 2,
    "has_code": false,
    "is_substantial": true,
    "is_long_form": false
  }
}
```

## Docker

```bash
docker build -t ai-site-scraper .
docker run --rm -v $(pwd):/app/output ai-site-scraper \
  --start-url=https://quotes.toscrape.com \
  --max-pages=50 \
  --output=/app/output/output.jsonl
```

See README.md for full documentation.
