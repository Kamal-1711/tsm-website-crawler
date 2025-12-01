"""
SEO Analyzer Module
====================

Comprehensive SEO analysis for website pages with actionable recommendations.

Features:
- Page metadata analysis (titles, descriptions, H1 tags)
- URL structure analysis
- Internal linking analysis
- Keyword presence analysis
- Priority recommendations
- Detailed SEO reports

Author: TSM Web Crawler Project
"""

from __future__ import annotations

import json
import logging
import re
import statistics
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse, parse_qs

import pandas as pd
import numpy as np

# ---------------------------------------------------------------------------
# Logging Setup
# ---------------------------------------------------------------------------

logger = logging.getLogger("SEOAnalyzer")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Optimal ranges
TITLE_MIN_LENGTH = 30
TITLE_OPTIMAL_MIN = 50
TITLE_OPTIMAL_MAX = 60
TITLE_MAX_LENGTH = 70

DESCRIPTION_MIN_LENGTH = 80
DESCRIPTION_OPTIMAL_MIN = 120
DESCRIPTION_OPTIMAL_MAX = 160
DESCRIPTION_MAX_LENGTH = 170

URL_OPTIMAL_MIN = 30
URL_OPTIMAL_MAX = 75
URL_MAX_LENGTH = 100

# Action words for meta descriptions
ACTION_WORDS = [
    "discover", "learn", "explore", "find", "get", "start", "join",
    "apply", "enroll", "register", "download", "contact", "view",
    "see", "check", "read", "browse", "search", "submit", "request",
]

# Common stop words to ignore in keyword analysis
STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "up", "about", "into", "over", "after",
    "is", "are", "was", "were", "be", "been", "being", "have", "has",
    "had", "do", "does", "did", "will", "would", "could", "should",
    "may", "might", "must", "shall", "can", "this", "that", "these",
    "those", "it", "its", "as", "if", "then", "than", "so", "no", "not",
    "only", "own", "same", "too", "very", "just", "also", "now", "here",
}


# ---------------------------------------------------------------------------
# SEO Analyzer Class
# ---------------------------------------------------------------------------

class SEOAnalyzer:
    """
    Comprehensive SEO analyzer for website pages.
    
    Analyzes page metadata, URL structure, internal linking, and keyword
    presence to provide actionable SEO recommendations.
    """
    
    def __init__(self, csv_file_path: str):
        """
        Initialize the SEO analyzer with crawled data.
        
        Args:
            csv_file_path: Path to the CSV file containing crawled data.
        """
        self.csv_file_path = Path(csv_file_path)
        
        if not self.csv_file_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_file_path}")
        
        # Load data
        self.df = pd.read_csv(self.csv_file_path)
        self._normalize_data()
        
        # Initialize analysis results
        self.metadata_analysis: Dict[str, Any] = {}
        self.url_analysis: Dict[str, Any] = {}
        self.linking_analysis: Dict[str, Any] = {}
        self.keyword_analysis: Dict[str, Any] = {}
        self.overall_score: float = 0.0
        self.recommendations: List[Dict[str, Any]] = []
        
        logger.info(f"SEO Analyzer initialized with {len(self.df)} pages")
    
    def _normalize_data(self) -> None:
        """Normalize and clean the loaded data."""
        # Ensure required columns exist
        required_cols = ["url", "title", "depth"]
        for col in required_cols:
            if col not in self.df.columns:
                self.df[col] = ""
        
        # Fill NaN values
        for col in ["title", "description", "heading", "url", "parent_url"]:
            if col in self.df.columns:
                self.df[col] = self.df[col].fillna("").astype(str)
        
        # Ensure numeric columns
        for col in ["depth", "child_count", "status_code"]:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors="coerce").fillna(0).astype(int)
    
    # -----------------------------------------------------------------------
    # Metadata Analysis
    # -----------------------------------------------------------------------
    
    def analyze_page_metadata(self) -> Dict[str, Any]:
        """
        Analyze page titles, meta descriptions, and H1 tags.
        
        Returns:
            Dictionary containing metadata analysis results.
        """
        logger.info("Analyzing page metadata...")
        
        title_issues = []
        description_issues = []
        h1_issues = []
        
        title_scores = []
        description_scores = []
        h1_scores = []
        
        # Track duplicates
        title_counts = Counter(self.df["title"].tolist())
        description_counts = Counter(
            self.df["description"].tolist() if "description" in self.df.columns else []
        )
        
        for _, row in self.df.iterrows():
            url = row["url"]
            title = row.get("title", "")
            description = row.get("description", "")
            h1 = row.get("heading", "")
            
            # Analyze title
            title_result = self._analyze_title(url, title, title_counts)
            title_scores.append(title_result["score"])
            if title_result["issues"]:
                title_issues.extend(title_result["issues"])
            
            # Analyze description
            desc_result = self._analyze_description(url, description, description_counts)
            description_scores.append(desc_result["score"])
            if desc_result["issues"]:
                description_issues.extend(desc_result["issues"])
            
            # Analyze H1
            h1_result = self._analyze_h1(url, h1, title)
            h1_scores.append(h1_result["score"])
            if h1_result["issues"]:
                h1_issues.extend(h1_result["issues"])
        
        # Calculate overall metadata score
        avg_title_score = statistics.mean(title_scores) if title_scores else 0
        avg_description_score = statistics.mean(description_scores) if description_scores else 0
        avg_h1_score = statistics.mean(h1_scores) if h1_scores else 0
        
        overall_metadata_score = (
            avg_title_score * 0.4 +
            avg_description_score * 0.4 +
            avg_h1_score * 0.2
        )
        
        # Count issues by type
        missing_titles = sum(1 for i in title_issues if "Missing" in i.get("issue", ""))
        short_titles = sum(1 for i in title_issues if "too short" in i.get("issue", ""))
        long_titles = sum(1 for i in title_issues if "too long" in i.get("issue", ""))
        duplicate_titles = sum(1 for i in title_issues if "Duplicate" in i.get("issue", ""))
        
        missing_descriptions = sum(1 for i in description_issues if "Missing" in i.get("issue", ""))
        short_descriptions = sum(1 for i in description_issues if "too short" in i.get("issue", ""))
        long_descriptions = sum(1 for i in description_issues if "too long" in i.get("issue", ""))
        duplicate_descriptions = sum(1 for i in description_issues if "Duplicate" in i.get("issue", ""))
        
        missing_h1 = sum(1 for i in h1_issues if "Missing" in i.get("issue", ""))
        
        self.metadata_analysis = {
            "total_pages": len(self.df),
            "title_analysis": {
                "average_score": round(avg_title_score, 1),
                "optimal_count": sum(1 for s in title_scores if s >= 80),
                "missing_count": missing_titles,
                "too_short_count": short_titles,
                "too_long_count": long_titles,
                "duplicate_count": duplicate_titles,
                "issues": title_issues[:20],  # Limit to 20 examples
            },
            "description_analysis": {
                "average_score": round(avg_description_score, 1),
                "optimal_count": sum(1 for s in description_scores if s >= 80),
                "missing_count": missing_descriptions,
                "too_short_count": short_descriptions,
                "too_long_count": long_descriptions,
                "duplicate_count": duplicate_descriptions,
                "issues": description_issues[:20],
            },
            "h1_analysis": {
                "average_score": round(avg_h1_score, 1),
                "missing_count": missing_h1,
                "issues": h1_issues[:20],
            },
            "pages_with_title_issues": len(set(i["url"] for i in title_issues)),
            "pages_with_description_issues": len(set(i["url"] for i in description_issues)),
            "pages_with_h1_issues": len(set(i["url"] for i in h1_issues)),
            "overall_metadata_score": round(overall_metadata_score, 1),
        }
        
        logger.info(f"Metadata analysis complete. Score: {overall_metadata_score:.1f}/100")
        
        return self.metadata_analysis
    
    def _analyze_title(
        self, url: str, title: str, title_counts: Counter
    ) -> Dict[str, Any]:
        """Analyze a single page title."""
        issues = []
        score = 100
        
        title_len = len(title.strip())
        
        # Check for missing title
        if not title or title_len == 0:
            issues.append({
                "url": url,
                "issue": "Missing title tag",
                "severity": "critical",
                "recommendation": "Add a descriptive title tag (50-60 characters)",
            })
            return {"score": 0, "issues": issues}
        
        # Check length
        if title_len < TITLE_MIN_LENGTH:
            issues.append({
                "url": url,
                "issue": f"Title too short ({title_len} chars)",
                "current": title[:50],
                "severity": "high",
                "recommendation": f"Expand title to 50-60 characters (currently {title_len})",
            })
            score = 30
        elif title_len < TITLE_OPTIMAL_MIN:
            score = 70
        elif title_len > TITLE_MAX_LENGTH:
            issues.append({
                "url": url,
                "issue": f"Title too long ({title_len} chars)",
                "current": title[:70] + "...",
                "severity": "medium",
                "recommendation": f"Shorten title to 50-60 characters (currently {title_len})",
            })
            score = 50
        elif title_len > TITLE_OPTIMAL_MAX:
            score = 80
        
        # Check for duplicates
        if title_counts.get(title, 0) > 1:
            issues.append({
                "url": url,
                "issue": f"Duplicate title (used {title_counts[title]} times)",
                "current": title[:50],
                "severity": "high",
                "recommendation": "Create unique title for this page",
            })
            score = min(score, 50)
        
        # Check for generic titles
        generic_titles = ["home", "welcome", "untitled", "page", "document"]
        if any(g in title.lower() for g in generic_titles) and title_len < 20:
            issues.append({
                "url": url,
                "issue": "Generic/non-descriptive title",
                "current": title,
                "severity": "medium",
                "recommendation": "Use a descriptive title with keywords",
            })
            score = min(score, 60)
        
        return {"score": score, "issues": issues}
    
    def _analyze_description(
        self, url: str, description: str, desc_counts: Counter
    ) -> Dict[str, Any]:
        """Analyze a single page meta description."""
        issues = []
        score = 100
        
        desc_len = len(description.strip())
        
        # Check for missing description
        if not description or desc_len == 0:
            issues.append({
                "url": url,
                "issue": "Missing meta description",
                "severity": "high",
                "recommendation": "Add a compelling meta description (120-160 characters)",
            })
            return {"score": 0, "issues": issues}
        
        # Check length
        if desc_len < DESCRIPTION_MIN_LENGTH:
            issues.append({
                "url": url,
                "issue": f"Description too short ({desc_len} chars)",
                "current": description[:80],
                "severity": "medium",
                "recommendation": f"Expand description to 120-160 characters (currently {desc_len})",
            })
            score = 40
        elif desc_len < DESCRIPTION_OPTIMAL_MIN:
            score = 70
        elif desc_len > DESCRIPTION_MAX_LENGTH:
            issues.append({
                "url": url,
                "issue": f"Description too long ({desc_len} chars)",
                "current": description[:100] + "...",
                "severity": "low",
                "recommendation": f"Shorten description to 120-160 characters (currently {desc_len})",
            })
            score = 70
        elif desc_len > DESCRIPTION_OPTIMAL_MAX:
            score = 85
        
        # Check for duplicates
        if desc_counts.get(description, 0) > 1:
            issues.append({
                "url": url,
                "issue": f"Duplicate description (used {desc_counts[description]} times)",
                "severity": "medium",
                "recommendation": "Create unique description for this page",
            })
            score = min(score, 60)
        
        # Check for action words
        desc_lower = description.lower()
        has_action_word = any(word in desc_lower for word in ACTION_WORDS)
        if not has_action_word and desc_len > 50:
            issues.append({
                "url": url,
                "issue": "Description lacks call-to-action",
                "severity": "low",
                "recommendation": "Add action words like 'Discover', 'Learn', 'Apply', 'Explore'",
            })
            score = min(score, 80)
        
        return {"score": score, "issues": issues}
    
    def _analyze_h1(self, url: str, h1: str, title: str) -> Dict[str, Any]:
        """Analyze H1 tag."""
        issues = []
        score = 100
        
        h1_clean = h1.strip()
        
        # Check for missing H1
        if not h1_clean:
            issues.append({
                "url": url,
                "issue": "Missing H1 tag",
                "severity": "high",
                "recommendation": "Add a descriptive H1 heading to the page",
            })
            return {"score": 0, "issues": issues}
        
        # Check for generic H1
        generic_h1s = ["welcome", "home", "untitled", "page"]
        if h1_clean.lower() in generic_h1s:
            issues.append({
                "url": url,
                "issue": f"Generic H1: '{h1_clean}'",
                "severity": "medium",
                "recommendation": "Use a descriptive H1 that matches page content",
            })
            score = 50
        
        # Check H1 length
        if len(h1_clean) < 10:
            issues.append({
                "url": url,
                "issue": f"H1 too short: '{h1_clean}'",
                "severity": "low",
                "recommendation": "Make H1 more descriptive (10-70 characters)",
            })
            score = min(score, 70)
        elif len(h1_clean) > 100:
            issues.append({
                "url": url,
                "issue": "H1 too long",
                "severity": "low",
                "recommendation": "Shorten H1 to under 70 characters",
            })
            score = min(score, 80)
        
        return {"score": score, "issues": issues}
    
    # -----------------------------------------------------------------------
    # URL Structure Analysis
    # -----------------------------------------------------------------------
    
    def analyze_url_structure(self) -> Dict[str, Any]:
        """
        Analyze URL structure for SEO optimization.
        
        Returns:
            Dictionary containing URL analysis results.
        """
        logger.info("Analyzing URL structure...")
        
        url_issues = []
        url_scores = []
        
        # Track URL patterns
        long_urls = []
        urls_with_params = []
        poor_keyword_urls = []
        url_slugs = Counter()
        
        for _, row in self.df.iterrows():
            url = row["url"]
            result = self._analyze_url(url)
            url_scores.append(result["score"])
            
            if result["issues"]:
                url_issues.extend(result["issues"])
            
            if result.get("is_long"):
                long_urls.append(url)
            if result.get("has_params"):
                urls_with_params.append(url)
            if result.get("poor_keywords"):
                poor_keyword_urls.append(url)
            
            # Track slug for duplicate detection
            parsed = urlparse(url)
            slug = parsed.path.split("/")[-1] if parsed.path else ""
            if slug:
                url_slugs[slug] += 1
        
        # Find duplicate slugs
        duplicate_slugs = {slug: count for slug, count in url_slugs.items() if count > 1 and slug}
        
        avg_url_score = statistics.mean(url_scores) if url_scores else 0
        
        self.url_analysis = {
            "total_urls": len(self.df),
            "average_score": round(avg_url_score, 1),
            "pages_with_long_urls": len(long_urls),
            "pages_with_parameters": len(urls_with_params),
            "pages_with_poor_keywords": len(poor_keyword_urls),
            "duplicate_slugs": len(duplicate_slugs),
            "url_structure_score": round(avg_url_score, 1),
            "long_urls": long_urls[:10],
            "parameter_urls": urls_with_params[:10],
            "poor_keyword_urls": poor_keyword_urls[:10],
            "issues": url_issues[:20],
            "recommendations": self._get_url_recommendations(
                len(long_urls), len(urls_with_params), len(poor_keyword_urls)
            ),
        }
        
        logger.info(f"URL analysis complete. Score: {avg_url_score:.1f}/100")
        
        return self.url_analysis
    
    def _analyze_url(self, url: str) -> Dict[str, Any]:
        """Analyze a single URL."""
        issues = []
        score = 100
        is_long = False
        has_params = False
        poor_keywords = False
        
        try:
            parsed = urlparse(url)
            path = parsed.path
            query = parsed.query
            
            # Check URL length
            url_len = len(url)
            if url_len > URL_MAX_LENGTH:
                issues.append({
                    "url": url[:80] + "...",
                    "issue": f"URL too long ({url_len} chars)",
                    "severity": "medium",
                    "recommendation": "Shorten URL to under 75 characters",
                })
                score = 50
                is_long = True
            elif url_len > URL_OPTIMAL_MAX:
                score = 80
                is_long = True
            
            # Check for query parameters
            if query:
                params = parse_qs(query)
                if len(params) > 2:
                    issues.append({
                        "url": url[:80],
                        "issue": f"Too many URL parameters ({len(params)})",
                        "severity": "medium",
                        "recommendation": "Use clean URLs without excessive parameters",
                    })
                    score = min(score, 60)
                    has_params = True
            
            # Check for keyword presence in URL
            path_parts = [p for p in path.split("/") if p]
            if path_parts:
                last_part = path_parts[-1]
                # Check for non-descriptive URLs
                if re.match(r'^(page|item|post|node|id)?\d+$', last_part, re.IGNORECASE):
                    issues.append({
                        "url": url,
                        "issue": "URL lacks descriptive keywords",
                        "severity": "low",
                        "recommendation": "Use descriptive keywords in URL path",
                    })
                    score = min(score, 70)
                    poor_keywords = True
            
            # Check for special characters
            if re.search(r'[^\w\-/\.\?=&%]', url):
                issues.append({
                    "url": url[:80],
                    "issue": "URL contains special characters",
                    "severity": "low",
                    "recommendation": "Use only alphanumeric characters, hyphens, and slashes",
                })
                score = min(score, 80)
            
            # Check for uppercase
            if any(c.isupper() for c in path):
                score = min(score, 90)  # Minor penalty
            
        except Exception as e:
            logger.warning(f"Error analyzing URL {url}: {e}")
            score = 50
        
        return {
            "score": score,
            "issues": issues,
            "is_long": is_long,
            "has_params": has_params,
            "poor_keywords": poor_keywords,
        }
    
    def _get_url_recommendations(
        self, long_count: int, param_count: int, poor_keyword_count: int
    ) -> List[str]:
        """Generate URL structure recommendations."""
        recommendations = []
        
        if long_count > 0:
            recommendations.append(
                f"Shorten {long_count} URLs that exceed 75 characters"
            )
        
        if param_count > 0:
            recommendations.append(
                f"Convert {param_count} parameter-based URLs to clean URLs"
            )
        
        if poor_keyword_count > 0:
            recommendations.append(
                f"Add descriptive keywords to {poor_keyword_count} URLs"
            )
        
        if not recommendations:
            recommendations.append("URL structure is well-optimized")
        
        return recommendations
    
    # -----------------------------------------------------------------------
    # Internal Linking Analysis
    # -----------------------------------------------------------------------
    
    def analyze_internal_linking(self) -> Dict[str, Any]:
        """
        Analyze internal linking structure for SEO.
        
        Returns:
            Dictionary containing linking analysis results.
        """
        logger.info("Analyzing internal linking...")
        
        # Build link graph
        all_urls = set(self.df["url"].tolist())
        parent_urls = set(self.df["parent_url"].dropna().tolist()) if "parent_url" in self.df.columns else set()
        
        # Find orphan pages (no parent, not homepage)
        orphan_pages = []
        for _, row in self.df.iterrows():
            url = row["url"]
            parent = row.get("parent_url", "")
            depth = row.get("depth", 0)
            
            # Skip homepage
            if depth == 0:
                continue
            
            # Check if page has a valid parent
            if not parent or parent not in all_urls:
                orphan_pages.append({
                    "url": url,
                    "title": row.get("title", "")[:50],
                    "depth": depth,
                })
        
        # Find dead ends (pages with no outbound links)
        dead_ends = []
        for _, row in self.df.iterrows():
            child_count = row.get("child_count", 0)
            if child_count == 0:
                dead_ends.append({
                    "url": row["url"],
                    "title": row.get("title", "")[:50],
                    "depth": row.get("depth", 0),
                })
        
        # Find pages too deep (depth > 3)
        deep_pages = []
        for _, row in self.df.iterrows():
            depth = row.get("depth", 0)
            if depth > 3:
                deep_pages.append({
                    "url": row["url"],
                    "title": row.get("title", "")[:50],
                    "depth": depth,
                })
        
        # Calculate link distribution
        child_counts = self.df["child_count"].tolist() if "child_count" in self.df.columns else []
        avg_links = statistics.mean(child_counts) if child_counts else 0
        
        # Calculate linking score
        total_pages = len(self.df)
        orphan_ratio = len(orphan_pages) / total_pages if total_pages > 0 else 0
        dead_end_ratio = len(dead_ends) / total_pages if total_pages > 0 else 0
        deep_ratio = len(deep_pages) / total_pages if total_pages > 0 else 0
        
        linking_score = 100
        linking_score -= orphan_ratio * 100  # Orphans heavily penalized
        linking_score -= dead_end_ratio * 30  # Dead ends moderately penalized
        linking_score -= deep_ratio * 20  # Deep pages slightly penalized
        linking_score = max(0, min(100, linking_score))
        
        self.linking_analysis = {
            "total_pages": total_pages,
            "orphan_pages": len(orphan_pages),
            "dead_ends": len(dead_ends),
            "pages_too_deep": len(deep_pages),
            "average_links_per_page": round(avg_links, 1),
            "linking_score": round(linking_score, 1),
            "orphan_pages_list": orphan_pages[:15],
            "dead_ends_list": dead_ends[:15],
            "deep_pages_list": deep_pages[:15],
            "improvements": self._get_linking_improvements(
                len(orphan_pages), len(dead_ends), len(deep_pages)
            ),
        }
        
        logger.info(f"Linking analysis complete. Score: {linking_score:.1f}/100")
        
        return self.linking_analysis
    
    def _get_linking_improvements(
        self, orphan_count: int, dead_end_count: int, deep_count: int
    ) -> List[str]:
        """Generate linking improvement recommendations."""
        improvements = []
        
        if orphan_count > 0:
            improvements.append(
                f"Add internal links to {orphan_count} orphan pages to make them discoverable"
            )
        
        if dead_end_count > 5:
            improvements.append(
                f"Add related links to {dead_end_count} dead-end pages to improve navigation"
            )
        
        if deep_count > 0:
            improvements.append(
                f"Restructure {deep_count} deep pages to be within 3 clicks of homepage"
            )
        
        if not improvements:
            improvements.append("Internal linking structure is well-optimized")
        
        return improvements
    
    # -----------------------------------------------------------------------
    # Keyword Analysis
    # -----------------------------------------------------------------------
    
    def analyze_keyword_presence(self) -> Dict[str, Any]:
        """
        Analyze keyword usage across pages.
        
        Returns:
            Dictionary containing keyword analysis results.
        """
        logger.info("Analyzing keyword presence...")
        
        # Extract keywords from all pages
        all_keywords = []
        page_keywords = []
        
        for _, row in self.df.iterrows():
            url = row["url"]
            title = row.get("title", "")
            description = row.get("description", "")
            h1 = row.get("heading", "")
            
            # Extract keywords from each element
            title_keywords = self._extract_keywords(title)
            desc_keywords = self._extract_keywords(description)
            url_keywords = self._extract_keywords_from_url(url)
            h1_keywords = self._extract_keywords(h1)
            
            # Combine all keywords
            combined = set(title_keywords + desc_keywords + url_keywords + h1_keywords)
            all_keywords.extend(combined)
            
            # Calculate keyword consistency for this page
            consistency_score = self._calculate_keyword_consistency(
                title_keywords, desc_keywords, url_keywords, h1_keywords
            )
            
            page_keywords.append({
                "url": url,
                "title_keywords": title_keywords,
                "desc_keywords": desc_keywords,
                "url_keywords": url_keywords,
                "h1_keywords": h1_keywords,
                "consistency_score": consistency_score,
            })
        
        # Find most common keywords
        keyword_counts = Counter(all_keywords)
        top_keywords = keyword_counts.most_common(20)
        
        # Find pages missing keywords
        pages_missing_keywords = []
        for pk in page_keywords:
            if pk["consistency_score"] < 50:
                pages_missing_keywords.append({
                    "url": pk["url"],
                    "score": pk["consistency_score"],
                })
        
        # Calculate overall keyword score
        avg_consistency = statistics.mean(
            [pk["consistency_score"] for pk in page_keywords]
        ) if page_keywords else 0
        
        self.keyword_analysis = {
            "total_pages": len(self.df),
            "top_keywords": top_keywords,
            "pages_missing_keywords": len(pages_missing_keywords),
            "keyword_consistency_score": round(avg_consistency, 1),
            "pages_with_low_consistency": pages_missing_keywords[:15],
            "keyword_gaps": self._identify_keyword_gaps(page_keywords),
            "recommendations": self._get_keyword_recommendations(
                avg_consistency, len(pages_missing_keywords)
            ),
        }
        
        logger.info(f"Keyword analysis complete. Score: {avg_consistency:.1f}/100")
        
        return self.keyword_analysis
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from text."""
        if not text:
            return []
        
        # Tokenize and clean
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        # Remove stop words
        keywords = [w for w in words if w not in STOP_WORDS]
        
        return keywords
    
    def _extract_keywords_from_url(self, url: str) -> List[str]:
        """Extract keywords from URL path."""
        try:
            parsed = urlparse(url)
            path = parsed.path
            
            # Split path and extract words
            parts = re.findall(r'[a-zA-Z]{3,}', path.lower())
            
            # Remove common URL words
            url_stop_words = {"www", "http", "https", "html", "php", "asp", "htm"}
            keywords = [p for p in parts if p not in url_stop_words and p not in STOP_WORDS]
            
            return keywords
        except Exception:
            return []
    
    def _calculate_keyword_consistency(
        self,
        title_kw: List[str],
        desc_kw: List[str],
        url_kw: List[str],
        h1_kw: List[str],
    ) -> float:
        """Calculate keyword consistency across page elements."""
        if not any([title_kw, desc_kw, url_kw, h1_kw]):
            return 0
        
        # Find common keywords
        all_sets = [set(kw) for kw in [title_kw, desc_kw, url_kw, h1_kw] if kw]
        
        if len(all_sets) < 2:
            return 50  # Not enough data
        
        # Calculate overlap
        common = set.intersection(*all_sets) if all_sets else set()
        total_unique = set.union(*all_sets) if all_sets else set()
        
        if not total_unique:
            return 50
        
        # Score based on how many elements share keywords
        score = 0
        elements_with_keywords = sum(1 for kw in [title_kw, desc_kw, url_kw, h1_kw] if kw)
        
        if common:
            score = (len(common) / len(total_unique)) * 100
        else:
            # Partial credit for having keywords in multiple places
            score = (elements_with_keywords / 4) * 60
        
        return min(100, score)
    
    def _identify_keyword_gaps(self, page_keywords: List[Dict]) -> List[Dict[str, Any]]:
        """Identify pages with keyword gaps."""
        gaps = []
        
        for pk in page_keywords:
            if not pk["title_keywords"] and pk["url_keywords"]:
                gaps.append({
                    "url": pk["url"],
                    "issue": "Keywords in URL but not in title",
                    "suggestion": f"Add '{pk['url_keywords'][0]}' to title",
                })
            elif pk["title_keywords"] and not pk["desc_keywords"]:
                gaps.append({
                    "url": pk["url"],
                    "issue": "Keywords in title but not in description",
                    "suggestion": f"Add '{pk['title_keywords'][0]}' to description",
                })
        
        return gaps[:10]
    
    def _get_keyword_recommendations(
        self, avg_consistency: float, missing_count: int
    ) -> List[str]:
        """Generate keyword recommendations."""
        recommendations = []
        
        if avg_consistency < 60:
            recommendations.append(
                "Improve keyword consistency by using same terms in title, description, and H1"
            )
        
        if missing_count > 10:
            recommendations.append(
                f"Add relevant keywords to {missing_count} pages with low keyword presence"
            )
        
        recommendations.append(
            "Ensure primary keyword appears in: title, meta description, URL, and H1"
        )
        
        return recommendations
    
    # -----------------------------------------------------------------------
    # Individual Page Scores
    # -----------------------------------------------------------------------
    
    def get_individual_page_scores(self) -> List[Dict[str, Any]]:
        """
        Calculate SEO score for each individual page.
        
        For each page calculates:
        - Title score (0-100): Based on length, keywords, uniqueness
        - Meta score (0-100): Based on description length, quality, action words
        - H1 score (0-100): Based on presence, relevance, length
        - URL score (0-100): Based on structure, keywords, length
        - Links score (0-100): Based on inbound/outbound link balance
        
        Returns:
            Sorted list of page scores (lowest first) with specific fixes.
        """
        logger.info("Calculating individual page SEO scores...")
        
        # Build link graph for inbound link calculation
        all_urls = set(self.df["url"].tolist())
        inbound_links = defaultdict(int)
        
        for _, row in self.df.iterrows():
            parent = row.get("parent_url", "")
            if parent and parent in all_urls:
                # The current page is a child of parent, so parent has outbound link to this page
                # This page has inbound link from parent
                url = row["url"]
                inbound_links[url] += 1
        
        # Track title and description counts for duplicate detection
        title_counts = Counter(self.df["title"].tolist())
        desc_counts = Counter(
            self.df["description"].tolist() if "description" in self.df.columns else []
        )
        
        page_scores = []
        
        for _, row in self.df.iterrows():
            url = row["url"]
            title = row.get("title", "")
            description = row.get("description", "")
            h1 = row.get("heading", "")
            depth = row.get("depth", 0)
            child_count = row.get("child_count", 0)
            
            # Calculate individual scores
            title_score, title_fixes = self._calculate_title_score(url, title, title_counts)
            meta_score, meta_fixes = self._calculate_meta_score(url, description, desc_counts)
            h1_score, h1_fixes = self._calculate_h1_score(url, h1, title)
            url_score, url_fixes = self._calculate_url_score_detailed(url)
            links_score, links_fixes = self._calculate_links_score(
                url, inbound_links.get(url, 0), child_count, depth
            )
            
            # Calculate overall page score (average of 5 components)
            overall_score = (title_score + meta_score + h1_score + url_score + links_score) / 5
            
            # Combine all fixes
            all_fixes = []
            if title_fixes:
                all_fixes.extend(title_fixes)
            if meta_fixes:
                all_fixes.extend(meta_fixes)
            if h1_fixes:
                all_fixes.extend(h1_fixes)
            if url_fixes:
                all_fixes.extend(url_fixes)
            if links_fixes:
                all_fixes.extend(links_fixes)
            
            # Prioritize fixes by impact
            prioritized_fixes = self._prioritize_fixes(all_fixes)
            
            page_scores.append({
                "url": url,
                "title": title[:60] if title else "(No Title)",
                "overall_score": round(overall_score, 1),
                "scores": {
                    "title": round(title_score, 1),
                    "meta": round(meta_score, 1),
                    "h1": round(h1_score, 1),
                    "url": round(url_score, 1),
                    "links": round(links_score, 1),
                },
                "fixes": prioritized_fixes[:5],  # Top 5 fixes
                "fix_count": len(all_fixes),
                "depth": depth,
            })
        
        # Sort by score (lowest first - these need the most attention)
        page_scores.sort(key=lambda x: x["overall_score"])
        
        logger.info(f"Individual page scores calculated for {len(page_scores)} pages")
        
        return page_scores
    
    def _calculate_title_score(
        self, url: str, title: str, title_counts: Counter
    ) -> Tuple[float, List[Dict[str, Any]]]:
        """Calculate title score with specific fixes."""
        fixes = []
        score = 100
        
        title_len = len(title.strip()) if title else 0
        
        # Missing title
        if not title or title_len == 0:
            fixes.append({
                "type": "title",
                "issue": "Missing title tag",
                "fix": "Add a descriptive title (50-60 characters)",
                "impact": "high",
                "effort": "low",
            })
            return 0, fixes
        
        # Too short
        if title_len < TITLE_MIN_LENGTH:
            fixes.append({
                "type": "title",
                "issue": f"Title too short ({title_len} chars)",
                "fix": f"Expand title to 50-60 characters. Current: '{title[:30]}...'",
                "impact": "medium",
                "effort": "low",
            })
            score = 30
        elif title_len < TITLE_OPTIMAL_MIN:
            score = 70
        
        # Too long
        if title_len > TITLE_MAX_LENGTH:
            fixes.append({
                "type": "title",
                "issue": f"Title too long ({title_len} chars)",
                "fix": f"Shorten to 50-60 characters. Will be truncated in search results.",
                "impact": "low",
                "effort": "low",
            })
            score = min(score, 60)
        elif title_len > TITLE_OPTIMAL_MAX:
            score = min(score, 85)
        
        # Duplicate
        if title_counts.get(title, 0) > 1:
            fixes.append({
                "type": "title",
                "issue": f"Duplicate title (used {title_counts[title]} times)",
                "fix": "Create a unique title that describes this specific page",
                "impact": "high",
                "effort": "low",
            })
            score = min(score, 50)
        
        # Generic title
        generic_words = ["home", "welcome", "untitled", "page", "document"]
        if any(g in title.lower() for g in generic_words) and title_len < 25:
            fixes.append({
                "type": "title",
                "issue": "Generic/non-descriptive title",
                "fix": "Use a specific, keyword-rich title describing page content",
                "impact": "medium",
                "effort": "low",
            })
            score = min(score, 60)
        
        return score, fixes
    
    def _calculate_meta_score(
        self, url: str, description: str, desc_counts: Counter
    ) -> Tuple[float, List[Dict[str, Any]]]:
        """Calculate meta description score with specific fixes."""
        fixes = []
        score = 100
        
        desc_len = len(description.strip()) if description else 0
        
        # Missing description
        if not description or desc_len == 0:
            fixes.append({
                "type": "meta",
                "issue": "Missing meta description",
                "fix": "Add a compelling description (120-160 chars) with call-to-action",
                "impact": "high",
                "effort": "low",
            })
            return 0, fixes
        
        # Too short
        if desc_len < DESCRIPTION_MIN_LENGTH:
            fixes.append({
                "type": "meta",
                "issue": f"Description too short ({desc_len} chars)",
                "fix": f"Expand to 120-160 characters with keywords and call-to-action",
                "impact": "medium",
                "effort": "low",
            })
            score = 40
        elif desc_len < DESCRIPTION_OPTIMAL_MIN:
            score = 70
        
        # Too long
        if desc_len > DESCRIPTION_MAX_LENGTH:
            fixes.append({
                "type": "meta",
                "issue": f"Description too long ({desc_len} chars)",
                "fix": "Shorten to 120-160 characters to avoid truncation",
                "impact": "low",
                "effort": "low",
            })
            score = min(score, 70)
        
        # Duplicate
        if desc_counts.get(description, 0) > 1:
            fixes.append({
                "type": "meta",
                "issue": f"Duplicate description (used {desc_counts[description]} times)",
                "fix": "Write a unique description for this specific page",
                "impact": "medium",
                "effort": "low",
            })
            score = min(score, 60)
        
        # No action words
        desc_lower = description.lower()
        has_action = any(word in desc_lower for word in ACTION_WORDS)
        if not has_action and desc_len > 50:
            fixes.append({
                "type": "meta",
                "issue": "No call-to-action in description",
                "fix": "Add action words like 'Discover', 'Learn', 'Apply', 'Explore'",
                "impact": "low",
                "effort": "low",
            })
            score = min(score, 80)
        
        return score, fixes
    
    def _calculate_h1_score(
        self, url: str, h1: str, title: str
    ) -> Tuple[float, List[Dict[str, Any]]]:
        """Calculate H1 tag score with specific fixes."""
        fixes = []
        score = 100
        
        h1_clean = h1.strip() if h1 else ""
        
        # Missing H1
        if not h1_clean:
            fixes.append({
                "type": "h1",
                "issue": "Missing H1 heading",
                "fix": "Add a descriptive H1 that matches the page topic",
                "impact": "high",
                "effort": "low",
            })
            return 0, fixes
        
        # Generic H1
        generic_h1s = ["welcome", "home", "untitled", "page"]
        if h1_clean.lower() in generic_h1s:
            fixes.append({
                "type": "h1",
                "issue": f"Generic H1: '{h1_clean}'",
                "fix": "Use a descriptive H1 with primary keyword",
                "impact": "medium",
                "effort": "low",
            })
            score = 50
        
        # H1 too short
        if len(h1_clean) < 10:
            fixes.append({
                "type": "h1",
                "issue": f"H1 too short ({len(h1_clean)} chars)",
                "fix": "Make H1 more descriptive (10-70 characters)",
                "impact": "low",
                "effort": "low",
            })
            score = min(score, 70)
        
        # H1 too long
        if len(h1_clean) > 100:
            fixes.append({
                "type": "h1",
                "issue": f"H1 too long ({len(h1_clean)} chars)",
                "fix": "Shorten H1 to under 70 characters",
                "impact": "low",
                "effort": "low",
            })
            score = min(score, 80)
        
        # Check H1 and title similarity (bonus for matching)
        if title and h1_clean:
            title_words = set(title.lower().split())
            h1_words = set(h1_clean.lower().split())
            common = title_words & h1_words
            if len(common) < 2 and len(title_words) > 3:
                fixes.append({
                    "type": "h1",
                    "issue": "H1 doesn't match page title",
                    "fix": "Align H1 with title for better SEO consistency",
                    "impact": "low",
                    "effort": "low",
                })
                score = min(score, 85)
        
        return score, fixes
    
    def _calculate_url_score_detailed(self, url: str) -> Tuple[float, List[Dict[str, Any]]]:
        """Calculate URL score with specific fixes."""
        fixes = []
        score = 100
        
        try:
            parsed = urlparse(url)
            path = parsed.path
            query = parsed.query
            url_len = len(url)
            
            # Too long
            if url_len > URL_MAX_LENGTH:
                fixes.append({
                    "type": "url",
                    "issue": f"URL too long ({url_len} chars)",
                    "fix": "Shorten URL to under 75 characters",
                    "impact": "medium",
                    "effort": "medium",
                })
                score = 50
            elif url_len > URL_OPTIMAL_MAX:
                score = 80
            
            # Has query parameters
            if query:
                from urllib.parse import parse_qs
                params = parse_qs(query)
                if len(params) > 2:
                    fixes.append({
                        "type": "url",
                        "issue": f"Too many URL parameters ({len(params)})",
                        "fix": "Use clean, static URLs without excessive parameters",
                        "impact": "medium",
                        "effort": "high",
                    })
                    score = min(score, 60)
            
            # Non-descriptive URL
            path_parts = [p for p in path.split("/") if p]
            if path_parts:
                last_part = path_parts[-1]
                if re.match(r'^(page|item|post|node|id)?\d+$', last_part, re.IGNORECASE):
                    fixes.append({
                        "type": "url",
                        "issue": "URL lacks descriptive keywords",
                        "fix": f"Replace '{last_part}' with descriptive, keyword-rich slug",
                        "impact": "medium",
                        "effort": "medium",
                    })
                    score = min(score, 70)
            
            # Has uppercase
            if any(c.isupper() for c in path):
                fixes.append({
                    "type": "url",
                    "issue": "URL contains uppercase characters",
                    "fix": "Use lowercase-only URLs for consistency",
                    "impact": "low",
                    "effort": "medium",
                })
                score = min(score, 90)
            
            # Special characters
            if re.search(r'[^\w\-/\.\?=&%]', url):
                fixes.append({
                    "type": "url",
                    "issue": "URL contains special characters",
                    "fix": "Use only letters, numbers, hyphens in URL path",
                    "impact": "low",
                    "effort": "medium",
                })
                score = min(score, 85)
            
        except Exception as e:
            fixes.append({
                "type": "url",
                "issue": f"URL parsing error: {str(e)}",
                "fix": "Review and fix URL format",
                "impact": "high",
                "effort": "medium",
            })
            score = 50
        
        return score, fixes
    
    def _calculate_links_score(
        self, url: str, inbound_count: int, outbound_count: int, depth: int
    ) -> Tuple[float, List[Dict[str, Any]]]:
        """Calculate internal linking score with specific fixes."""
        fixes = []
        score = 100
        
        # Orphan page (no inbound links, not homepage)
        if depth > 0 and inbound_count == 0:
            fixes.append({
                "type": "links",
                "issue": "Orphan page (no internal links pointing here)",
                "fix": "Add links to this page from relevant parent pages",
                "impact": "high",
                "effort": "low",
            })
            score = 30
        
        # Dead-end page (no outbound links)
        if outbound_count == 0:
            fixes.append({
                "type": "links",
                "issue": "Dead-end page (no outbound links)",
                "fix": "Add related content links or navigation elements",
                "impact": "medium",
                "effort": "low",
            })
            score = min(score, 60)
        
        # Too deep
        if depth > 3:
            fixes.append({
                "type": "links",
                "issue": f"Page too deep ({depth} clicks from homepage)",
                "fix": "Add shortcut links from higher-level pages",
                "impact": "medium",
                "effort": "medium",
            })
            score = min(score, 70)
        
        # Low outbound links (for non-leaf pages)
        if depth < 2 and outbound_count < 3:
            fixes.append({
                "type": "links",
                "issue": f"Few outbound links ({outbound_count}) for a high-level page",
                "fix": "Add more internal links to distribute link equity",
                "impact": "low",
                "effort": "low",
            })
            score = min(score, 80)
        
        return score, fixes
    
    def _prioritize_fixes(self, fixes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prioritize fixes by impact and effort."""
        # Sort by impact (high first) then by effort (low first)
        impact_order = {"high": 0, "medium": 1, "low": 2}
        effort_order = {"low": 0, "medium": 1, "high": 2}
        
        return sorted(
            fixes,
            key=lambda x: (
                impact_order.get(x.get("impact", "low"), 2),
                effort_order.get(x.get("effort", "high"), 2),
            )
        )
    
    # -----------------------------------------------------------------------
    # Competitor SEO Analysis
    # -----------------------------------------------------------------------
    
    def competitor_seo_analysis(
        self, competitor_domains: List[str], max_pages: int = 50
    ) -> Dict[str, Any]:
        """
        Compare SEO metrics with competitor websites.
        
        Args:
            competitor_domains: List of competitor domain URLs to analyze.
            max_pages: Maximum pages to crawl per competitor (default 50).
        
        Returns:
            Dictionary containing comparison matrix, gap analysis, and opportunities.
        """
        logger.info(f"Starting competitor SEO analysis for {len(competitor_domains)} competitors...")
        
        # Our metrics (ensure we have them)
        self.calculate_overall_seo_score()
        
        our_metrics = {
            "domain": self._extract_domain_from_data(),
            "seo_score": self.overall_score,
            "total_pages": len(self.df),
            "metadata_score": self.metadata_analysis.get("overall_metadata_score", 0),
            "url_score": self.url_analysis.get("url_structure_score", 0),
            "linking_score": self.linking_analysis.get("linking_score", 0),
            "keyword_score": self.keyword_analysis.get("keyword_consistency_score", 0),
            "top_keywords": [kw for kw, _ in self.keyword_analysis.get("top_keywords", [])[:10]],
            "avg_depth": self.df["depth"].mean() if "depth" in self.df.columns else 0,
            "orphan_pages": self.linking_analysis.get("orphan_pages", 0),
            "dead_ends": self.linking_analysis.get("dead_ends", 0),
        }
        
        competitor_metrics = []
        
        for domain in competitor_domains:
            try:
                metrics = self._analyze_competitor(domain, max_pages)
                competitor_metrics.append(metrics)
            except Exception as e:
                logger.warning(f"Failed to analyze competitor {domain}: {e}")
                competitor_metrics.append({
                    "domain": domain,
                    "error": str(e),
                    "seo_score": 0,
                })
        
        # Generate comparison matrix
        comparison_matrix = self._generate_comparison_matrix(our_metrics, competitor_metrics)
        
        # Gap analysis
        gap_analysis = self._perform_gap_analysis(our_metrics, competitor_metrics)
        
        # Opportunities
        opportunities = self._identify_opportunities(our_metrics, competitor_metrics, gap_analysis)
        
        result = {
            "our_metrics": our_metrics,
            "competitor_metrics": competitor_metrics,
            "comparison_matrix": comparison_matrix,
            "gap_analysis": gap_analysis,
            "opportunities": opportunities,
            "summary": self._generate_competitor_summary(our_metrics, competitor_metrics),
        }
        
        logger.info("Competitor SEO analysis complete")
        
        return result
    
    def _extract_domain_from_data(self) -> str:
        """Extract domain from crawled data."""
        if len(self.df) > 0:
            first_url = self.df.iloc[0]["url"]
            parsed = urlparse(first_url)
            return parsed.netloc
        return "unknown"
    
    def _analyze_competitor(self, domain: str, max_pages: int) -> Dict[str, Any]:
        """
        Analyze a competitor website.
        
        Note: This performs a lightweight analysis based on accessible data.
        Full crawling would require the crawler module.
        """
        import requests
        from bs4 import BeautifulSoup
        
        logger.info(f"Analyzing competitor: {domain}")
        
        # Normalize domain URL
        if not domain.startswith(("http://", "https://")):
            domain = "https://" + domain
        
        metrics = {
            "domain": urlparse(domain).netloc,
            "url": domain,
            "seo_score": 0,
            "total_pages_analyzed": 0,
            "metadata_score": 0,
            "url_score": 0,
            "linking_score": 0,
            "keyword_score": 0,
            "top_keywords": [],
            "avg_depth": 0,
            "technical_seo": {},
        }
        
        try:
            # Fetch homepage
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            response = requests.get(domain, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "lxml")
            
            # Analyze homepage
            homepage_analysis = self._analyze_competitor_page(soup, domain)
            
            # Extract links for further analysis
            internal_links = []
            for link in soup.find_all("a", href=True):
                href = link["href"]
                if href.startswith("/") or urlparse(href).netloc == metrics["domain"]:
                    if href.startswith("/"):
                        href = domain.rstrip("/") + href
                    internal_links.append(href)
            
            # Analyze sample of internal pages (up to max_pages)
            pages_analyzed = [homepage_analysis]
            unique_links = list(set(internal_links))[:max_pages - 1]
            
            for link in unique_links[:10]:  # Limit to 10 additional pages for speed
                try:
                    page_response = requests.get(link, headers=headers, timeout=5)
                    if page_response.status_code == 200:
                        page_soup = BeautifulSoup(page_response.text, "lxml")
                        page_analysis = self._analyze_competitor_page(page_soup, link)
                        pages_analyzed.append(page_analysis)
                except Exception:
                    continue
            
            # Aggregate metrics
            metrics["total_pages_analyzed"] = len(pages_analyzed)
            
            if pages_analyzed:
                # Calculate average scores
                metrics["metadata_score"] = statistics.mean(
                    [p.get("metadata_score", 0) for p in pages_analyzed]
                )
                metrics["url_score"] = statistics.mean(
                    [p.get("url_score", 0) for p in pages_analyzed]
                )
                
                # Extract keywords
                all_keywords = []
                for p in pages_analyzed:
                    all_keywords.extend(p.get("keywords", []))
                keyword_counts = Counter(all_keywords)
                metrics["top_keywords"] = [kw for kw, _ in keyword_counts.most_common(10)]
                
                # Estimate linking score based on internal links
                avg_links = len(internal_links) / len(pages_analyzed) if pages_analyzed else 0
                metrics["linking_score"] = min(100, avg_links * 5)  # Rough estimate
                
                # Keyword consistency
                metrics["keyword_score"] = 50  # Default middle score without full analysis
                
                # Calculate overall SEO score
                metrics["seo_score"] = (
                    metrics["metadata_score"] * 0.3 +
                    metrics["url_score"] * 0.2 +
                    metrics["linking_score"] * 0.3 +
                    metrics["keyword_score"] * 0.2
                )
            
            # Technical SEO indicators
            metrics["technical_seo"] = {
                "has_ssl": domain.startswith("https://"),
                "has_sitemap": self._check_sitemap(domain),
                "has_robots": self._check_robots(domain),
                "mobile_friendly": self._check_mobile_meta(soup),
                "page_speed_estimate": self._estimate_page_speed(response),
            }
            
        except requests.RequestException as e:
            logger.warning(f"Request failed for {domain}: {e}")
            metrics["error"] = str(e)
        except Exception as e:
            logger.warning(f"Analysis failed for {domain}: {e}")
            metrics["error"] = str(e)
        
        return metrics
    
    def _analyze_competitor_page(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Analyze a single competitor page."""
        from bs4 import BeautifulSoup
        
        # Title analysis
        title_tag = soup.find("title")
        title = title_tag.get_text().strip() if title_tag else ""
        title_len = len(title)
        
        if not title:
            title_score = 0
        elif TITLE_OPTIMAL_MIN <= title_len <= TITLE_OPTIMAL_MAX:
            title_score = 100
        elif TITLE_MIN_LENGTH <= title_len <= TITLE_MAX_LENGTH:
            title_score = 75
        else:
            title_score = 50
        
        # Meta description
        meta_desc = soup.find("meta", attrs={"name": "description"})
        description = meta_desc.get("content", "").strip() if meta_desc else ""
        desc_len = len(description)
        
        if not description:
            desc_score = 0
        elif DESCRIPTION_OPTIMAL_MIN <= desc_len <= DESCRIPTION_OPTIMAL_MAX:
            desc_score = 100
        elif DESCRIPTION_MIN_LENGTH <= desc_len <= DESCRIPTION_MAX_LENGTH:
            desc_score = 75
        else:
            desc_score = 50
        
        # H1 analysis
        h1_tags = soup.find_all("h1")
        h1_score = 100 if len(h1_tags) == 1 else (70 if len(h1_tags) > 1 else 0)
        
        # URL analysis
        url_len = len(url)
        if url_len <= URL_OPTIMAL_MAX:
            url_score = 100
        elif url_len <= URL_MAX_LENGTH:
            url_score = 75
        else:
            url_score = 50
        
        # Extract keywords
        text_content = soup.get_text()
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text_content.lower())
        keywords = [w for w in words if w not in STOP_WORDS][:50]
        
        return {
            "url": url,
            "title": title,
            "description": description,
            "metadata_score": (title_score + desc_score + h1_score) / 3,
            "url_score": url_score,
            "keywords": keywords,
        }
    
    def _check_sitemap(self, domain: str) -> bool:
        """Check if sitemap.xml exists."""
        try:
            import requests
            sitemap_url = domain.rstrip("/") + "/sitemap.xml"
            response = requests.head(sitemap_url, timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def _check_robots(self, domain: str) -> bool:
        """Check if robots.txt exists."""
        try:
            import requests
            robots_url = domain.rstrip("/") + "/robots.txt"
            response = requests.head(robots_url, timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def _check_mobile_meta(self, soup) -> bool:
        """Check for mobile-friendly viewport meta tag."""
        viewport = soup.find("meta", attrs={"name": "viewport"})
        return viewport is not None
    
    def _estimate_page_speed(self, response) -> str:
        """Estimate page speed based on response size and time."""
        try:
            size_kb = len(response.content) / 1024
            elapsed = response.elapsed.total_seconds()
            
            if elapsed < 1 and size_kb < 500:
                return "fast"
            elif elapsed < 2 and size_kb < 1000:
                return "average"
            else:
                return "slow"
        except Exception:
            return "unknown"
    
    def _generate_comparison_matrix(
        self, our_metrics: Dict, competitor_metrics: List[Dict]
    ) -> Dict[str, Any]:
        """Generate a comparison matrix of all metrics."""
        all_domains = [our_metrics] + competitor_metrics
        
        metrics_to_compare = [
            ("seo_score", "SEO Score", True),  # True = higher is better
            ("metadata_score", "Metadata Score", True),
            ("url_score", "URL Structure", True),
            ("linking_score", "Internal Linking", True),
            ("keyword_score", "Keyword Optimization", True),
            ("total_pages", "Total Pages", None),  # None = informational
            ("orphan_pages", "Orphan Pages", False),  # False = lower is better
            ("dead_ends", "Dead Ends", False),
        ]
        
        matrix = {
            "headers": ["Metric"] + [d.get("domain", "Unknown") for d in all_domains],
            "rows": [],
            "our_rank": {},
        }
        
        for metric_key, metric_name, higher_is_better in metrics_to_compare:
            row = [metric_name]
            values = []
            
            for d in all_domains:
                value = d.get(metric_key, 0)
                if isinstance(value, float):
                    value = round(value, 1)
                row.append(value)
                values.append(value)
            
            # Calculate our rank
            if higher_is_better is not None and len(values) > 1:
                our_value = values[0]
                if higher_is_better:
                    rank = sum(1 for v in values if v > our_value) + 1
                else:
                    rank = sum(1 for v in values if v < our_value) + 1
                matrix["our_rank"][metric_key] = rank
            
            matrix["rows"].append(row)
        
        return matrix
    
    def _perform_gap_analysis(
        self, our_metrics: Dict, competitor_metrics: List[Dict]
    ) -> Dict[str, Any]:
        """Perform gap analysis to identify where we're behind."""
        gaps = {
            "keywords": [],
            "technical": [],
            "content": [],
            "structure": [],
        }
        
        # Keyword gaps
        our_keywords = set(our_metrics.get("top_keywords", []))
        for comp in competitor_metrics:
            comp_keywords = set(comp.get("top_keywords", []))
            missing = comp_keywords - our_keywords
            if missing:
                gaps["keywords"].append({
                    "competitor": comp.get("domain"),
                    "missing_keywords": list(missing)[:10],
                    "recommendation": f"Consider targeting: {', '.join(list(missing)[:5])}",
                })
        
        # Score gaps
        for comp in competitor_metrics:
            if comp.get("seo_score", 0) > our_metrics.get("seo_score", 0):
                gap_amount = comp["seo_score"] - our_metrics["seo_score"]
                gaps["content"].append({
                    "competitor": comp.get("domain"),
                    "their_score": round(comp["seo_score"], 1),
                    "our_score": round(our_metrics["seo_score"], 1),
                    "gap": round(gap_amount, 1),
                    "recommendation": f"Close {gap_amount:.1f} point gap by improving metadata and keywords",
                })
        
        # Technical gaps
        for comp in competitor_metrics:
            tech = comp.get("technical_seo", {})
            our_tech = {
                "has_ssl": True,  # Assume we have SSL
                "has_sitemap": True,
                "has_robots": True,
            }
            
            if tech.get("has_sitemap") and not our_tech.get("has_sitemap"):
                gaps["technical"].append({
                    "competitor": comp.get("domain"),
                    "feature": "Sitemap",
                    "recommendation": "Add sitemap.xml for better crawling",
                })
            
            if tech.get("page_speed_estimate") == "fast" and comp.get("seo_score", 0) > our_metrics.get("seo_score", 0):
                gaps["technical"].append({
                    "competitor": comp.get("domain"),
                    "feature": "Page Speed",
                    "recommendation": "Optimize page load speed for better rankings",
                })
        
        # Structure gaps
        our_depth = our_metrics.get("avg_depth", 0)
        for comp in competitor_metrics:
            comp_depth = comp.get("avg_depth", 0)
            if comp_depth > 0 and comp_depth < our_depth - 0.5:
                gaps["structure"].append({
                    "competitor": comp.get("domain"),
                    "their_depth": round(comp_depth, 1),
                    "our_depth": round(our_depth, 1),
                    "recommendation": "Flatten site structure for better accessibility",
                })
        
        return gaps
    
    def _identify_opportunities(
        self, our_metrics: Dict, competitor_metrics: List[Dict], gaps: Dict
    ) -> List[Dict[str, Any]]:
        """Identify SEO opportunities based on competitor analysis."""
        opportunities = []
        
        # High-value keyword opportunities
        all_competitor_keywords = set()
        for comp in competitor_metrics:
            all_competitor_keywords.update(comp.get("top_keywords", []))
        
        our_keywords = set(our_metrics.get("top_keywords", []))
        keyword_opportunities = all_competitor_keywords - our_keywords
        
        if keyword_opportunities:
            opportunities.append({
                "type": "keywords",
                "priority": "high",
                "title": f"Target {len(keyword_opportunities)} untapped keywords",
                "description": f"Keywords competitors rank for: {', '.join(list(keyword_opportunities)[:5])}",
                "impact": "High - can drive significant organic traffic",
                "effort": "Medium - requires content creation/optimization",
                "keywords": list(keyword_opportunities)[:20],
            })
        
        # Content gap opportunities
        if gaps.get("content"):
            best_competitor = max(
                competitor_metrics,
                key=lambda x: x.get("seo_score", 0),
                default=None
            )
            if best_competitor:
                opportunities.append({
                    "type": "content",
                    "priority": "high",
                    "title": f"Match {best_competitor.get('domain')}'s SEO score",
                    "description": f"They score {best_competitor.get('seo_score', 0):.1f} vs our {our_metrics.get('seo_score', 0):.1f}",
                    "impact": "High - improved rankings across the board",
                    "effort": "Medium - systematic optimization required",
                    "actions": [
                        "Improve title tags and meta descriptions",
                        "Enhance keyword consistency",
                        "Add missing H1 tags",
                    ],
                })
        
        # Technical opportunities
        if any(comp.get("technical_seo", {}).get("has_sitemap") for comp in competitor_metrics):
            opportunities.append({
                "type": "technical",
                "priority": "medium",
                "title": "Implement comprehensive sitemap",
                "description": "Ensure XML sitemap is present and submitted to search engines",
                "impact": "Medium - better crawling and indexing",
                "effort": "Low - one-time setup",
            })
        
        # Quick wins
        if our_metrics.get("metadata_score", 0) < 70:
            opportunities.append({
                "type": "quick_win",
                "priority": "high",
                "title": "Fix metadata issues",
                "description": f"Metadata score is {our_metrics.get('metadata_score', 0):.1f}/100",
                "impact": "High - immediate ranking improvements",
                "effort": "Low - bulk update titles and descriptions",
                "actions": [
                    "Add missing meta descriptions",
                    "Fix duplicate titles",
                    "Optimize title lengths",
                ],
            })
        
        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        opportunities.sort(key=lambda x: priority_order.get(x.get("priority", "low"), 2))
        
        return opportunities
    
    def _generate_competitor_summary(
        self, our_metrics: Dict, competitor_metrics: List[Dict]
    ) -> Dict[str, Any]:
        """Generate a summary of the competitor analysis."""
        valid_competitors = [c for c in competitor_metrics if "error" not in c]
        
        if not valid_competitors:
            return {
                "status": "No competitors could be analyzed",
                "our_position": "Unknown",
            }
        
        # Calculate our position
        all_scores = [our_metrics.get("seo_score", 0)] + [
            c.get("seo_score", 0) for c in valid_competitors
        ]
        all_scores.sort(reverse=True)
        our_rank = all_scores.index(our_metrics.get("seo_score", 0)) + 1
        
        avg_competitor_score = statistics.mean(
            [c.get("seo_score", 0) for c in valid_competitors]
        )
        
        if our_metrics.get("seo_score", 0) > avg_competitor_score:
            position = "Above Average"
            status = "good"
        elif our_metrics.get("seo_score", 0) > avg_competitor_score - 10:
            position = "Average"
            status = "moderate"
        else:
            position = "Below Average"
            status = "needs_improvement"
        
        return {
            "competitors_analyzed": len(valid_competitors),
            "our_seo_score": round(our_metrics.get("seo_score", 0), 1),
            "avg_competitor_score": round(avg_competitor_score, 1),
            "our_rank": f"{our_rank} of {len(all_scores)}",
            "our_position": position,
            "status": status,
            "key_insight": self._get_key_insight(our_metrics, valid_competitors),
        }
    
    def _get_key_insight(self, our_metrics: Dict, competitors: List[Dict]) -> str:
        """Generate a key insight from the analysis."""
        our_score = our_metrics.get("seo_score", 0)
        best_competitor = max(competitors, key=lambda x: x.get("seo_score", 0), default=None)
        
        if not best_competitor:
            return "Unable to generate insights - no competitor data available."
        
        best_score = best_competitor.get("seo_score", 0)
        gap = best_score - our_score
        
        if gap <= 0:
            return f"Congratulations! You're leading in SEO with a score of {our_score:.1f}/100."
        elif gap < 10:
            return f"You're close! Just {gap:.1f} points behind {best_competitor.get('domain')}. Focus on metadata optimization."
        elif gap < 20:
            return f"Room for improvement: {gap:.1f} point gap with {best_competitor.get('domain')}. Prioritize quick wins."
        else:
            return f"Significant opportunity: Closing the {gap:.1f} point gap could boost organic traffic by 30-50%."
    
    # -----------------------------------------------------------------------
    # Overall Score Calculation
    # -----------------------------------------------------------------------
    
    def calculate_overall_seo_score(self) -> float:
        """
        Calculate comprehensive SEO score.
        
        Formula:
        - Metadata score: 30% weight
        - URL structure score: 20% weight
        - Internal linking score: 30% weight
        - Keyword analysis score: 20% weight
        
        Returns:
            Overall SEO score (0-100).
        """
        # Ensure all analyses are run
        if not self.metadata_analysis:
            self.analyze_page_metadata()
        if not self.url_analysis:
            self.analyze_url_structure()
        if not self.linking_analysis:
            self.analyze_internal_linking()
        if not self.keyword_analysis:
            self.analyze_keyword_presence()
        
        # Get individual scores
        metadata_score = self.metadata_analysis.get("overall_metadata_score", 0)
        url_score = self.url_analysis.get("url_structure_score", 0)
        linking_score = self.linking_analysis.get("linking_score", 0)
        keyword_score = self.keyword_analysis.get("keyword_consistency_score", 0)
        
        # Calculate weighted average
        self.overall_score = (
            metadata_score * 0.30 +
            url_score * 0.20 +
            linking_score * 0.30 +
            keyword_score * 0.20
        )
        
        logger.info(f"Overall SEO Score: {self.overall_score:.1f}/100")
        
        return round(self.overall_score, 1)
    
    def get_score_interpretation(self) -> Dict[str, Any]:
        """Get interpretation of the overall SEO score."""
        score = self.overall_score
        
        if score >= 80:
            grade = "A"
            status = "Excellent"
            description = "Your website has strong SEO foundations. Focus on maintaining and fine-tuning."
        elif score >= 60:
            grade = "B"
            status = "Good"
            description = "Good SEO with room for improvement. Address the identified issues for better results."
        elif score >= 40:
            grade = "C"
            status = "Needs Improvement"
            description = "Several SEO issues need attention. Prioritize critical fixes for quick wins."
        else:
            grade = "D"
            status = "Critical"
            description = "Significant SEO problems detected. Immediate action required."
        
        return {
            "score": round(score, 1),
            "grade": grade,
            "status": status,
            "description": description,
        }
    
    # -----------------------------------------------------------------------
    # Priority Recommendations
    # -----------------------------------------------------------------------
    
    def generate_priority_recommendations(self) -> List[Dict[str, Any]]:
        """
        Generate prioritized action plan based on impact and effort.
        
        Returns:
            List of prioritized recommendations.
        """
        recommendations = []
        
        # Ensure analyses are run
        if not self.metadata_analysis:
            self.analyze_page_metadata()
        if not self.url_analysis:
            self.analyze_url_structure()
        if not self.linking_analysis:
            self.analyze_internal_linking()
        if not self.keyword_analysis:
            self.analyze_keyword_presence()
        
        # Priority 1: Critical - High Impact, Low Effort
        missing_titles = self.metadata_analysis.get("title_analysis", {}).get("missing_count", 0)
        if missing_titles > 0:
            recommendations.append({
                "priority": 1,
                "category": "Critical",
                "action": f"Add title tags to {missing_titles} pages",
                "impact": "High (+15% search visibility)",
                "effort": f"{missing_titles * 5} minutes",
                "difficulty": "Easy",
                "steps": [
                    "Identify pages without titles",
                    "Write unique, descriptive titles (50-60 chars)",
                    "Include primary keyword in each title",
                    "Update CMS or HTML files",
                ],
            })
        
        missing_descriptions = self.metadata_analysis.get("description_analysis", {}).get("missing_count", 0)
        if missing_descriptions > 0:
            recommendations.append({
                "priority": 1,
                "category": "Critical",
                "action": f"Add meta descriptions to {missing_descriptions} pages",
                "impact": "High (+10% click-through rate)",
                "effort": f"{missing_descriptions * 3} minutes",
                "difficulty": "Easy",
                "steps": [
                    "Identify pages without descriptions",
                    "Write compelling descriptions (120-160 chars)",
                    "Include call-to-action words",
                    "Add primary keyword naturally",
                ],
            })
        
        # Priority 2: High Impact, Medium Effort
        orphan_pages = self.linking_analysis.get("orphan_pages", 0)
        if orphan_pages > 0:
            recommendations.append({
                "priority": 2,
                "category": "High",
                "action": f"Link {orphan_pages} orphan pages",
                "impact": "High (+{} pages indexed)".format(orphan_pages),
                "effort": f"{orphan_pages * 2} minutes",
                "difficulty": "Easy",
                "steps": [
                    "Review orphan pages list",
                    "Identify relevant parent pages",
                    "Add contextual links to orphan pages",
                    "Verify links work correctly",
                ],
            })
        
        dead_ends = self.linking_analysis.get("dead_ends", 0)
        if dead_ends > 5:
            recommendations.append({
                "priority": 2,
                "category": "High",
                "action": f"Add navigation to {dead_ends} dead-end pages",
                "impact": "Medium (+5% user engagement)",
                "effort": f"{dead_ends * 3} minutes",
                "difficulty": "Easy",
                "steps": [
                    "Identify dead-end pages",
                    "Add 'Related Content' sections",
                    "Include breadcrumb navigation",
                    "Add footer links to main sections",
                ],
            })
        
        # Priority 3: Medium Impact, Low Effort
        duplicate_titles = self.metadata_analysis.get("title_analysis", {}).get("duplicate_count", 0)
        if duplicate_titles > 0:
            recommendations.append({
                "priority": 3,
                "category": "Medium",
                "action": f"Fix {duplicate_titles} duplicate titles",
                "impact": "Medium (avoid duplicate content penalty)",
                "effort": f"{duplicate_titles * 5} minutes",
                "difficulty": "Easy",
                "steps": [
                    "Identify duplicate titles",
                    "Create unique titles for each page",
                    "Ensure titles reflect page content",
                ],
            })
        
        # Priority 4: Long-term improvements
        deep_pages = self.linking_analysis.get("pages_too_deep", 0)
        if deep_pages > 0:
            recommendations.append({
                "priority": 4,
                "category": "Long-term",
                "action": f"Restructure {deep_pages} deep pages",
                "impact": "High (+20% crawl efficiency)",
                "effort": "2-4 hours",
                "difficulty": "Medium",
                "steps": [
                    "Analyze current site structure",
                    "Plan flatter hierarchy",
                    "Implement redirects if needed",
                    "Update internal links",
                    "Test navigation paths",
                ],
            })
        
        long_urls = self.url_analysis.get("pages_with_long_urls", 0)
        if long_urls > 5:
            recommendations.append({
                "priority": 4,
                "category": "Long-term",
                "action": f"Optimize {long_urls} long URLs",
                "impact": "Medium (cleaner URLs, better UX)",
                "effort": "4-8 hours",
                "difficulty": "Medium",
                "steps": [
                    "Identify URLs over 75 characters",
                    "Create shorter, keyword-rich URLs",
                    "Set up 301 redirects",
                    "Update all internal links",
                ],
            })
        
        # Sort by priority
        recommendations.sort(key=lambda x: x["priority"])
        
        self.recommendations = recommendations
        
        return recommendations
    
    # -----------------------------------------------------------------------
    # Report Generation
    # -----------------------------------------------------------------------
    
    def generate_seo_report(
        self, output_file: str = "output/SEO_Analysis_Report.txt"
    ) -> str:
        """
        Generate comprehensive SEO audit report.
        
        Args:
            output_file: Path to save the report.
            
        Returns:
            Path to the generated report.
        """
        # Ensure all analyses are run
        self.calculate_overall_seo_score()
        self.generate_priority_recommendations()
        
        interpretation = self.get_score_interpretation()
        
        report_lines = [
            "═" * 70,
            "SEO ANALYSIS REPORT",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Website: {self.csv_file_path.name}",
            "═" * 70,
            "",
            "1. EXECUTIVE SUMMARY",
            "─" * 50,
            f"   Overall SEO Score: {interpretation['score']}/100",
            f"   Grade: {interpretation['grade']}",
            f"   Status: {interpretation['status']}",
            f"   {interpretation['description']}",
            "",
            "   Quick Findings:",
            f"   • Pages analyzed: {len(self.df)}",
            f"   • Pages with title issues: {self.metadata_analysis.get('pages_with_title_issues', 0)}",
            f"   • Pages with description issues: {self.metadata_analysis.get('pages_with_description_issues', 0)}",
            f"   • Orphan pages: {self.linking_analysis.get('orphan_pages', 0)}",
            f"   • Dead-end pages: {self.linking_analysis.get('dead_ends', 0)}",
            "",
            "   Estimated Traffic Potential: +25-40% with recommended fixes",
            "   Timeline to see results: 4-8 weeks",
            "",
            "2. DETAILED SCORING BREAKDOWN",
            "─" * 50,
            f"   Metadata Score:      {self.metadata_analysis.get('overall_metadata_score', 0)}/100 (30% weight)",
            f"   URL Structure Score: {self.url_analysis.get('url_structure_score', 0)}/100 (20% weight)",
            f"   Internal Linking:    {self.linking_analysis.get('linking_score', 0)}/100 (30% weight)",
            f"   Keyword Analysis:    {self.keyword_analysis.get('keyword_consistency_score', 0)}/100 (20% weight)",
            "",
            "3. METADATA ANALYSIS",
            "─" * 50,
            "",
            "   3.1 Title Tags",
            f"       Pages analyzed: {len(self.df)}",
            f"       Optimal length (50-60 chars): {self.metadata_analysis.get('title_analysis', {}).get('optimal_count', 0)} pages",
            f"       Missing titles: {self.metadata_analysis.get('title_analysis', {}).get('missing_count', 0)} pages",
            f"       Too short (<50): {self.metadata_analysis.get('title_analysis', {}).get('too_short_count', 0)} pages",
            f"       Too long (>60): {self.metadata_analysis.get('title_analysis', {}).get('too_long_count', 0)} pages",
            f"       Duplicates: {self.metadata_analysis.get('title_analysis', {}).get('duplicate_count', 0)} pages",
            "",
            "   3.2 Meta Descriptions",
            f"       Optimal length (120-160 chars): {self.metadata_analysis.get('description_analysis', {}).get('optimal_count', 0)} pages",
            f"       Missing: {self.metadata_analysis.get('description_analysis', {}).get('missing_count', 0)} pages",
            f"       Too short: {self.metadata_analysis.get('description_analysis', {}).get('too_short_count', 0)} pages",
            f"       Too long: {self.metadata_analysis.get('description_analysis', {}).get('too_long_count', 0)} pages",
            "",
            "   3.3 H1 Tags",
            f"       Missing H1: {self.metadata_analysis.get('h1_analysis', {}).get('missing_count', 0)} pages",
            "",
            "4. URL STRUCTURE ANALYSIS",
            "─" * 50,
            f"   Score: {self.url_analysis.get('url_structure_score', 0)}/100",
            f"   Long URLs (>75 chars): {self.url_analysis.get('pages_with_long_urls', 0)} pages",
            f"   URLs with parameters: {self.url_analysis.get('pages_with_parameters', 0)} pages",
            f"   Poor keyword URLs: {self.url_analysis.get('pages_with_poor_keywords', 0)} pages",
            "",
            "5. INTERNAL LINKING ANALYSIS",
            "─" * 50,
            f"   Score: {self.linking_analysis.get('linking_score', 0)}/100",
            f"   Orphan pages: {self.linking_analysis.get('orphan_pages', 0)}",
            f"   Dead-end pages: {self.linking_analysis.get('dead_ends', 0)}",
            f"   Pages too deep (>3 clicks): {self.linking_analysis.get('pages_too_deep', 0)}",
            f"   Average links per page: {self.linking_analysis.get('average_links_per_page', 0)}",
            "",
            "6. KEYWORD ANALYSIS",
            "─" * 50,
            f"   Keyword consistency score: {self.keyword_analysis.get('keyword_consistency_score', 0)}/100",
            f"   Pages with low keyword presence: {self.keyword_analysis.get('pages_missing_keywords', 0)}",
            "",
            "   Top Keywords Found:",
        ]
        
        for keyword, count in self.keyword_analysis.get("top_keywords", [])[:10]:
            report_lines.append(f"   • {keyword}: {count} occurrences")
        
        report_lines.extend([
            "",
            "7. PRIORITY RECOMMENDATIONS",
            "─" * 50,
        ])
        
        for rec in self.recommendations:
            report_lines.extend([
                "",
                f"   [{rec['category'].upper()}] {rec['action']}",
                f"   Impact: {rec['impact']}",
                f"   Effort: {rec['effort']}",
                f"   Difficulty: {rec['difficulty']}",
                "   Steps:",
            ])
            for step in rec.get("steps", []):
                report_lines.append(f"      • {step}")
        
        report_lines.extend([
            "",
            "8. QUICK WINS (1-2 hour tasks)",
            "─" * 50,
            "   Complete these for immediate improvement:",
        ])
        
        quick_wins = [r for r in self.recommendations if r["priority"] <= 2]
        total_time = 0
        for rec in quick_wins[:5]:
            report_lines.append(f"   • {rec['action']} → {rec['impact']}")
        
        report_lines.extend([
            "",
            "   Expected result: +15-25% organic traffic potential",
            "",
            "9. IMPLEMENTATION ROADMAP",
            "─" * 50,
            "",
            "   Week 1: Quick Wins",
            "   ├─ Fix missing titles and descriptions",
            "   ├─ Link orphan pages",
            "   └─ Fix broken internal links",
            "",
            "   Week 2-3: Medium Tasks",
            "   ├─ Optimize keyword consistency",
            "   ├─ Improve URL structure",
            "   └─ Add related content sections",
            "",
            "   Month 2+: Long-term",
            "   ├─ Restructure deep pages",
            "   ├─ Content optimization",
            "   └─ Ongoing monitoring",
            "",
            "10. MONITORING & MAINTENANCE",
            "─" * 50,
            "   • Run SEO audit monthly",
            "   • Track keyword rankings weekly",
            "   • Monitor traffic changes in Google Analytics",
            "   • Update content based on search trends",
            "",
            "═" * 70,
            "End of Report",
            "═" * 70,
        ])
        
        report = "\n".join(report_lines)
        
        # Save report
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report)
        
        logger.info(f"SEO report saved to {output_path}")
        
        return str(output_path)
    
    # -----------------------------------------------------------------------
    # Dashboard Data Generation
    # -----------------------------------------------------------------------
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Generate data for dashboard visualization.
        
        Returns:
            Dictionary with all metrics for dashboard charts.
        """
        # Ensure all analyses are run
        self.calculate_overall_seo_score()
        self.generate_priority_recommendations()
        
        interpretation = self.get_score_interpretation()
        
        return {
            "overall_score": interpretation["score"],
            "grade": interpretation["grade"],
            "status": interpretation["status"],
            "description": interpretation["description"],
            "scores": {
                "metadata": self.metadata_analysis.get("overall_metadata_score", 0),
                "url_structure": self.url_analysis.get("url_structure_score", 0),
                "internal_linking": self.linking_analysis.get("linking_score", 0),
                "keywords": self.keyword_analysis.get("keyword_consistency_score", 0),
            },
            "issues": {
                "missing_titles": self.metadata_analysis.get("title_analysis", {}).get("missing_count", 0),
                "missing_descriptions": self.metadata_analysis.get("description_analysis", {}).get("missing_count", 0),
                "duplicate_titles": self.metadata_analysis.get("title_analysis", {}).get("duplicate_count", 0),
                "duplicate_descriptions": self.metadata_analysis.get("description_analysis", {}).get("duplicate_count", 0),
                "missing_h1": self.metadata_analysis.get("h1_analysis", {}).get("missing_count", 0),
                "long_urls": self.url_analysis.get("pages_with_long_urls", 0),
                "parameter_urls": self.url_analysis.get("pages_with_parameters", 0),
                "orphan_pages": self.linking_analysis.get("orphan_pages", 0),
                "dead_ends": self.linking_analysis.get("dead_ends", 0),
                "pages_too_deep": self.linking_analysis.get("pages_too_deep", 0),
                "low_keyword_pages": self.keyword_analysis.get("pages_missing_keywords", 0),
            },
            "metrics": {
                "total_pages": len(self.df),
                "avg_links_per_page": self.linking_analysis.get("average_links_per_page", 0),
                "top_keywords": self.keyword_analysis.get("top_keywords", [])[:10],
            },
            "priority_actions": [
                {
                    "priority": rec["priority"],
                    "category": rec["category"],
                    "action": rec["action"],
                    "impact": rec["impact"],
                    "effort": rec["effort"],
                }
                for rec in self.recommendations[:5]
            ],
            "chart_data": {
                "score_breakdown": {
                    "labels": ["Metadata", "URL Structure", "Internal Linking", "Keywords"],
                    "values": [
                        self.metadata_analysis.get("overall_metadata_score", 0),
                        self.url_analysis.get("url_structure_score", 0),
                        self.linking_analysis.get("linking_score", 0),
                        self.keyword_analysis.get("keyword_consistency_score", 0),
                    ],
                },
                "issues_breakdown": {
                    "labels": [
                        "Missing Titles",
                        "Missing Descriptions",
                        "Orphan Pages",
                        "Dead Ends",
                        "Deep Pages",
                    ],
                    "values": [
                        self.metadata_analysis.get("title_analysis", {}).get("missing_count", 0),
                        self.metadata_analysis.get("description_analysis", {}).get("missing_count", 0),
                        self.linking_analysis.get("orphan_pages", 0),
                        self.linking_analysis.get("dead_ends", 0),
                        self.linking_analysis.get("pages_too_deep", 0),
                    ],
                },
            },
            "estimated_traffic_boost": self._estimate_traffic_boost(),
        }
    
    def _estimate_traffic_boost(self) -> str:
        """Estimate potential traffic boost from fixing issues."""
        score = self.overall_score
        
        if score >= 80:
            return "5-10%"
        elif score >= 60:
            return "15-25%"
        elif score >= 40:
            return "25-40%"
        else:
            return "40-60%"


# ---------------------------------------------------------------------------
# Standalone Function for Dashboard
# ---------------------------------------------------------------------------

def generate_seo_dashboard_data(csv_file: str) -> Dict[str, Any]:
    """
    Generate SEO data for dashboard visualization.
    
    Args:
        csv_file: Path to the CSV file containing crawled data.
        
    Returns:
        Dictionary with all metrics for Plotly charts.
    """
    try:
        analyzer = SEOAnalyzer(csv_file)
        return analyzer.get_dashboard_data()
    except Exception as e:
        logger.error(f"Error generating SEO dashboard data: {e}")
        return {
            "overall_score": 0,
            "grade": "N/A",
            "status": "Error",
            "description": f"Could not analyze SEO: {str(e)}",
            "scores": {},
            "issues": {},
            "metrics": {},
            "priority_actions": [],
            "chart_data": {},
            "estimated_traffic_boost": "N/A",
        }


# ---------------------------------------------------------------------------
# Main Execution
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    
    # Default CSV path
    csv_path = "output/tsm_crawl_data.csv"
    
    if len(sys.argv) > 1:
        csv_path = sys.argv[1]
    
    print("=" * 60)
    print("SEO ANALYZER")
    print("=" * 60)
    print(f"\nAnalyzing: {csv_path}\n")
    
    try:
        # Initialize analyzer
        analyzer = SEOAnalyzer(csv_path)
        
        # Run all analyses
        print("Running metadata analysis...")
        analyzer.analyze_page_metadata()
        
        print("Running URL structure analysis...")
        analyzer.analyze_url_structure()
        
        print("Running internal linking analysis...")
        analyzer.analyze_internal_linking()
        
        print("Running keyword analysis...")
        analyzer.analyze_keyword_presence()
        
        # Calculate overall score
        overall_score = analyzer.calculate_overall_seo_score()
        interpretation = analyzer.get_score_interpretation()
        
        print("\n" + "=" * 60)
        print("RESULTS")
        print("=" * 60)
        print(f"\n✓ Overall SEO Score: {overall_score}/100")
        print(f"✓ Grade: {interpretation['grade']}")
        print(f"✓ Status: {interpretation['status']}")
        print(f"\n{interpretation['description']}")
        
        # Generate recommendations
        recommendations = analyzer.generate_priority_recommendations()
        
        print("\n" + "-" * 40)
        print("TOP PRIORITY ACTIONS:")
        print("-" * 40)
        
        for rec in recommendations[:3]:
            print(f"\n[{rec['category']}] {rec['action']}")
            print(f"   Impact: {rec['impact']}")
            print(f"   Effort: {rec['effort']}")
        
        # Generate report
        report_path = analyzer.generate_seo_report()
        
        print("\n" + "=" * 60)
        print(f"✓ Full report saved to: {report_path}")
        print("=" * 60)
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Make sure to run the crawler first to generate the CSV file.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
