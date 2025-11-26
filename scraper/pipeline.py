"""Main pipeline orchestrator."""

import json
import logging
from typing import List, Dict, Optional
from pathlib import Path
import hashlib

from .crawler import Crawler
from .extractor import ContentExtractor
from .enricher import ContentEnricher

logger = logging.getLogger(__name__)


class ScrapingPipeline:
    """Orchestrates the complete scraping pipeline."""
    
    def __init__(
        self,
        start_url: str,
        max_pages: int = 100,
        max_depth: int = 5,
        delay: float = 1.0,
        timeout: int = 10,
        output_file: Optional[str] = None
    ):
        """
        Initialize the pipeline.
        
        Args:
            start_url: Starting URL for crawling
            max_pages: Maximum number of pages to crawl
            max_depth: Maximum depth from start URL
            delay: Delay between requests in seconds
            timeout: Request timeout in seconds
            output_file: Output file path (JSONL format)
        """
        self.start_url = start_url
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.delay = delay
        self.timeout = timeout
        self.output_file = output_file or "output.jsonl"
        
        # Initialize components
        self.crawler = Crawler(
            start_url=start_url,
            max_pages=max_pages,
            max_depth=max_depth,
            delay=delay,
            timeout=timeout
        )
        self.extractor = ContentExtractor()
        self.enricher = ContentEnricher()
        
        # Track processed URLs for idempotency
        self.processed_urls: set = set()
    
    def _generate_doc_id(self, url: str) -> str:
        """Generate a deterministic document ID from URL."""
        return hashlib.md5(url.encode()).hexdigest()
    
    def _load_existing_urls(self) -> set:
        """Load already processed URLs from output file for idempotency."""
        if not Path(self.output_file).exists():
            return set()
        
        existing_urls = set()
        try:
            with open(self.output_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            doc = json.loads(line)
                            existing_urls.add(doc.get("url", ""))
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            logger.warning(f"Could not load existing URLs: {e}")
        
        return existing_urls
    
    def _process_page(self, page_data: Dict) -> Optional[Dict]:
        """
        Process a single page: extract content and enrich.
        
        Args:
            page_data: Raw page data from crawler
        
        Returns:
            Enriched document or None if processing fails
        """
        url = page_data["url"]
        
        # Skip if already processed (idempotency)
        if url in self.processed_urls:
            logger.debug(f"Skipping already processed URL: {url}")
            return None
        
        try:
            # Extract content
            extracted = self.extractor.extract(page_data["html"], url)
            
            # Skip if no substantial content
            if not extracted["body_text"] or len(extracted["body_text"].strip()) < 50:
                logger.debug(f"Skipping page with insufficient content: {url}")
                return None
            
            # Enrich with metadata
            from datetime import datetime, timezone
            fetched_at = datetime.now(timezone.utc)
            enriched = self.enricher.enrich(
                url=url,
                title=extracted["title"],
                body_text=extracted["body_text"],
                fetched_at=fetched_at
            )
            
            # Add document ID
            enriched["doc_id"] = self._generate_doc_id(url)
            
            # Mark as processed
            self.processed_urls.add(url)
            
            return enriched
            
        except Exception as e:
            logger.error(f"Error processing page {url}: {e}")
            return None
    
    def _write_jsonl(self, documents: List[Dict], append: bool = False):
        """
        Write documents to JSONL file.
        
        Args:
            documents: List of document dictionaries
            append: Whether to append to existing file
        """
        mode = "a" if append else "w"
        
        with open(self.output_file, mode, encoding='utf-8') as f:
            for doc in documents:
                try:
                    json_line = json.dumps(doc, ensure_ascii=False)
                    f.write(json_line + "\n")
                except Exception as e:
                    logger.error(f"Error writing document {doc.get('url', 'unknown')}: {e}")
    
    def run(self) -> Dict:
        """
        Run the complete scraping pipeline.
        
        Returns:
            Summary statistics
        """
        logger.info("Starting scraping pipeline")
        
        # Load existing URLs for idempotency
        self.processed_urls = self._load_existing_urls()
        if self.processed_urls:
            logger.info(f"Found {len(self.processed_urls)} previously processed URLs")
        
        # Step 1: Crawl
        logger.info("Step 1: Crawling website...")
        crawled_pages = self.crawler.crawl()
        
        # Step 2: Extract and enrich
        logger.info("Step 2: Extracting and enriching content...")
        enriched_docs = []
        skipped = 0
        
        for page_data in crawled_pages:
            doc = self._process_page(page_data)
            if doc:
                enriched_docs.append(doc)
            else:
                skipped += 1
        
        # Step 3: Write output
        logger.info(f"Step 3: Writing {len(enriched_docs)} documents to {self.output_file}...")
        append_mode = len(self.processed_urls) > 0
        self._write_jsonl(enriched_docs, append=append_mode)
        
        # Generate summary
        total_word_count = sum(doc["word_count"] for doc in enriched_docs)
        avg_word_count = total_word_count / len(enriched_docs) if enriched_docs else 0
        
        summary = {
            "total_pages_crawled": len(crawled_pages),
            "documents_processed": len(enriched_docs),
            "documents_skipped": skipped,
            "total_word_count": total_word_count,
            "average_word_count": round(avg_word_count, 2),
            "output_file": self.output_file
        }
        
        logger.info("Pipeline complete!")
        logger.info(f"Summary: {summary}")
        
        return summary

