"""
Production-Ready Web Crawler Module
TSMCrawler - A comprehensive web crawler for educational institution websites.
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlunparse
import json
import csv
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from collections import defaultdict
import pandas as pd


# ============================================================================
# Custom Exception Classes
# ============================================================================

class CrawlerException(Exception):
    """Base exception class for all crawler-related errors."""
    
    def __init__(self, message: str, url: Optional[str] = None):
        """
        Initialize crawler exception.
        
        Args:
            message: Error message
            url: Optional URL associated with the error
        """
        self.message = message
        self.url = url
        super().__init__(self.message)
    
    def __str__(self) -> str:
        if self.url:
            return f"{self.message} (URL: {self.url})"
        return self.message


class URLNormalizationException(CrawlerException):
    """Raised when URL normalization fails."""
    
    def __init__(self, url: str, reason: str = "Unknown normalization error"):
        """
        Initialize URL normalization exception.
        
        Args:
            url: URL that failed to normalize
            reason: Reason for normalization failure
        """
        message = f"URL normalization failed: {reason}"
        super().__init__(message, url)
        self.reason = reason


class URLValidationException(CrawlerException):
    """Raised when URL validation fails."""
    
    def __init__(self, url: str, reason: str = "Invalid URL format"):
        """
        Initialize URL validation exception.
        
        Args:
            url: URL that failed validation
            reason: Reason for validation failure
        """
        message = f"URL validation failed: {reason}"
        super().__init__(message, url)
        self.reason = reason


class DomainNotAllowedException(CrawlerException):
    """Raised when a URL's domain is not in the allowed domains list."""
    
    def __init__(self, url: str, domain: str, allowed_domains: List[str]):
        """
        Initialize domain not allowed exception.
        
        Args:
            url: URL with disallowed domain
            domain: The domain that was rejected
            allowed_domains: List of allowed domains
        """
        message = f"Domain '{domain}' is not in allowed domains: {allowed_domains}"
        super().__init__(message, url)
        self.domain = domain
        self.allowed_domains = allowed_domains


class FetchException(CrawlerException):
    """Base exception for HTTP fetch errors."""
    
    def __init__(self, url: str, status_code: Optional[int] = None, reason: str = "Unknown fetch error"):
        """
        Initialize fetch exception.
        
        Args:
            url: URL that failed to fetch
            status_code: HTTP status code if available
            reason: Reason for fetch failure
        """
        if status_code:
            message = f"Failed to fetch URL (Status {status_code}): {reason}"
        else:
            message = f"Failed to fetch URL: {reason}"
        super().__init__(message, url)
        self.status_code = status_code
        self.reason = reason


class FetchTimeoutException(FetchException):
    """Raised when a fetch request times out."""
    
    def __init__(self, url: str, timeout: float):
        """
        Initialize fetch timeout exception.
        
        Args:
            url: URL that timed out
            timeout: Timeout value in seconds
        """
        message = f"Request timed out after {timeout} seconds"
        super().__init__(url, reason=message)
        self.timeout = timeout


class FetchConnectionException(FetchException):
    """Raised when a fetch request fails due to connection issues."""
    
    def __init__(self, url: str, reason: str = "Connection error"):
        """
        Initialize fetch connection exception.
        
        Args:
            url: URL that failed to connect
            reason: Connection error reason
        """
        super().__init__(url, reason=reason)


class FetchHTTPException(FetchException):
    """Raised when a fetch request returns an HTTP error status."""
    
    def __init__(self, url: str, status_code: int, reason: str = "HTTP error"):
        """
        Initialize fetch HTTP exception.
        
        Args:
            url: URL that returned HTTP error
            status_code: HTTP status code
            reason: HTTP error reason
        """
        super().__init__(url, status_code=status_code, reason=reason)


class ParsingException(CrawlerException):
    """Raised when HTML parsing fails."""
    
    def __init__(self, url: str, reason: str = "HTML parsing failed"):
        """
        Initialize parsing exception.
        
        Args:
            url: URL that failed to parse
            reason: Reason for parsing failure
        """
        message = f"HTML parsing failed: {reason}"
        super().__init__(message, url)
        self.reason = reason


class SaveException(CrawlerException):
    """Raised when saving data to file fails."""
    
    def __init__(self, file_path: str, reason: str = "File save failed"):
        """
        Initialize save exception.
        
        Args:
            file_path: Path to file that failed to save
            reason: Reason for save failure
        """
        message = f"Failed to save file '{file_path}': {reason}"
        super().__init__(message)
        self.file_path = file_path
        self.reason = reason


class ConfigurationException(CrawlerException):
    """Raised when crawler configuration is invalid."""
    
    def __init__(self, parameter: str, value: Any, reason: str = "Invalid configuration"):
        """
        Initialize configuration exception.
        
        Args:
            parameter: Configuration parameter name
            value: Invalid value
            reason: Reason for configuration failure
        """
        message = f"Invalid configuration for '{parameter}' (value: {value}): {reason}"
        super().__init__(message)
        self.parameter = parameter
        self.value = value
        self.reason = reason


# ============================================================================
# TSMCrawler Class
# ============================================================================

class TSMCrawler:
    """
    Production-ready web crawler for scraping educational institution websites.
    
    Features:
    - Depth-limited recursive crawling
    - Domain filtering
    - URL normalization
    - Comprehensive logging
    - CSV and JSON export
    - Crawl statistics
    """
    
    def __init__(
        self,
        base_url: str,
        max_depth: int = 3,
        request_delay: float = 1.5,
        allowed_domains: Optional[List[str]] = None,
        timeout: int = 10,
        user_agent: str = "TSM-Crawler/1.0 (Educational Project)",
        exclude_extensions: Optional[List[str]] = None
    ):
        """
        Initialize TSMCrawler instance.
        
        Args:
            base_url: Starting URL for crawling
            max_depth: Maximum depth to crawl (default: 3)
            request_delay: Delay in seconds between requests (default: 1.5)
            allowed_domains: List of allowed domains (default: None = all domains)
            timeout: Request timeout in seconds (default: 10)
            user_agent: User-Agent string for requests (default: TSM-Crawler)
            exclude_extensions: List of file extensions to exclude (default: None)
            
        Raises:
            ConfigurationException: If configuration parameters are invalid
            URLValidationException: If base_url is invalid
        """
        # Validate configuration
        TSMCrawler._validate_configuration(
            base_url=base_url,
            max_depth=max_depth,
            request_delay=request_delay,
            timeout=timeout
        )
        
        self.base_url = base_url
        self.max_depth = max_depth
        self.request_delay = request_delay
        self.allowed_domains = allowed_domains or []
        self.timeout = timeout
        self.user_agent = user_agent
        self.exclude_extensions = exclude_extensions or [".pdf", ".jpg", ".png", ".gif", ".zip"]
        
        # Initialize instance variables
        self.visited_urls: Set[str] = set()
        self.crawl_data: List[Dict[str, Any]] = []
        self.logger = self.setup_logger()
        
        # Ensure output directory exists
        try:
            Path("output").mkdir(exist_ok=True)
        except (OSError, PermissionError) as e:
            self.logger.error(f"Cannot create output directory: {e}")
            raise ConfigurationException("output_directory", "output", f"Cannot create: {str(e)}")
    
    @staticmethod
    def _validate_configuration(
        base_url: str,
        max_depth: int,
        request_delay: float,
        timeout: int
    ) -> None:
        """
        Validate crawler configuration parameters.
        
        Args:
            base_url: Starting URL
            max_depth: Maximum crawl depth
            request_delay: Delay between requests
            timeout: Request timeout
            
        Raises:
            ConfigurationException: If any parameter is invalid
            URLValidationException: If base_url is invalid
        """
        # Validate base_url
        if not base_url or not isinstance(base_url, str):
            raise ConfigurationException("base_url", base_url, "Must be a non-empty string")
        
        if not TSMCrawler.is_valid_url(base_url, raise_exception=True):
            raise URLValidationException(base_url, "Invalid URL format")
        
        # Validate max_depth
        if not isinstance(max_depth, int) or max_depth < 0:
            raise ConfigurationException("max_depth", max_depth, "Must be a non-negative integer")
        
        if max_depth > 10:
            raise ConfigurationException("max_depth", max_depth, "Max depth should not exceed 10 for safety")
        
        # Validate request_delay
        if not isinstance(request_delay, (int, float)) or request_delay < 0:
            raise ConfigurationException("request_delay", request_delay, "Must be a non-negative number")
        
        if request_delay > 60:
            raise ConfigurationException("request_delay", request_delay, "Delay should not exceed 60 seconds")
        
        # Validate timeout
        if not isinstance(timeout, int) or timeout <= 0:
            raise ConfigurationException("timeout", timeout, "Must be a positive integer")
        
        if timeout > 300:
            raise ConfigurationException("timeout", timeout, "Timeout should not exceed 300 seconds")
    
    def setup_logger(self) -> logging.Logger:
        """
        Configure and return logger instance.
        
        Logs to both console and file (output/crawler.log).
        Format: "[%(asctime)s] %(levelname)s: %(message)s"
        
        Returns:
            Configured logger instance
        """
        logger = logging.getLogger("TSMCrawler")
        logger.setLevel(logging.INFO)
        
        # Prevent duplicate handlers
        if logger.handlers:
            return logger
        
        # Create formatter
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File handler
        log_file = Path("output/crawler.log")
        log_file.parent.mkdir(exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        return logger
    
    @staticmethod
    def is_valid_url(url: str, raise_exception: bool = False) -> bool:
        """
        Check if URL has valid scheme (http/https) and netloc.
        
        Args:
            url: URL string to validate
            raise_exception: If True, raise URLValidationException instead of returning False
            
        Returns:
            True if URL is valid, False otherwise (unless raise_exception=True)
            
        Raises:
            URLValidationException: If raise_exception=True and URL is invalid
        """
        try:
            parsed = urlparse(url)
            is_valid = bool(parsed.scheme in ["http", "https"] and parsed.netloc)
            
            if not is_valid and raise_exception:
                reason = "Missing scheme or netloc"
                if parsed.scheme not in ["http", "https"]:
                    reason = f"Invalid scheme '{parsed.scheme}'. Must be 'http' or 'https'"
                elif not parsed.netloc:
                    reason = "Missing netloc (domain)"
                raise URLValidationException(url, reason)
            
            return is_valid
        except URLValidationException:
            raise
        except Exception as e:
            if raise_exception:
                raise URLValidationException(url, f"URL parsing error: {str(e)}")
            return False
    
    def is_allowed_domain(self, url: str, raise_exception: bool = False) -> bool:
        """
        Check if URL domain matches allowed_domains.
        
        Args:
            url: URL to check
            raise_exception: If True, raise DomainNotAllowedException instead of returning False
            
        Returns:
            True if domain is allowed or no restrictions, False otherwise (unless raise_exception=True)
            
        Raises:
            DomainNotAllowedException: If raise_exception=True and domain is not allowed
        """
        if not self.allowed_domains:
            return True
        
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Remove 'www.' prefix for comparison
            domain = domain.replace("www.", "")
            
            for allowed in self.allowed_domains:
                allowed_clean = allowed.lower().replace("www.", "")
                if domain == allowed_clean or domain.endswith("." + allowed_clean):
                    return True
            
            if raise_exception:
                raise DomainNotAllowedException(url, domain, self.allowed_domains)
            
            return False
        except DomainNotAllowedException:
            raise
        except Exception as e:
            self.logger.warning(f"Error checking domain for {url}: {e}")
            if raise_exception:
                raise CrawlerException(f"Domain check error: {str(e)}", url)
            return False
    
    @staticmethod
    def normalize_url(url: str, raise_exception: bool = False) -> str:
        """
        Normalize URL by removing fragments, query parameters, and trailing slashes.
        Convert to lowercase.
        
        Args:
            url: URL to normalize
            raise_exception: If True, raise URLNormalizationException on failure
            
        Returns:
            Normalized URL string
            
        Raises:
            URLNormalizationException: If raise_exception=True and normalization fails
        """
        try:
            parsed = urlparse(url.lower())
            
            # Validate basic structure
            if not parsed.scheme or not parsed.netloc:
                if raise_exception:
                    raise URLNormalizationException(url, "Missing scheme or netloc")
                return url.lower()
            
            # Remove fragment and query
            normalized = urlunparse((
                parsed.scheme,
                parsed.netloc,
                parsed.path.rstrip("/") or "/",  # Remove trailing slash but keep root
                parsed.params,
                "",  # Remove query
                ""   # Remove fragment
            ))
            
            return normalized
        except URLNormalizationException:
            raise
        except Exception as e:
            if raise_exception:
                raise URLNormalizationException(url, f"Normalization error: {str(e)}")
            # If parsing fails, return original URL (fallback)
            return url.lower()
    
    def fetch_page(self, url: str, raise_exception: bool = False) -> Optional[requests.Response]:
        """
        Fetch a web page using requests.get().
        
        Uses:
        - User-Agent header from instance variable
        - Timeout from instance variable
        - SSL certificate verification
        
        Args:
            url: URL to fetch
            raise_exception: If True, raise custom exceptions instead of returning None
            
        Returns:
            Response object if successful, None if error (unless raise_exception=True)
            
        Raises:
            FetchTimeoutException: If request times out and raise_exception=True
            FetchConnectionException: If connection fails and raise_exception=True
            FetchHTTPException: If HTTP error status and raise_exception=True
            FetchException: For other fetch errors if raise_exception=True
        """
        try:
            headers = {
                "User-Agent": self.user_agent
            }
            
            response = requests.get(
                url,
                headers=headers,
                timeout=self.timeout,
                verify=True  # Verify SSL certificates
            )
            
            response.raise_for_status()
            return response
            
        except requests.Timeout:
            self.logger.error(f"Timeout error fetching {url} (timeout: {self.timeout}s)")
            if raise_exception:
                raise FetchTimeoutException(url, self.timeout)
            return None
        except requests.ConnectionError as e:
            self.logger.error(f"Connection error fetching {url}: {str(e)}")
            if raise_exception:
                raise FetchConnectionException(url, f"Connection failed: {str(e)}")
            return None
        except requests.HTTPError as e:
            status_code = e.response.status_code if hasattr(e, 'response') and e.response else None
            self.logger.error(f"HTTP error fetching {url}: Status {status_code} - {str(e)}")
            if raise_exception:
                if status_code:
                    raise FetchHTTPException(url, status_code, str(e))
                else:
                    raise FetchException(url, reason=f"HTTP error: {str(e)}")
            return None
        except requests.RequestException as e:
            self.logger.error(f"Request error fetching {url}: {type(e).__name__} - {str(e)}")
            if raise_exception:
                raise FetchException(url, reason=f"{type(e).__name__}: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error fetching {url}: {type(e).__name__} - {str(e)}")
            if raise_exception:
                raise FetchException(url, reason=f"Unexpected error: {type(e).__name__}: {str(e)}")
            return None
    
    def extract_links(self, soup: BeautifulSoup, current_url: str) -> List[str]:
        """
        Extract all valid links from a BeautifulSoup object.
        
        Finds all <a> tags with href attribute, converts relative URLs to absolute,
        normalizes URLs, checks domain restrictions, and filters duplicates.
        
        Args:
            soup: BeautifulSoup object of the parsed page
            current_url: Current page URL for resolving relative links
            
        Returns:
            List of unique, valid, normalized URLs
        """
        links = []
        
        try:
            # Find all anchor tags with href
            for anchor in soup.find_all("a", href=True):
                href = anchor.get("href", "").strip()
                
                if not href:
                    continue
                
                # Skip mailto, tel, javascript links
                if href.startswith(("mailto:", "tel:", "javascript:", "#")):
                    continue
                
                # Skip excluded file extensions
                if any(href.lower().endswith(ext.lower()) for ext in self.exclude_extensions):
                    continue
                
                # Convert relative URL to absolute
                absolute_url = urljoin(current_url, href)
                
                # Normalize URL
                normalized_url = self.normalize_url(absolute_url)
                
                # Validate URL
                if not self.is_valid_url(normalized_url):
                    continue
                
                # Check if domain is allowed
                if not self.is_allowed_domain(normalized_url):
                    continue
                
                links.append(normalized_url)
        
        except URLValidationException:
            # Re-raise URL validation exceptions
            raise
        except DomainNotAllowedException:
            # Re-raise domain exceptions
            raise
        except Exception as e:
            error_msg = f"Error extracting links from {current_url}: {type(e).__name__} - {str(e)}"
            self.logger.warning(error_msg)
            # Continue with links extracted so far
        
        # Return unique links
        return list(set(links))
    
    @staticmethod
    def extract_page_info(soup: BeautifulSoup) -> Dict[str, Optional[str]]:
        """
        Extract page information from BeautifulSoup object.
        
        Extracts:
        - Title from <title> tag
        - Meta description from meta tag
        - Main heading from first <h1> tag
        
        Args:
            soup: BeautifulSoup object of the parsed page
            
        Returns:
            Dictionary with title, description, and heading
        """
        info = {
            "title": None,
            "description": None,
            "heading": None
        }
        
        try:
            # Extract title
            title_tag = soup.find("title")
            if title_tag:
                info["title"] = title_tag.get_text(strip=True)
            
            # Extract meta description
            meta_desc = soup.find("meta", attrs={"name": "description"})
            if not meta_desc:
                meta_desc = soup.find("meta", attrs={"property": "og:description"})
            if meta_desc:
                info["description"] = meta_desc.get("content", "").strip()
            
            # Extract first h1 heading
            h1_tag = soup.find("h1")
            if h1_tag:
                info["heading"] = h1_tag.get_text(strip=True)
        
        except Exception as e:
            # Log but don't fail - return what we have
            pass
        
        return info
    
    def crawl(self, url: str, depth: int = 0, parent_url: Optional[str] = None) -> None:
        """
        Recursively crawl a URL and its linked pages.
        
        Process:
        1. Check depth limit
        2. Check if already visited
        3. Mark as visited
        4. Fetch and parse page
        5. Extract page info and links
        6. Store crawl data
        7. Recursively crawl child links
        
        Args:
            url: URL to crawl
            depth: Current crawl depth (default: 0)
            parent_url: Parent URL that linked to this page (default: None)
        """
        # Check depth limit
        if depth > self.max_depth:
            return
        
        # Normalize URL
        normalized_url = self.normalize_url(url)
        
        # Check if already visited
        if normalized_url in self.visited_urls:
            return
        
        # Mark as visited
        self.visited_urls.add(normalized_url)
        
        # Log crawling
        self.logger.info(f"Crawling (Depth {depth}): {normalized_url}")
        
        # Fetch page
        response = self.fetch_page(normalized_url)
        
        if response is None:
            # Store failed page
            self.crawl_data.append({
                "url": normalized_url,
                "parent_url": parent_url,
                "depth": depth,
                "status_code": None,
                "title": None,
                "description": None,
                "heading": None,
                "child_count": 0
            })
            return
        
        # Parse with BeautifulSoup
        try:
            soup = BeautifulSoup(response.content, "lxml")
        except Exception as e:
            error_msg = f"Error parsing {normalized_url}: {type(e).__name__} - {str(e)}"
            self.logger.error(error_msg)
            # Store failed page with parsing error info
            self.crawl_data.append({
                "url": normalized_url,
                "parent_url": parent_url,
                "depth": depth,
                "status_code": response.status_code if response else None,
                "title": None,
                "description": None,
                "heading": None,
                "child_count": 0
            })
            return
        
        # Extract page info
        page_info = self.extract_page_info(soup)
        
        # Extract links
        child_links = self.extract_links(soup, normalized_url)
        child_count = len(child_links)
        
        # Store crawl data
        self.crawl_data.append({
            "url": normalized_url,
            "parent_url": parent_url,
            "depth": depth,
            "status_code": response.status_code,
            "title": page_info["title"],
            "description": page_info["description"],
            "heading": page_info["heading"],
            "child_count": child_count
        })
        
        # Sleep before next request
        time.sleep(self.request_delay)
        
        # Recursively crawl child links
        for child_url in child_links:
            self.crawl(child_url, depth + 1, normalized_url)
    
    def save_to_csv(self, output_path: str = "output/tsm_crawl_data.csv") -> None:
        """
        Save crawl data to CSV file using pandas.
        
        Creates DataFrame from crawl_data and saves to CSV.
        Column order: url, parent_url, depth, status_code, title, description, child_count
        
        Args:
            output_path: Path to save CSV file (default: output/tsm_crawl_data.csv)
            
        Raises:
            SaveException: If file save operation fails
        """
        try:
            if not self.crawl_data:
                self.logger.warning("No crawl data to save to CSV")
                return
            
            # Create DataFrame
            df = pd.DataFrame(self.crawl_data)
            
            # Ensure column order
            columns = ["url", "parent_url", "depth", "status_code", "title", "description", "child_count"]
            # Only include columns that exist in the data
            available_columns = [col for col in columns if col in df.columns]
            df = df[available_columns]
            
            # Save to CSV
            output_file = Path(output_path)
            try:
                output_file.parent.mkdir(parents=True, exist_ok=True)
            except (OSError, PermissionError) as e:
                raise SaveException(str(output_file), f"Cannot create directory: {str(e)}")
            
            try:
                df.to_csv(output_file, index=False, encoding="utf-8")
            except (IOError, PermissionError) as e:
                raise SaveException(str(output_file), f"File write error: {str(e)}")
            
            self.logger.info(f"Saved {len(self.crawl_data)} pages to CSV: {output_path}")
        
        except SaveException:
            raise
        except Exception as e:
            error_msg = f"Unexpected error saving CSV: {type(e).__name__} - {str(e)}"
            self.logger.error(error_msg)
            raise SaveException(output_path, error_msg)
    
    def save_to_json(self, output_path: str = "output/tsm_crawl_data.json") -> None:
        """
        Save crawl data to hierarchical JSON structure.
        
        Creates a tree structure with root node = base_url and nested children
        under each parent.
        
        Args:
            output_path: Path to save JSON file (default: output/tsm_crawl_data.json)
            
        Raises:
            SaveException: If file save operation fails
        """
        try:
            if not self.crawl_data:
                self.logger.warning("No crawl data to save to JSON")
                return
            
            # Build URL to data mapping
            url_to_data = {item["url"]: item.copy() for item in self.crawl_data}
            
            # Build parent-child relationships
            children_map = defaultdict(list)
            root_url = None
            
            for item in self.crawl_data:
                url = item["url"]
                parent = item["parent_url"]
                
                if parent is None:
                    root_url = url
                else:
                    children_map[parent].append(url)
            
            # If no explicit root, use base_url
            if root_url is None:
                root_url = self.normalize_url(self.base_url)
            
            # Recursive function to build tree
            def build_tree(url: str, visited: Set[str]) -> Dict[str, Any]:
                if url in visited or url not in url_to_data:
                    return None
                
                visited.add(url)
                data = url_to_data[url].copy()
                data["children"] = []
                
                for child_url in children_map.get(url, []):
                    child_tree = build_tree(child_url, visited)
                    if child_tree:
                        data["children"].append(child_tree)
                
                return data
            
            # Build hierarchical structure
            visited = set()
            root_tree = build_tree(root_url, visited)
            
            # If root not found in data, create it
            if root_tree is None:
                root_tree = {
                    "url": root_url,
                    "parent_url": None,
                    "depth": 0,
                    "status_code": None,
                    "title": None,
                    "description": None,
                    "heading": None,
                    "child_count": 0,
                    "children": []
                }
                # Add all top-level items as children
                for item in self.crawl_data:
                    if item["parent_url"] is None or item["parent_url"] not in url_to_data:
                        child_tree = build_tree(item["url"], visited)
                        if child_tree:
                            root_tree["children"].append(child_tree)
            
            # Save to JSON
            output_file = Path(output_path)
            try:
                output_file.parent.mkdir(parents=True, exist_ok=True)
            except (OSError, PermissionError) as e:
                raise SaveException(str(output_file), f"Cannot create directory: {str(e)}")
            
            try:
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(root_tree, f, indent=2, ensure_ascii=False)
            except (IOError, PermissionError, json.JSONEncodeError) as e:
                raise SaveException(str(output_file), f"File write/JSON encoding error: {str(e)}")
            
            self.logger.info(f"Saved hierarchical data to JSON: {output_path}")
        
        except SaveException:
            raise
        except Exception as e:
            error_msg = f"Unexpected error saving JSON: {type(e).__name__} - {str(e)}"
            self.logger.error(error_msg)
            raise SaveException(output_path, error_msg)
    
    def get_crawl_statistics(self) -> Dict[str, Any]:
        """
        Calculate and return crawl statistics.
        
        Returns:
            Dictionary containing:
            - total_pages: Total number of pages crawled
            - max_depth_reached: Maximum depth reached
            - unique_domains: Number of unique domains
            - pages_by_depth: Dictionary mapping depth to page count
            - average_children_per_page: Average number of child links per page
        """
        if not self.crawl_data:
            return {
                "total_pages": 0,
                "max_depth_reached": 0,
                "unique_domains": 0,
                "pages_by_depth": {},
                "average_children_per_page": 0.0
            }
        
        # Total pages
        total_pages = len(self.crawl_data)
        
        # Max depth reached
        max_depth_reached = max(item["depth"] for item in self.crawl_data)
        
        # Unique domains
        domains = set()
        for item in self.crawl_data:
            try:
                parsed = urlparse(item["url"])
                domain = parsed.netloc.lower().replace("www.", "")
                domains.add(domain)
            except Exception:
                pass
        unique_domains = len(domains)
        
        # Pages by depth
        pages_by_depth = defaultdict(int)
        for item in self.crawl_data:
            pages_by_depth[item["depth"]] += 1
        pages_by_depth = dict(pages_by_depth)
        
        # Average children per page
        total_children = sum(item["child_count"] for item in self.crawl_data)
        average_children = total_children / total_pages if total_pages > 0 else 0.0
        
        return {
            "total_pages": total_pages,
            "max_depth_reached": max_depth_reached,
            "unique_domains": unique_domains,
            "pages_by_depth": pages_by_depth,
            "average_children_per_page": round(average_children, 2)
        }


def main():
    """Main execution function."""
    # Example usage
    crawler = TSMCrawler(
        base_url="https://tsm.ac.in/",
        max_depth=2,
        request_delay=1.5,
        allowed_domains=["tsm.ac.in"],
        timeout=10,
        user_agent="TSM-Crawler/1.0 (Educational Project for Portfolio)",
        exclude_extensions=[".pdf", ".jpg", ".png", ".gif", ".zip"]
    )
    
    # Start crawling
    crawler.crawl(crawler.base_url)
    
    # Save results
    crawler.save_to_csv()
    crawler.save_to_json()
    
    # Print statistics
    stats = crawler.get_crawl_statistics()
    print("\n" + "="*50)
    print("CRAWL STATISTICS")
    print("="*50)
    print(f"Total Pages Crawled: {stats['total_pages']}")
    print(f"Max Depth Reached: {stats['max_depth_reached']}")
    print(f"Unique Domains: {stats['unique_domains']}")
    print(f"Average Children per Page: {stats['average_children_per_page']}")
    print("\nPages by Depth:")
    for depth, count in sorted(stats['pages_by_depth'].items()):
        print(f"  Depth {depth}: {count} pages")
    print("="*50)


if __name__ == "__main__":
    main()
