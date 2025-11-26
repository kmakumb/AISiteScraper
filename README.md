# AISiteScraper

A production-minded web scraping pipeline that crawls a public site, extracts and cleans main content, enriches it with AI-ready metadata, and outputs structured JSONL documents for use in RAG, search, and fine-tuning workflows.

## Site Chosen

This scraper is designed to crawl a single public website. For this project, I chose:

**quotes.toscrape.com** - A simple quotes website designed for scraping practice.

### Why This Site?

I selected quotes.toscrape.com for several reasons:

- **Explicitly allows scraping**: The site is specifically designed for web scraping practice and explicitly permits automated access, making it an ethical choice for this project.

- **Good test coverage**: The site contains a variety of page types (homepage, author pages, tag pages, pagination) that allow testing different aspects of the crawler:

  - Internal link following
  - Pagination handling
  - Content extraction from different page structures
  - URL normalization (handles trailing slashes, index.html variations)

- **Reasonable size**: The site is large enough to demonstrate crawling depth and breadth limits, but small enough to complete test runs quickly.

- **Clean structure**: The HTML structure is relatively clean, making it a good test case for content extraction algorithms while still presenting realistic challenges (navigation, footers, etc.).

- **Educational value**: As a sandbox site, it's perfect for demonstrating production-minded scraping practices without impacting real websites.

### Ethical Considerations

The scraper respects `robots.txt` and includes sensible throttling (1 second delay between requests by default) to be a good web citizen. When scraping other sites, always:

- Check and respect robots.txt
- Use appropriate delays between requests
- Follow the site's terms of service
- Only scrape publicly accessible content

## Quick Start

### Installation

1. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

   **Optional:** Install as a package to use `scrape_site` command from anywhere:

   ```bash
   pip install -e .
   ```

### Basic Usage

**From the project root directory**, run:

```bash
python scrape_site.py --start-url=https://quotes.toscrape.com --max-pages=50
```

**Or if installed as a package**, you can run from anywhere:

```bash
scrape_site --start-url=https://quotes.toscrape.com --max-pages=50
```

### Full Command Reference

**Run from project root directory:**

```bash
python scrape_site.py --start-url=https://quotes.toscrape.com --max-pages=50 --max-depth=3
```

**Or if installed as package:**

```bash
scrape_site --start-url=https://quotes.toscrape.com --max-pages=50 --max-depth=3
```

**Required Arguments:**

- `--start-url`: Starting URL for crawling (must start with http:// or https://)

**Optional Arguments:**

- `--max-pages`: Maximum number of pages to crawl (default: 100)
- `--max-depth`: Maximum depth from start URL (default: 5)
- `--delay`: Delay between requests in seconds (default: 1.0)
- `--timeout`: Request timeout in seconds (default: 10)
- `--output`: Output file path in JSONL format (default: output.jsonl)
- `--verbose`: Enable verbose logging for debugging

**Examples:**

```bash
# Scrape quotes site with default settings
python scrape_site.py --start-url=https://quotes.toscrape.com

# Scrape with custom limits and output file
python scrape_site.py --start-url=https://quotes.toscrape.com --max-pages=200 --output=quotes.jsonl

# Scrape with higher depth and slower rate
python scrape_site.py --start-url=https://quotes.toscrape.com --max-depth=3 --delay=2.0

# Verbose mode for debugging
python scrape_site.py --start-url=https://quotes.toscrape.com --verbose
```

## Data Schema

Each document in the output JSONL file follows this schema:

```json
{
  "url": "https://example.com/page",
  "title": "Page Title",
  "body_text": "Main content text, cleaned and normalized...",
  "fetched_at": "2024-01-15T10:30:00+00:00",
  "language": "en",
  "content_type": "article",
  "word_count": 450,
  "char_count": 2800,
  "reading_time_minutes": 2,
  "has_code": false,
  "is_substantial": true,
  "is_long_form": false,
  "doc_id": "md5_hash_of_url"
}
```

### Field Descriptions

- **`url`**: Source URL of the document
- **`title`**: Document title (extracted from HTML `<title>`, Open Graph, or `<h1>`)
- **`body_text`**: Main content text, cleaned of HTML, boilerplate, and normalized whitespace
- **`fetched_at`**: ISO 8601 timestamp when document was fetched
- **`language`**: Detected language code (`en`, `es`, `fr`, `de` - simple heuristic)
- **`content_type`**: Type of page (`article`, `doc_page`, `product_page`, `homepage`, `page`)
- **`word_count`**: Number of words in body_text
- **`char_count`**: Number of characters in body_text
- **`reading_time_minutes`**: Estimated reading time (assumes 200 words/minute)
- **`has_code`**: Boolean indicating if content contains code snippets
- **`is_substantial`**: Boolean indicating if document has ≥100 words
- **`is_long_form`**: Boolean indicating if document has ≥1000 words
- **`doc_id`**: Unique document identifier (MD5 hash of URL) for deduplication

A complete JSON Schema is provided in `schema.json`.

## Design Decisions

### Crawling Strategy

**Which Pages to Keep:**

- **Same domain only**: Only follows links within the starting domain
- **Depth limiting**: Respects `--max-depth` to prevent unbounded crawling
- **Content filtering**: Automatically skips obvious non-content pages:
  - Login/signup pages
  - Search result pages
  - API endpoints
  - Static assets (images, PDFs, etc.)
  - External links
- **Duplicate prevention**: Maintains a visited URLs set to avoid re-crawling
- **robots.txt compliance**: Checks and respects robots.txt rules when available

### Content Extraction

**Main Content Extraction:**

1. **Primary method**: Uses `readability-lxml` library, which applies Mozilla's Readability algorithm to extract the main content article
2. **Fallback method**: If Readability fails or produces insufficient content, uses heuristics:
   - Looks for semantic HTML5 elements (`<main>`, `<article>`)
   - Tries common content container classes (`.content`, `.main-content`, etc.)
   - Falls back to `<body>` after removing boilerplate

**Text Cleaning:**

- Removes `<script>`, `<style>`, and `<noscript>` tags
- Removes HTML comments
- Strips navigation, headers, footers, and sidebar elements
- Normalizes whitespace (collapses multiple spaces/newlines)
- Preserves paragraph structure where possible

**Title Extraction:**

- Tries `<title>` tag first
- Falls back to Open Graph `og:title` meta tag
- Then tries `<h1>` tag
- Finally uses URL path as fallback

### AI Workflow Support

**Metadata Fields Rationale:**

- **`word_count`/`char_count`**: Essential for filtering by length, ranking by quality
- **`language`**: Critical for multilingual RAG systems, allows language-specific indexing
- **`content_type`**: Enables content-based filtering (e.g., only articles, only docs)
- **`reading_time_minutes`**: Useful for user-facing features and content prioritization
- **`has_code`**: Important signal for code-focused search or documentation systems
- **`is_substantial`/`is_long_form`**: Quick quality filters for training data selection
- **`fetched_at`**: Enables time-based filtering and freshness checks

**Why This Schema:**

- **Search/RAG ready**: Clean `body_text` can be directly chunked and embedded
- **Filterable**: Rich metadata enables easy filtering and ranking
- **Traceable**: `doc_id` and `url` enable deduplication and source tracking
- **Extensible**: Schema can be extended without breaking existing consumers

## Architecture

The pipeline consists of four main components:

1. **`Crawler`** (`scraper/crawler.py`): Discovers and fetches pages

   - Handles link following, deduplication, throttling
   - Respects robots.txt and domain boundaries
   - Implements retry logic for resilience

2. **`ContentExtractor`** (`scraper/extractor.py`): Extracts and cleans content

   - Uses Readability algorithm with heuristic fallback
   - Removes boilerplate and normalizes text

3. **`ContentEnricher`** (`scraper/enricher.py`): Adds AI-ready metadata

   - Language detection
   - Content type classification
   - Quality signals and metrics

4. **`ScrapingPipeline`** (`scraper/pipeline.py`): Orchestrates the workflow
   - Coordinates crawling, extraction, and enrichment
   - Handles JSONL output
   - Provides idempotency (skips already-processed URLs)

## Quality & Robustness

### Idempotency

- The pipeline checks existing output files before processing
- URLs already in the output are skipped
- Running the script twice won't create duplicates (unless `--output` points to a different file)

### Error Handling

- **Network errors**: Retries with exponential backoff (via `urllib3`)
- **HTTP errors**: Logs and skips problematic pages (4xx/5xx)
- **Timeouts**: Configurable timeout with graceful handling
- **Parsing errors**: Individual page failures don't crash the pipeline

### Maintainability

- **Modular design**: Clear separation between crawling, extraction, and enrichment
- **Logging**: Comprehensive logging at INFO level (DEBUG with `--verbose`)
- **Type hints**: Functions include type hints for clarity
- **Documentation**: Inline comments for complex logic

## Analytics

Use the included analytics script to analyze your scraped collection:

```bash
python analytics.py output.jsonl
```

This will print statistics including:

- Total documents and word counts
- Language and content type distributions
- Quality signal summaries
- Reading time estimates
- Top documents by word count

## Running Tests

Unit tests are provided for core extraction and enrichment logic:

```bash
python -m pytest tests/ -v
```

Or using unittest:

```bash
python -m unittest discover tests
```

## Docker

A Dockerfile is provided for containerized execution:

```bash
# Build image
docker build -t ai-site-scraper .

# Run scraper
docker run --rm -v $(pwd):/app/output ai-site-scraper \
  --start-url=https://quotes.toscrape.com \
  --max-pages=50 \
  --output=/app/output/output.jsonl
```

## Future Work

Ideas for improving this pipeline in a production system:

### Scalability

- **Distributed crawling**: Use Celery or similar for parallel crawling across multiple workers
- **Database storage**: Store documents in a database (PostgreSQL, MongoDB) instead of JSONL files
- **Incremental updates**: Track last-modified dates and only re-crawl changed pages

### Quality Improvements

- **Better language detection**: Use `langdetect` or `spacy` for more accurate detection
- **Content quality scoring**: ML-based quality scores using models like BERT
- **Duplicate detection**: Semantic similarity checks beyond URL matching
- **Broken link detection**: Validate internal links during crawling

### Features

- **Scheduled crawling**: Integrate with cron or task schedulers
- **Monitoring & alerting**: Metrics collection (Prometheus) and alerting (PagerDuty)
- **Configurable filters**: URL pattern matching, content type whitelisting
- **Multi-source aggregation**: Combine multiple sources into a single collection
- **Change detection**: Track document changes over time

### Production Hardening

- **Rate limiting**: More sophisticated rate limiting based on domain
- **Proxy rotation**: Support for proxy pools to avoid IP blocking
- **User agent rotation**: Rotate user agents to appear more human-like
- **CAPTCHA handling**: Integration with CAPTCHA solving services if needed
- **Resume capability**: Save crawl state to resume interrupted crawls

### AI Workflow Integration

- **Direct embedding**: Option to generate embeddings during scraping
- **Chunking**: Automatic text chunking for RAG workflows
- **Metadata extraction**: Extract structured metadata (author, publish date) from meta tags
- **Image extraction**: Optional extraction of images with alt text

## Dependencies

- `requests`: HTTP client with retry logic
- `beautifulsoup4`: HTML parsing
- `lxml`: Fast XML/HTML parser
- `readability-lxml`: Main content extraction using Readability algorithm
- `urllib3`: HTTP utilities and retry strategies

See `requirements.txt` for versions.

## License

This project is provided as-is for the take-home assignment.

## Support

For issues or questions, please review the code comments and error messages. The `--verbose` flag provides detailed debugging information.
