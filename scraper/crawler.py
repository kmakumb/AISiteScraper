"""Web crawler module for discovering and fetching pages."""

import time
import logging
from typing import Set, List, Optional, Dict
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class Crawler:
    """Crawls a website starting from a seed URL with configurable limits."""
    
    def __init__(
        self,
        start_url: str,
        max_pages: int = 100,
        max_depth: int = 5,
        delay: float = 1.0,
        timeout: int = 10,
        user_agent: str = "AISiteScraper/1.0"
    ):
        """
        Initialize the crawler.
        
        Args:
            start_url: Starting URL for crawling
            max_pages: Maximum number of pages to crawl
            max_depth: Maximum depth from start URL
            delay: Delay between requests in seconds
            timeout: Request timeout in seconds
            user_agent: User agent string for requests
        """
        self.start_url = start_url
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.delay = delay
        self.timeout = timeout
        self.user_agent = user_agent
        
        # Parse base domain
        parsed = urlparse(start_url)
        self.base_domain = f"{parsed.scheme}://{parsed.netloc}"
        self.allowed_domains = {parsed.netloc}
        
        # Track visited URLs and pages to crawl
        self.visited_urls: Set[str] = set()
        self.to_crawl: List[tuple[str, int]] = []  # (url, depth)
        self.crawled_pages: List[Dict] = []
        
        # Setup session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        self.session.headers.update({"User-Agent": self.user_agent})
        
        # Check robots.txt
        self._check_robots_txt()
    
    def _check_robots_txt(self):
        """Check robots.txt for crawling rules."""
        try:
            robots_url = urljoin(self.base_domain, "/robots.txt")
            rp = RobotFileParser()
            rp.set_url(robots_url)
            rp.read()
            self.robots_allowed = rp.can_fetch(self.user_agent, self.start_url)
            if not self.robots_allowed:
                logger.warning(f"robots.txt disallows crawling {self.start_url}")
        except Exception as e:
            logger.debug(f"Could not fetch robots.txt: {e}")
            self.robots_allowed = True
    
    def _is_valid_url(self, url: str, depth: int) -> bool:
        """Check if URL should be crawled."""
        # Skip if already visited
        if url in self.visited_urls:
            return False
        
        # Skip if max depth exceeded
        if depth > self.max_depth:
            return False
        
        # Parse URL
        try:
            parsed = urlparse(url)
        except Exception:
            return False
        
        # Only crawl same domain
        if parsed.netloc not in self.allowed_domains:
            return False
        
        # Skip external links
        if not url.startswith(self.base_domain):
            return False
        
        # Skip obvious non-content pages
        skip_patterns = [
            "/login", "/signup", "/register", "/logout",
            "/search?", "/?search=", "/results?",
            "/api/", "/ajax/", "/static/", "/assets/",
            ".pdf", ".zip", ".jpg", ".png", ".gif", ".svg",
            "#", "mailto:", "tel:", "javascript:"
        ]
        url_lower = url.lower()
        if any(pattern in url_lower for pattern in skip_patterns):
            return False
        
        # Check robots.txt if available
        if hasattr(self, 'robots_allowed') and not self.robots_allowed:
            try:
                rp = RobotFileParser()
                rp.set_url(urljoin(self.base_domain, "/robots.txt"))
                rp.read()
                if not rp.can_fetch(self.user_agent, url):
                    return False
            except Exception:
                pass
        
        return True
    
    def _fetch_page(self, url: str) -> Optional[Dict]:
        """Fetch a single page and return response data."""
        try:
            logger.info(f"Fetching: {url}")
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            # Only process HTML content
            content_type = response.headers.get("Content-Type", "").lower()
            if "text/html" not in content_type:
                logger.debug(f"Skipping non-HTML content: {url}")
                return None
            
            return {
                "url": url,
                "html": response.text,
                "status_code": response.status_code,
                "content_type": content_type,
                "headers": dict(response.headers)
            }
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout fetching {url}")
            return None
        except requests.exceptions.HTTPError as e:
            logger.warning(f"HTTP error fetching {url}: {e}")
            return None
        except requests.exceptions.RequestException as e:
            logger.warning(f"Error fetching {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching {url}: {e}")
            return None
    
    def _extract_links(self, html: str, base_url: str) -> List[str]:
        """Extract all links from HTML page."""
        from bs4 import BeautifulSoup
        
        try:
            soup = BeautifulSoup(html, "html.parser")
            links = []
            
            for tag in soup.find_all("a", href=True):
                href = tag["href"]
                # Convert relative URLs to absolute
                absolute_url = urljoin(base_url, href)
                # Remove fragment
                absolute_url = absolute_url.split("#")[0]
                links.append(absolute_url)
            
            return links
        except Exception as e:
            logger.error(f"Error extracting links: {e}")
            return []
    
    def crawl(self) -> List[Dict]:
        """
        Start crawling from the seed URL.
        
        Returns:
            List of crawled page data dictionaries
        """
        logger.info(f"Starting crawl from {self.start_url}")
        logger.info(f"Max pages: {self.max_pages}, Max depth: {self.max_depth}")
        
        # Initialize crawl queue
        self.to_crawl = [(self.start_url, 0)]
        
        while self.to_crawl and len(self.crawled_pages) < self.max_pages:
            url, depth = self.to_crawl.pop(0)
            
            # Skip if already visited
            if url in self.visited_urls:
                continue
            
            # Validate URL
            if not self._is_valid_url(url, depth):
                continue
            
            # Mark as visited
            self.visited_urls.add(url)
            
            # Fetch page
            page_data = self._fetch_page(url)
            if page_data:
                self.crawled_pages.append(page_data)
                
                # Extract links for further crawling
                if depth < self.max_depth:
                    links = self._extract_links(page_data["html"], url)
                    for link in links:
                        if self._is_valid_url(link, depth + 1):
                            if (link, depth + 1) not in self.to_crawl:
                                self.to_crawl.append((link, depth + 1))
            
            # Throttle requests
            if len(self.crawled_pages) < self.max_pages:
                time.sleep(self.delay)
        
        logger.info(f"Crawling complete. Fetched {len(self.crawled_pages)} pages")
        return self.crawled_pages

