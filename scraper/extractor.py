"""Content extraction and cleaning module."""

import re
import logging
from typing import Optional, Dict
from bs4 import BeautifulSoup, Comment, NavigableString
from readability import Document

logger = logging.getLogger(__name__)


class ContentExtractor:
    """Extracts and cleans main content from HTML pages."""
    
    def __init__(self):
        """Initialize the extractor."""
        pass
    
    def _remove_scripts_and_styles(self, soup: BeautifulSoup) -> BeautifulSoup:
        """Remove script and style elements."""
        for element in soup(["script", "style", "noscript"]):
            element.decompose()
        return soup
    
    def _remove_comments(self, soup: BeautifulSoup) -> BeautifulSoup:
        """Remove HTML comments."""
        comments = soup.findAll(string=lambda text: isinstance(text, Comment))
        for comment in comments:
            comment.extract()
        return soup
    
    def _remove_boilerplate(self, soup: BeautifulSoup) -> BeautifulSoup:
        """Remove common boilerplate elements."""
        # Common selectors for navigation, headers, footers, ads
        boilerplate_selectors = [
            "nav", "header", "footer", "aside",
            ".nav", ".navigation", ".navbar", ".menu",
            ".header", ".footer", ".sidebar",
            ".advertisement", ".ad", ".ads",
            ".social-share", ".share-buttons",
            ".comments", ".comment-section",
            ".breadcrumb", ".breadcrumbs",
            "[role='navigation']", "[role='banner']", "[role='contentinfo']",
            "[role='complementary']"
        ]
        
        for selector in boilerplate_selectors:
            for element in soup.select(selector):
                element.decompose()
        
        return soup
    
    def _extract_with_readability(self, html: str, url: str) -> Optional[Dict[str, str]]:
        """
        Use readability-lxml to extract main content.
        
        Returns:
            Dict with 'title' and 'content' or None if extraction fails
        """
        try:
            doc = Document(html)
            title = doc.title()
            content_html = doc.summary()
            
            if not content_html:
                return None
            
            # Parse and clean the extracted content
            content_soup = BeautifulSoup(content_html, "html.parser")
            content_soup = self._remove_scripts_and_styles(content_soup)
            content_soup = self._remove_comments(content_soup)
            
            # Get text and clean it
            text = content_soup.get_text(separator=" ", strip=True)
            
            return {
                "title": title.strip() if title else "",
                "content": text
            }
        except Exception as e:
            logger.debug(f"Readability extraction failed for {url}: {e}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup, url: str) -> str:
        """Extract page title from various sources."""
        # Try multiple title sources
        title = None
        
        # 1. Title tag
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
        
        # 2. Open Graph title
        if not title:
            og_title = soup.find("meta", property="og:title")
            if og_title and og_title.get("content"):
                title = og_title["content"].strip()
        
        # 3. H1 tag
        if not title:
            h1 = soup.find("h1")
            if h1:
                title = h1.get_text(strip=True)
        
        # 4. Fallback to URL
        if not title:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            title = parsed.path.strip("/").replace("/", " - ") or "Untitled"
        
        return title or "Untitled"
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main content using heuristics."""
        # Try common content containers
        content_selectors = [
            "main",
            "article",
            "[role='main']",
            ".content",
            ".main-content",
            ".post-content",
            ".entry-content",
            ".article-content",
            "#content",
            "#main",
            "#article"
        ]
        
        for selector in content_selectors:
            elements = soup.select(selector)
            if elements:
                # Use the first matching element
                content_soup = BeautifulSoup(str(elements[0]), "html.parser")
                content_soup = self._remove_scripts_and_styles(content_soup)
                text = content_soup.get_text(separator=" ", strip=True)
                if len(text) > 100:  # Ensure we have substantial content
                    return text
        
        # Fallback: use body without boilerplate
        body = soup.find("body")
        if body:
            body_soup = BeautifulSoup(str(body), "html.parser")
            body_soup = self._remove_boilerplate(body_soup)
            body_soup = self._remove_scripts_and_styles(body_soup)
            text = body_soup.get_text(separator=" ", strip=True)
            if len(text) > 50:
                return text
        
        return ""
    
    def _clean_text(self, text: str) -> str:
        """
        Clean extracted text.
        
        - Normalize whitespace
        - Remove excessive line breaks
        - Strip leading/trailing whitespace
        """
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Normalize line breaks (keep paragraph structure)
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        # Strip
        text = text.strip()
        
        return text
    
    def extract(self, html: str, url: str) -> Dict[str, str]:
        """
        Extract and clean content from HTML.
        
        Args:
            html: Raw HTML content
            url: Source URL (for fallback title)
        
        Returns:
            Dict with 'title' and 'body_text'
        """
        try:
            # First try readability-lxml for better content extraction
            readability_result = self._extract_with_readability(html, url)
            
            if readability_result and len(readability_result.get("content", "")) > 50:
                return {
                    "title": readability_result["title"],
                    "body_text": self._clean_text(readability_result["content"])
                }
            
            # Fallback to heuristic extraction
            soup = BeautifulSoup(html, "html.parser")
            soup = self._remove_scripts_and_styles(soup)
            soup = self._remove_comments(soup)
            soup = self._remove_boilerplate(soup)
            
            title = self._extract_title(soup, url)
            content = self._extract_main_content(soup)
            content = self._clean_text(content)
            
            return {
                "title": title,
                "body_text": content
            }
            
        except Exception as e:
            logger.error(f"Error extracting content from {url}: {e}")
            return {
                "title": "Extraction Error",
                "body_text": ""
            }

