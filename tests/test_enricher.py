"""Tests for content enricher."""

import unittest
from datetime import datetime, timezone
from scraper.enricher import ContentEnricher


class TestContentEnricher(unittest.TestCase):
    """Test cases for ContentEnricher."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.enricher = ContentEnricher()
    
    def test_enrich_basic(self):
        """Test basic enrichment."""
        url = "https://example.com/article"
        title = "Test Article"
        body_text = "This is a test article with some content. " * 50  # ~400 words
        
        result = self.enricher.enrich(url, title, body_text)
        
        self.assertEqual(result["url"], url)
        self.assertEqual(result["title"], title)
        self.assertEqual(result["body_text"], body_text)
        
        # Check that all fields are at top level (no nested metadata)
        self.assertIn("word_count", result)
        self.assertIn("char_count", result)
        self.assertIn("language", result)
        self.assertIn("content_type", result)
        self.assertIn("fetched_at", result)
        self.assertGreater(result["word_count"], 0)
        self.assertGreater(result["char_count"], 0)
    
    def test_detect_content_type(self):
        """Test content type detection."""
        # Documentation page
        url = "https://example.com/docs/getting-started"
        result = self.enricher._detect_content_type(url, "Guide", "Content")
        self.assertEqual(result, "doc_page")
        
        # Blog post
        url = "https://example.com/blog/post-title"
        result = self.enricher._detect_content_type(url, "Blog Post", "Content")
        self.assertEqual(result, "article")
        
        # Product page
        url = "https://example.com/product/item-name"
        result = self.enricher._detect_content_type(url, "Product", "Content")
        self.assertEqual(result, "product_page")
    
    def test_has_code_detection(self):
        """Test code detection."""
        # Text with code
        text_with_code = "Here is some code: function test() { return true; }"
        self.assertTrue(self.enricher._has_code(text_with_code))
        
        # Text without code
        text_without_code = "This is just plain text with no code snippets."
        self.assertFalse(self.enricher._has_code(text_without_code))
    
    def test_reading_time_estimation(self):
        """Test reading time estimation."""
        word_count = 200
        reading_time = self.enricher._estimate_reading_time(word_count)
        self.assertEqual(reading_time, 1)  # 200 words = 1 minute
        
        word_count = 1000
        reading_time = self.enricher._estimate_reading_time(word_count)
        self.assertEqual(reading_time, 5)  # 1000 words = 5 minutes
    
    def test_substantial_content_flag(self):
        """Test substantial content flag."""
        # Long content
        long_text = "Word " * 150  # 150 words
        result = self.enricher.enrich("https://example.com", "Title", long_text)
        self.assertTrue(result["is_substantial"])
        
        # Short content
        short_text = "Word " * 10  # 10 words
        result = self.enricher.enrich("https://example.com", "Title", short_text)
        self.assertFalse(result["is_substantial"])


if __name__ == "__main__":
    unittest.main()

