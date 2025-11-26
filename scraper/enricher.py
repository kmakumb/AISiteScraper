"""Content enrichment module for AI-ready metadata."""

import re
from datetime import datetime, timezone
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class ContentEnricher:
    """Enriches extracted content with AI-ready metadata and signals."""
    
    def __init__(self):
        """Initialize the enricher."""
        # Simple language detection patterns (can be improved with langdetect library)
        self.language_patterns = {
            "en": [
                r"\b(the|and|or|but|in|on|at|to|for|of|with|by)\b",
                r"\b(is|are|was|were|been|being|have|has|had)\b",
            ],
            "es": [
                r"\b(el|la|los|las|un|una|con|por|para|de|en)\b",
                r"\b(es|son|era|eran|ser|estar)\b",
            ],
            "fr": [
                r"\b(le|la|les|un|une|avec|pour|de|dans|sur)\b",
                r"\b(est|sont|était|étaient|être|avoir)\b",
            ],
            "de": [
                r"\b(der|die|das|ein|eine|mit|für|von|in|auf)\b",
                r"\b(ist|sind|war|waren|sein|haben)\b",
            ],
        }
    
    def _detect_language(self, text: str) -> str:
        """
        Detect language using simple heuristics.
        
        Returns language code (default: 'en')
        """
        if not text or len(text) < 50:
            return "en"
        
        text_lower = text.lower()
        scores = {}
        
        for lang, patterns in self.language_patterns.items():
            score = sum(len(re.findall(pattern, text_lower, re.IGNORECASE)) for pattern in patterns)
            scores[lang] = score
        
        if scores:
            detected = max(scores, key=scores.get)
            # Only return if confidence is reasonable
            if scores[detected] > 5:
                return detected
        
        return "en"  # Default to English
    
    def _detect_content_type(self, url: str, title: str, body_text: str) -> str:
        """
        Detect content type based on URL patterns and content.
        
        Returns: content type (e.g., 'article', 'doc_page', 'product_page')
        """
        url_lower = url.lower()
        title_lower = title.lower()
        
        # Documentation pages
        if any(term in url_lower for term in ["/docs/", "/documentation/", "/guide/", "/tutorial/"]):
            return "doc_page"
        
        # Blog posts / articles
        if any(term in url_lower for term in ["/blog/", "/post/", "/article/", "/news/"]):
            return "article"
        
        # Product pages
        if any(term in url_lower for term in ["/product/", "/shop/", "/item/", "/p/"]):
            return "product_page"
        
        # Homepage
        if url.rstrip("/").endswith(("com", "org", "net", "io")) or url.count("/") <= 2:
            return "homepage"
        
        # Default to article for content-rich pages
        if len(body_text) > 500:
            return "article"
        
        return "page"
    
    def _estimate_reading_time(self, word_count: int) -> int:
        """
        Estimate reading time in minutes.
        
        Assumes average reading speed of 200 words per minute.
        """
        return max(1, round(word_count / 200))
    
    def _has_code(self, text: str) -> bool:
        """
        Detect if content contains code snippets.
        
        Looks for common code patterns.
        """
        code_indicators = [
            r"function\s+\w+\s*\(",
            r"def\s+\w+\s*\(",
            r"class\s+\w+",
            r"import\s+\w+",
            r"<\?php",
            r"<script",
            r"```",
            r"`[^`]+`",
        ]
        
        for pattern in code_indicators:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    def enrich(
        self,
        url: str,
        title: str,
        body_text: str,
        fetched_at: Optional[datetime] = None
    ) -> Dict:
        """
        Enrich document with metadata and AI-ready signals.
        
        Args:
            url: Document URL
            title: Document title
            body_text: Main body text
            fetched_at: Timestamp when document was fetched (default: now)
        
        Returns:
            Enriched document dictionary
        """
        if fetched_at is None:
            fetched_at = datetime.now(timezone.utc)
        
        # Basic counts
        char_count = len(body_text)
        word_count = len(body_text.split()) if body_text else 0
        
        # Language detection
        language = self._detect_language(body_text)
        
        # Content type
        content_type = self._detect_content_type(url, title, body_text)
        
        # Reading time
        reading_time_minutes = self._estimate_reading_time(word_count)
        
        # Code detection
        has_code = self._has_code(body_text)
        
        # Quality signals
        is_substantial = word_count >= 100
        is_long_form = word_count >= 1000
        
        # Build enriched document
        enriched = {
            "url": url,
            "title": title,
            "body_text": body_text,
            "metadata": {
                "fetched_at": fetched_at.isoformat(),
                "language": language,
                "content_type": content_type,
                "word_count": word_count,
                "char_count": char_count,
                "reading_time_minutes": reading_time_minutes,
                "has_code": has_code,
                "is_substantial": is_substantial,
                "is_long_form": is_long_form,
            }
        }
        
        return enriched

