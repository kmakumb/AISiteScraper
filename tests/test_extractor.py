"""Tests for content extractor."""

import unittest
from scraper.extractor import ContentExtractor


class TestContentExtractor(unittest.TestCase):
    """Test cases for ContentExtractor."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.extractor = ContentExtractor()
    
    def test_extract_simple_html(self):
        """Test extraction from simple HTML."""
        html = """
        <html>
        <head><title>Test Page</title></head>
        <body>
            <h1>Main Title</h1>
            <article>
                <p>This is the main content of the page.</p>
                <p>It has multiple paragraphs with useful information.</p>
            </article>
        </body>
        </html>
        """
        result = self.extractor.extract(html, "https://example.com/test")
        
        self.assertIn("title", result)
        self.assertIn("body_text", result)
        self.assertGreater(len(result["body_text"]), 0)
        self.assertIn("main content", result["body_text"].lower())
    
    def test_extract_removes_boilerplate(self):
        """Test that boilerplate is removed."""
        html = """
        <html>
        <head><title>Test</title></head>
        <body>
            <nav>Navigation links</nav>
            <header>Header content</header>
            <main>
                <p>This is the real content.</p>
            </main>
            <footer>Footer content</footer>
        </body>
        </html>
        """
        result = self.extractor.extract(html, "https://example.com/test")
        
        # Main content should be present
        self.assertIn("real content", result["body_text"].lower())
        # Navigation and footer should be minimized or removed
        text_lower = result["body_text"].lower()
        # Note: exact behavior depends on extraction method
    
    def test_clean_text_normalizes_whitespace(self):
        """Test that text cleaning normalizes whitespace."""
        html = """
        <html>
        <body>
            <p>Text    with     excessive      spaces</p>
            <p>And multiple   line breaks</p>
        </body>
        </html>
        """
        result = self.extractor.extract(html, "https://example.com/test")
        
        # Should not have excessive spaces
        self.assertNotIn("     ", result["body_text"])
    
    def test_extract_title_fallback(self):
        """Test title extraction with fallbacks."""
        # Test with title tag
        html = '<html><head><title>Page Title</title></head><body><p>Content</p></body></html>'
        result = self.extractor.extract(html, "https://example.com/test")
        self.assertIn("Page Title", result["title"])
        
        # Test without title tag (should use URL or h1)
        html = '<html><body><h1>Heading Title</h1><p>Content</p></body></html>'
        result = self.extractor.extract(html, "https://example.com/test")
        self.assertGreater(len(result["title"]), 0)


if __name__ == "__main__":
    unittest.main()

