#!/usr/bin/env python3
"""CLI entry point for the AISiteScraper."""

import argparse
import logging
import sys
from scraper.pipeline import ScrapingPipeline

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Scrape a website and produce AI-ready JSONL documents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  scrape_site --start-url=https://quotes.toscrape.com --max-pages=50
  scrape_site --start-url=https://books.toscrape.com --max-pages=100 --output=books.jsonl
  scrape_site --start-url=https://docs.example.com --max-pages=200 --max-depth=3 --delay=2.0
        """
    )
    
    parser.add_argument(
        "--start-url",
        required=True,
        help="Starting URL for crawling (required)"
    )
    
    parser.add_argument(
        "--max-pages",
        type=int,
        default=100,
        help="Maximum number of pages to crawl (default: 100)"
    )
    
    parser.add_argument(
        "--max-depth",
        type=int,
        default=5,
        help="Maximum depth from start URL (default: 5)"
    )
    
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Delay between requests in seconds (default: 1.0)"
    )
    
    parser.add_argument(
        "--timeout",
        type=int,
        default=10,
        help="Request timeout in seconds (default: 10)"
    )
    
    parser.add_argument(
        "--output",
        default="output.jsonl",
        help="Output file path (JSONL format) (default: output.jsonl)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Adjust logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate URL
    if not args.start_url.startswith(("http://", "https://")):
        logger.error("start-url must start with http:// or https://")
        sys.exit(1)
    
    try:
        # Create and run pipeline
        pipeline = ScrapingPipeline(
            start_url=args.start_url,
            max_pages=args.max_pages,
            max_depth=args.max_depth,
            delay=args.delay,
            timeout=args.timeout,
            output_file=args.output
        )
        
        summary = pipeline.run()
        
        # Print summary
        print("\n" + "="*60)
        print("SCRAPING COMPLETE")
        print("="*60)
        print(f"Pages crawled: {summary['total_pages_crawled']}")
        print(f"Documents processed: {summary['documents_processed']}")
        print(f"Documents skipped: {summary['documents_skipped']}")
        print(f"Total word count: {summary['total_word_count']:,}")
        print(f"Average word count: {summary['average_word_count']:,.0f}")
        print(f"Output file: {summary['output_file']}")
        print("="*60)
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=args.verbose)
        sys.exit(1)


if __name__ == "__main__":
    main()

