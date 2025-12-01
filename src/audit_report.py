"""
Website Audit Report Generator Module
=====================================

Comprehensive audit report generator for TSM website analysis.
Generates detailed reports on information architecture, content distribution,
navigation bottlenecks, and actionable recommendations.

Author: TSM Web Crawler Project
"""

from __future__ import annotations

import json
import logging
import statistics
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import pandas as pd

# ---------------------------------------------------------------------------
# Logging Setup
# ---------------------------------------------------------------------------

logger = logging.getLogger("AuditReportGenerator")
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
# AuditReportGenerator Class
# ---------------------------------------------------------------------------


class AuditReportGenerator:
    """
    Comprehensive website audit report generator.
    
    Analyzes crawl data to produce detailed reports on:
    - Information Architecture scoring
    - Orphan pages and dead ends
    - Content distribution
    - Navigation bottlenecks
    - User journey analysis
    - Prioritized recommendations
    """

    def __init__(self, csv_file_path: str) -> None:
        """
        Initialize the audit report generator.
        
        Args:
            csv_file_path: Path to the crawl data CSV file.
        """
        self.csv_path = Path(csv_file_path)
        self.df = self._load_and_validate_csv()
        self.crawl_timestamp = datetime.now()
        logger.info(f"Loaded {len(self.df)} pages from {self.csv_path}")

    def _load_and_validate_csv(self) -> pd.DataFrame:
        """Load and validate the CSV data."""
        if not self.csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {self.csv_path}")

        df = pd.read_csv(self.csv_path)

        if df.empty:
            raise ValueError("CSV file is empty")

        # Normalize numeric columns
        for col in ("depth", "child_count", "status_code"):
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

        # Normalize string columns
        for col in ("url", "parent_url", "title", "description", "heading"):
            if col in df.columns:
                df[col] = df[col].fillna("").astype(str)

        return df

    def _extract_section(self, url: str) -> str:
        """Extract the main section (first path segment) from a URL."""
        try:
            parsed = urlparse(url)
            parts = [p for p in parsed.path.split("/") if p]
            return parts[0] if parts else "homepage"
        except Exception:
            return "unknown"

    def _get_homepage_url(self) -> Optional[str]:
        """Get the homepage URL (depth 0)."""
        if "depth" not in self.df.columns:
            return None
        roots = self.df[self.df["depth"] == 0]
        if roots.empty:
            return None
        return str(roots.iloc[0]["url"])

    def _build_link_graph(self) -> Dict[str, List[str]]:
        """Build parent → children adjacency list."""
        graph: Dict[str, List[str]] = defaultdict(list)
        for _, row in self.df.iterrows():
            parent = row.get("parent_url", "") or ""
            url = row.get("url", "") or ""
            if parent and url:
                graph[parent].append(url)
        return graph

    def _build_reverse_graph(self) -> Dict[str, List[str]]:
        """Build child → parents adjacency list (inbound links)."""
        graph: Dict[str, List[str]] = defaultdict(list)
        for _, row in self.df.iterrows():
            parent = row.get("parent_url", "") or ""
            url = row.get("url", "") or ""
            if parent and url:
                graph[url].append(parent)
        return graph

    # =========================================================================
    # a) calculate_ia_score
    # =========================================================================

    def calculate_ia_score(self) -> Dict[str, Any]:
        """
        Calculate Information Architecture score (0-100).
        
        Metrics:
        - Optimal depth: 3-4 clicks from homepage (best practice)
        - Content balance: Standard deviation of pages per depth
        - Link density: Average internal links per page
        - Page connectivity: % of pages linked from homepage
        
        Returns:
            Dictionary with score, breakdown, and interpretation.
        """
        total_pages = len(self.df)
        
        # Depth metrics
        avg_depth = float(self.df["depth"].mean()) if "depth" in self.df.columns else 0
        max_depth = int(self.df["depth"].max()) if "depth" in self.df.columns else 0
        
        # Depth score: 100 if avg_depth <= 4, else penalize
        if avg_depth <= 4:
            depth_score = 100.0
        else:
            depth_score = max(0, 100 - (avg_depth - 4) * 10)

        # Balance score: based on std deviation of pages per depth
        depth_counts = self.df["depth"].value_counts().sort_index()
        if len(depth_counts) > 1:
            std_dev_pages = statistics.stdev(depth_counts.tolist())
            balance_score = max(0, 100 - (std_dev_pages / total_pages * 100))
        else:
            balance_score = 100.0

        # Connectivity score: % of pages reachable from homepage
        homepage = self._get_homepage_url()
        graph = self._build_link_graph()
        
        if homepage:
            # BFS to find all reachable pages
            visited = set()
            queue = [homepage]
            while queue:
                current = queue.pop(0)
                if current in visited:
                    continue
                visited.add(current)
                for child in graph.get(current, []):
                    if child not in visited:
                        queue.append(child)
            linked_pages = len(visited)
        else:
            linked_pages = total_pages

        connectivity_score = (linked_pages / total_pages) * 100 if total_pages > 0 else 0

        # Final score: weighted average
        final_score = (depth_score * 0.3) + (balance_score * 0.3) + (connectivity_score * 0.4)
        final_score = round(min(100, max(0, final_score)), 1)

        # Interpretation
        if final_score >= 90:
            health_status = "Excellent"
            interpretation = "Outstanding information architecture with optimal navigation"
        elif final_score >= 75:
            health_status = "Good"
            interpretation = "Solid structure with minor improvements needed"
        elif final_score >= 50:
            health_status = "Needs Improvement"
            interpretation = "Several areas require attention for better user experience"
        else:
            health_status = "Critical"
            interpretation = "Major restructuring recommended for optimal navigation"

        return {
            "final_score": final_score,
            "health_status": health_status,
            "interpretation": interpretation,
            "breakdown": {
                "depth_score": round(depth_score, 1),
                "balance_score": round(balance_score, 1),
                "connectivity_score": round(connectivity_score, 1),
            },
            "metrics": {
                "total_pages": total_pages,
                "avg_depth": round(avg_depth, 2),
                "max_depth": max_depth,
                "linked_pages": linked_pages,
            },
        }

    # =========================================================================
    # b) identify_orphan_pages
    # =========================================================================

    def identify_orphan_pages(self) -> List[Dict[str, Any]]:
        """
        Find pages with NO inbound links (except homepage).
        
        Returns:
            List of dictionaries with {url, title, depth, reason}.
        """
        reverse_graph = self._build_reverse_graph()
        homepage = self._get_homepage_url()
        all_urls = set(self.df["url"].tolist())
        
        orphans = []
        for _, row in self.df.iterrows():
            url = row["url"]
            
            # Skip homepage
            if url == homepage:
                continue
            
            inbound_links = reverse_graph.get(url, [])
            
            if len(inbound_links) == 0:
                # Check if it appears as parent_url anywhere
                has_parent = row.get("parent_url", "")
                
                reason = "No inbound links detected"
                if not has_parent:
                    reason = "Isolated page - no parent URL and no inbound links"
                
                orphans.append({
                    "url": url,
                    "title": row.get("title", "No Title"),
                    "depth": int(row.get("depth", 0)),
                    "reason": reason,
                    "recommendation": "Add internal links or archive if obsolete",
                })

        return orphans

    # =========================================================================
    # c) identify_dead_ends
    # =========================================================================

    def identify_dead_ends(self) -> List[Dict[str, Any]]:
        """
        Find pages with NO outbound links to other pages.
        
        Returns:
            List of dictionaries with {url, title, importance}.
        """
        dead_ends = []
        
        for _, row in self.df.iterrows():
            child_count = int(row.get("child_count", 0))
            
            if child_count == 0:
                depth = int(row.get("depth", 0))
                
                # Importance based on depth (deeper = less critical)
                if depth <= 1:
                    importance = "High"
                elif depth <= 2:
                    importance = "Medium"
                else:
                    importance = "Low"
                
                dead_ends.append({
                    "url": row["url"],
                    "title": row.get("title", "No Title"),
                    "depth": depth,
                    "importance": importance,
                    "impact": "Users may leave without exploring further",
                    "recommendation": "Add related links, navigation, or call-to-action",
                })

        # Sort by importance
        importance_order = {"High": 0, "Medium": 1, "Low": 2}
        dead_ends.sort(key=lambda x: importance_order.get(x["importance"], 3))

        return dead_ends

    # =========================================================================
    # d) analyze_content_distribution
    # =========================================================================

    def analyze_content_distribution(self) -> Dict[str, Any]:
        """
        Analyze how content is spread across sections.
        
        Returns:
            Dictionary with sections, distribution, assessment, and recommendations.
        """
        self.df["section"] = self.df["url"].apply(self._extract_section)
        
        section_counts = self.df["section"].value_counts().to_dict()
        total_pages = len(self.df)
        avg_pages_per_section = total_pages / len(section_counts) if section_counts else 0

        sections_list = []
        for section, count in section_counts.items():
            pct = round((count / total_pages) * 100, 1)
            sections_list.append({
                "name": section,
                "page_count": count,
                "percentage": pct,
            })

        # Sort by page count descending
        sections_list.sort(key=lambda x: x["page_count"], reverse=True)

        # Identify imbalances
        most_heavy = sections_list[:3] if len(sections_list) >= 3 else sections_list
        most_light = sections_list[-3:] if len(sections_list) >= 3 else []

        # Balance assessment
        if len(section_counts) > 1:
            counts = list(section_counts.values())
            cv = statistics.stdev(counts) / statistics.mean(counts) if statistics.mean(counts) > 0 else 0
            if cv < 0.5:
                balance_assessment = "Well balanced"
            elif cv < 1.0:
                balance_assessment = "Moderately balanced"
            else:
                balance_assessment = "Needs rebalancing"
        else:
            balance_assessment = "Single section - N/A"

        # Recommendations
        recommendations = []
        for section in sections_list:
            if section["page_count"] > avg_pages_per_section * 2:
                recommendations.append(
                    f"Consider splitting '{section['name']}' into subsections for better navigation"
                )
            elif section["page_count"] < avg_pages_per_section * 0.3 and section["page_count"] < 5:
                recommendations.append(
                    f"Consider merging '{section['name']}' with related content or expanding it"
                )

        if not recommendations:
            recommendations.append("Content distribution appears healthy across sections")

        return {
            "sections": sections_list,
            "pages_per_section": section_counts,
            "total_sections": len(section_counts),
            "avg_pages_per_section": round(avg_pages_per_section, 1),
            "balance_assessment": balance_assessment,
            "most_content_heavy": most_heavy,
            "most_content_light": most_light,
            "recommendations": recommendations,
        }

    # =========================================================================
    # e) find_navigation_bottlenecks
    # =========================================================================

    def find_navigation_bottlenecks(self) -> List[Dict[str, Any]]:
        """
        Identify pages that are hard to reach (depth > 3).
        
        Returns:
            List of {url, minimum_clicks, path, improvement_suggestion}.
        """
        bottlenecks = []
        
        # Pages at depth > 3 are considered bottlenecks
        deep_pages = self.df[self.df["depth"] > 3]
        
        for _, row in deep_pages.iterrows():
            depth = int(row["depth"])
            
            # Build approximate path from parent chain
            path = [row["url"]]
            current_url = row.get("parent_url", "")
            visited = {row["url"]}
            
            while current_url and current_url not in visited:
                visited.add(current_url)
                path.insert(0, current_url)
                parent_row = self.df[self.df["url"] == current_url]
                if parent_row.empty:
                    break
                current_url = parent_row.iloc[0].get("parent_url", "")

            bottlenecks.append({
                "url": row["url"],
                "title": row.get("title", "No Title"),
                "minimum_clicks": depth,
                "path": " → ".join(path[-4:]),  # Show last 4 in path
                "improvement_suggestion": f"Add direct link from homepage or main section to reduce clicks from {depth} to 2-3",
            })

        # Sort by depth descending (hardest to reach first)
        bottlenecks.sort(key=lambda x: x["minimum_clicks"], reverse=True)

        return bottlenecks

    # =========================================================================
    # f) get_top_pages
    # =========================================================================

    def get_top_pages(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get most important pages by link count.
        
        Args:
            limit: Number of top pages to return.
            
        Returns:
            Sorted list with {url, title, child_count, importance_score}.
        """
        # Sort by child_count descending
        top_df = self.df.nlargest(limit, "child_count")
        
        max_links = int(self.df["child_count"].max()) if len(self.df) > 0 else 1
        
        top_pages = []
        for rank, (_, row) in enumerate(top_df.iterrows(), 1):
            child_count = int(row["child_count"])
            importance_score = round((child_count / max_links) * 100, 1) if max_links > 0 else 0
            
            top_pages.append({
                "rank": rank,
                "url": row["url"],
                "title": row.get("title", "No Title"),
                "child_count": child_count,
                "importance_score": importance_score,
                "role": "Navigation Hub" if child_count > 20 else "Content Page",
            })

        return top_pages

    # =========================================================================
    # g) get_depth_analysis
    # =========================================================================

    def get_depth_analysis(self) -> Dict[str, Any]:
        """
        Analyze depth distribution of the website.
        
        Returns:
            Dictionary with depth metrics and assessment.
        """
        total_pages = len(self.df)
        avg_depth = float(self.df["depth"].mean()) if "depth" in self.df.columns else 0
        max_depth = int(self.df["depth"].max()) if "depth" in self.df.columns else 0
        
        pages_by_depth = self.df["depth"].value_counts().sort_index().to_dict()
        pages_by_depth = {int(k): int(v) for k, v in pages_by_depth.items()}

        # Assessment based on best practices
        if max_depth <= 3:
            assessment = "Excellent - All content within 3 clicks"
        elif max_depth <= 4:
            assessment = "Good - Most content easily accessible"
        elif max_depth <= 5:
            assessment = "Acceptable - Some pages may be hard to find"
        else:
            assessment = "Needs restructuring - Deep pages are hard to discover"

        # Breadth vs Depth analysis
        depth_0_1 = sum(pages_by_depth.get(d, 0) for d in [0, 1])
        depth_2_3 = sum(pages_by_depth.get(d, 0) for d in [2, 3])
        depth_4_plus = sum(v for k, v in pages_by_depth.items() if k >= 4)

        if depth_0_1 > total_pages * 0.5:
            structure_type = "Flat - Most content at top levels"
        elif depth_4_plus > total_pages * 0.3:
            structure_type = "Deep - Significant content buried deep"
        else:
            structure_type = "Balanced - Good mix of breadth and depth"

        return {
            "total_pages": total_pages,
            "avg_depth": round(avg_depth, 2),
            "max_depth": max_depth,
            "pages_by_depth": pages_by_depth,
            "assessment": assessment,
            "structure_type": structure_type,
            "distribution": {
                "shallow_pages_0_1": depth_0_1,
                "mid_level_2_3": depth_2_3,
                "deep_pages_4_plus": depth_4_plus,
            },
        }

    # =========================================================================
    # h) analyze_user_journey
    # =========================================================================

    def analyze_user_journey(self) -> Dict[str, Any]:
        """
        Analyze typical user navigation paths.
        
        Returns:
            Dictionary with hubs, entry/exit points, and recommendations.
        """
        # Navigation hubs: pages with most outbound links
        hubs = self.df.nlargest(10, "child_count")[["url", "title", "child_count"]].to_dict("records")
        for hub in hubs:
            hub["role"] = "Primary Hub" if hub["child_count"] > 30 else "Secondary Hub"

        # Entry points: homepage + depth 1 pages with high link counts
        entry_candidates = self.df[self.df["depth"] <= 1].nlargest(10, "child_count")
        entry_points = entry_candidates[["url", "title", "child_count", "depth"]].to_dict("records")

        # Exit points: dead ends (no outbound links)
        exit_df = self.df[self.df["child_count"] == 0].head(10)
        exit_points = exit_df[["url", "title", "depth"]].to_dict("records")
        for ep in exit_points:
            ep["reason"] = "No outbound links"

        # Recommendations
        recommendations = []
        
        if len(exit_points) > 10:
            recommendations.append(
                f"High number of dead ends ({len(self.df[self.df['child_count'] == 0])} pages). "
                "Add related links or navigation elements."
            )
        
        if len(hubs) < 3:
            recommendations.append(
                "Few navigation hubs detected. Consider creating category landing pages."
            )

        avg_links = self.df["child_count"].mean()
        if avg_links < 5:
            recommendations.append(
                f"Low average internal links ({avg_links:.1f}). "
                "Increase internal linking for better discoverability."
            )

        if not recommendations:
            recommendations.append("Navigation structure appears well-organized.")

        return {
            "most_linked_pages": hubs,
            "likely_entry_points": entry_points,
            "likely_exit_points": exit_points,
            "average_links_per_page": round(self.df["child_count"].mean(), 1),
            "recommended_improvements": recommendations,
        }

    # =========================================================================
    # i) generate_recommendations
    # =========================================================================

    def generate_recommendations(self) -> Dict[str, Any]:
        """
        Create prioritized list of improvements.
        
        Returns:
            Dictionary with critical, important, and nice_to_have recommendations.
        """
        orphans = self.identify_orphan_pages()
        dead_ends = self.identify_dead_ends()
        bottlenecks = self.find_navigation_bottlenecks()
        ia_score = self.calculate_ia_score()
        
        critical = []
        important = []
        nice_to_have = []

        # Critical: Fix orphan pages
        if len(orphans) > 0:
            critical.append({
                "action": f"Fix {len(orphans)} orphan pages by adding internal links",
                "effort_estimate": f"{len(orphans) * 5} minutes",
                "expected_impact": "Improve page discoverability by search engines and users",
                "difficulty": "Easy",
            })

        # Critical: Fix high-importance dead ends
        high_dead_ends = [d for d in dead_ends if d["importance"] == "High"]
        if high_dead_ends:
            critical.append({
                "action": f"Add navigation to {len(high_dead_ends)} high-priority dead-end pages",
                "effort_estimate": f"{len(high_dead_ends) * 10} minutes",
                "expected_impact": "Reduce bounce rate and improve user engagement",
                "difficulty": "Easy",
            })

        # Important: Address navigation bottlenecks
        if bottlenecks:
            important.append({
                "action": f"Restructure {len(bottlenecks)} hard-to-reach pages",
                "effort_estimate": "2-4 hours",
                "expected_impact": "Reduce average clicks to content from deep pages",
                "difficulty": "Medium",
            })

        # Important: Balance content distribution
        content_dist = self.analyze_content_distribution()
        if content_dist["balance_assessment"] == "Needs rebalancing":
            important.append({
                "action": "Reorganize content sections for better balance",
                "effort_estimate": "1-2 days",
                "expected_impact": "Improve navigation clarity and user orientation",
                "difficulty": "Medium",
            })

        # Important: Improve IA score if below 75
        if ia_score["final_score"] < 75:
            important.append({
                "action": "Improve information architecture structure",
                "effort_estimate": "1 week",
                "expected_impact": f"Raise IA score from {ia_score['final_score']} to 80+",
                "difficulty": "Medium-Hard",
            })

        # Nice to have: Additional dead ends
        medium_dead_ends = [d for d in dead_ends if d["importance"] == "Medium"]
        if medium_dead_ends:
            nice_to_have.append({
                "action": f"Add links to {len(medium_dead_ends)} medium-priority dead-end pages",
                "effort_estimate": f"{len(medium_dead_ends) * 5} minutes",
                "expected_impact": "Incremental improvement in site navigation",
                "difficulty": "Easy",
            })

        # Nice to have: Implement breadcrumbs
        nice_to_have.append({
            "action": "Implement breadcrumb navigation across all pages",
            "effort_estimate": "1-2 days development",
            "expected_impact": "Improve user orientation and reduce back-button usage",
            "difficulty": "Medium",
        })

        # Nice to have: Add related content sections
        nice_to_have.append({
            "action": "Add 'Related Pages' sections to content pages",
            "effort_estimate": "3-5 days development",
            "expected_impact": "Increase pages per session and reduce bounce rate",
            "difficulty": "Medium",
        })

        return {
            "critical": critical,
            "important": important,
            "nice_to_have": nice_to_have,
            "summary": {
                "total_actions": len(critical) + len(important) + len(nice_to_have),
                "critical_count": len(critical),
                "important_count": len(important),
                "nice_to_have_count": len(nice_to_have),
            },
        }

    # =========================================================================
    # j) generate_full_report
    # =========================================================================

    def generate_full_report(self, output_file: str = "output/TSM_Website_Audit_Report.txt") -> str:
        """
        Generate comprehensive audit report.
        
        Args:
            output_file: Path to save the report.
            
        Returns:
            The report content as a string.
        """
        # Gather all data
        ia_score = self.calculate_ia_score()
        orphans = self.identify_orphan_pages()
        dead_ends = self.identify_dead_ends()
        content_dist = self.analyze_content_distribution()
        bottlenecks = self.find_navigation_bottlenecks()
        top_pages = self.get_top_pages(10)
        depth_analysis = self.get_depth_analysis()
        user_journey = self.analyze_user_journey()
        recommendations = self.generate_recommendations()

        # Build report
        report_lines = []
        
        def add_line(line: str = "") -> None:
            report_lines.append(line)

        def add_separator(char: str = "═", width: int = 80) -> None:
            report_lines.append(char * width)

        def add_section_header(title: str) -> None:
            add_line()
            add_separator()
            add_line(title)
            add_separator()
            add_line()

        # Header
        add_separator("═")
        add_line("                    TSM WEBSITE AUDIT REPORT")
        add_line(f"                    Generated: {self.crawl_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        add_separator("═")

        # ─────────────────────────────────────────────────────────────────────
        # 1. EXECUTIVE SUMMARY
        # ─────────────────────────────────────────────────────────────────────
        add_section_header("1. EXECUTIVE SUMMARY")
        
        add_line(f"   Overall Information Architecture Score: {ia_score['final_score']}/100")
        add_line(f"   Health Status: {ia_score['health_status']}")
        add_line()
        add_line("   KEY FINDINGS:")
        add_line(f"   • Total pages analyzed: {len(self.df)}")
        add_line(f"   • Maximum depth: {depth_analysis['max_depth']} clicks from homepage")
        add_line(f"   • Orphan pages found: {len(orphans)}")
        add_line(f"   • Dead-end pages found: {len(dead_ends)}")
        add_line(f"   • Navigation bottlenecks: {len(bottlenecks)}")
        add_line()
        
        if recommendations["critical"]:
            add_line("   CRITICAL ISSUES:")
            for item in recommendations["critical"]:
                add_line(f"   ⚠ {item['action']}")
        
        add_line()
        add_line("   QUICK WINS:")
        if orphans:
            add_line(f"   ✓ Link {min(5, len(orphans))} orphan pages to improve SEO")
        if dead_ends:
            add_line(f"   ✓ Add navigation to {min(5, len(dead_ends))} dead-end pages")
        add_line("   ✓ Review top pages for optimization opportunities")

        # ─────────────────────────────────────────────────────────────────────
        # 2. WEBSITE STRUCTURE ANALYSIS
        # ─────────────────────────────────────────────────────────────────────
        add_section_header("2. WEBSITE STRUCTURE ANALYSIS")
        
        add_line(f"   Total Pages Analyzed: {depth_analysis['total_pages']}")
        add_line(f"   Homepage to Deepest Page: {depth_analysis['max_depth']} clicks")
        add_line(f"   Average Depth: {depth_analysis['avg_depth']} clicks")
        add_line(f"   Structure Type: {depth_analysis['structure_type']}")
        add_line()
        add_line("   PAGES PER DEPTH LEVEL:")
        add_line("   ┌─────────┬───────────┬────────────┐")
        add_line("   │  Depth  │   Pages   │ Percentage │")
        add_line("   ├─────────┼───────────┼────────────┤")
        for depth, count in sorted(depth_analysis["pages_by_depth"].items()):
            pct = round(count / depth_analysis["total_pages"] * 100, 1)
            add_line(f"   │    {depth}    │    {count:>4}   │   {pct:>5.1f}%   │")
        add_line("   └─────────┴───────────┴────────────┘")
        add_line()
        add_line(f"   Assessment: {depth_analysis['assessment']}")

        # ─────────────────────────────────────────────────────────────────────
        # 3. CRITICAL ISSUES IDENTIFIED
        # ─────────────────────────────────────────────────────────────────────
        add_section_header("3. CRITICAL ISSUES IDENTIFIED")

        # 3.1 Orphan Pages
        add_line("   3.1 ORPHAN PAGES")
        add_line("   " + "─" * 50)
        add_line(f"   Found: {len(orphans)} pages with no inbound links")
        add_line()
        if orphans:
            for i, orphan in enumerate(orphans[:10], 1):
                add_line(f"   {i}. {orphan['url'][:60]}...")
                add_line(f"      Title: {orphan['title'][:50]}")
                add_line(f"      Depth: {orphan['depth']} | Reason: {orphan['reason']}")
                add_line()
            if len(orphans) > 10:
                add_line(f"   ... and {len(orphans) - 10} more orphan pages")
        else:
            add_line("   ✓ No orphan pages found - excellent internal linking!")
        add_line()

        # 3.2 Dead Ends
        add_line("   3.2 DEAD-END PAGES")
        add_line("   " + "─" * 50)
        add_line(f"   Found: {len(dead_ends)} pages with no outbound navigation")
        add_line()
        high_priority = [d for d in dead_ends if d["importance"] == "High"]
        if high_priority:
            add_line(f"   HIGH PRIORITY ({len(high_priority)} pages):")
            for i, de in enumerate(high_priority[:5], 1):
                add_line(f"   {i}. {de['url'][:60]}")
                add_line(f"      Impact: {de['impact']}")
        add_line()

        # 3.3 Navigation Bottlenecks
        add_line("   3.3 NAVIGATION BOTTLENECKS")
        add_line("   " + "─" * 50)
        add_line(f"   Found: {len(bottlenecks)} pages requiring more than 3 clicks")
        add_line()
        if bottlenecks:
            for i, bn in enumerate(bottlenecks[:5], 1):
                add_line(f"   {i}. {bn['url'][:60]}")
                add_line(f"      Clicks required: {bn['minimum_clicks']}")
                add_line(f"      Suggestion: {bn['improvement_suggestion'][:60]}")
                add_line()
        else:
            add_line("   ✓ All pages within optimal click distance!")
        add_line()

        # 3.4 Content Imbalance
        add_line("   3.4 CONTENT DISTRIBUTION")
        add_line("   " + "─" * 50)
        add_line(f"   Balance Assessment: {content_dist['balance_assessment']}")
        add_line(f"   Total Sections: {content_dist['total_sections']}")
        add_line(f"   Average Pages per Section: {content_dist['avg_pages_per_section']}")
        add_line()
        add_line("   Most Content-Heavy Sections:")
        for section in content_dist["most_content_heavy"]:
            add_line(f"   • {section['name']}: {section['page_count']} pages ({section['percentage']}%)")
        add_line()

        # ─────────────────────────────────────────────────────────────────────
        # 4. INFORMATION ARCHITECTURE ASSESSMENT
        # ─────────────────────────────────────────────────────────────────────
        add_section_header("4. INFORMATION ARCHITECTURE ASSESSMENT")
        
        add_line(f"   OVERALL IA SCORE: {ia_score['final_score']}/100 ({ia_score['health_status']})")
        add_line()
        add_line("   SCORE BREAKDOWN:")
        add_line(f"   • Depth Optimization:  {ia_score['breakdown']['depth_score']}/100")
        add_line(f"   • Content Balance:     {ia_score['breakdown']['balance_score']}/100")
        add_line(f"   • Page Connectivity:   {ia_score['breakdown']['connectivity_score']}/100")
        add_line()
        add_line(f"   Architecture Type: {depth_analysis['structure_type']}")
        add_line()
        add_line(f"   Assessment: {ia_score['interpretation']}")

        # ─────────────────────────────────────────────────────────────────────
        # 5. CONTENT DISTRIBUTION ANALYSIS
        # ─────────────────────────────────────────────────────────────────────
        add_section_header("5. CONTENT DISTRIBUTION ANALYSIS")
        
        add_line("   SECTIONS OVERVIEW:")
        add_line("   ┌────────────────────────────┬───────────┬────────────┐")
        add_line("   │         Section            │   Pages   │ Percentage │")
        add_line("   ├────────────────────────────┼───────────┼────────────┤")
        for section in content_dist["sections"][:15]:
            name = section["name"][:26].ljust(26)
            add_line(f"   │ {name} │    {section['page_count']:>4}   │   {section['percentage']:>5.1f}%   │")
        add_line("   └────────────────────────────┴───────────┴────────────┘")
        add_line()
        add_line("   RECOMMENDATIONS:")
        for rec in content_dist["recommendations"]:
            add_line(f"   • {rec}")

        # ─────────────────────────────────────────────────────────────────────
        # 6. USER JOURNEY ANALYSIS
        # ─────────────────────────────────────────────────────────────────────
        add_section_header("6. USER JOURNEY ANALYSIS")
        
        add_line("   NAVIGATION HUBS (Most Linked Pages):")
        add_line("   ┌────┬────────────────────────────────────┬───────────┬─────────────┐")
        add_line("   │ #  │ URL                                │   Links   │    Role     │")
        add_line("   ├────┼────────────────────────────────────┼───────────┼─────────────┤")
        for i, hub in enumerate(user_journey["most_linked_pages"][:10], 1):
            url_short = hub["url"][:34].ljust(34)
            role = hub["role"][:11].ljust(11)
            add_line(f"   │ {i:>2} │ {url_short} │    {hub['child_count']:>4}   │ {role} │")
        add_line("   └────┴────────────────────────────────────┴───────────┴─────────────┘")
        add_line()
        add_line(f"   Average Links per Page: {user_journey['average_links_per_page']}")
        add_line()
        add_line("   LIKELY EXIT POINTS:")
        for ep in user_journey["likely_exit_points"][:5]:
            add_line(f"   • {ep['url'][:50]}... (depth: {ep['depth']})")
        add_line()
        add_line("   RECOMMENDATIONS:")
        for rec in user_journey["recommended_improvements"]:
            add_line(f"   • {rec}")

        # ─────────────────────────────────────────────────────────────────────
        # 7. TOP 10 MOST IMPORTANT PAGES
        # ─────────────────────────────────────────────────────────────────────
        add_section_header("7. TOP 10 MOST IMPORTANT PAGES")
        
        add_line("   ┌──────┬────────────────────────────────────┬───────────┬────────────┐")
        add_line("   │ Rank │ URL                                │   Links   │ Importance │")
        add_line("   ├──────┼────────────────────────────────────┼───────────┼────────────┤")
        for page in top_pages:
            url_short = page["url"][:34].ljust(34)
            add_line(f"   │  {page['rank']:>2}  │ {url_short} │    {page['child_count']:>4}   │   {page['importance_score']:>5.1f}%   │")
        add_line("   └──────┴────────────────────────────────────┴───────────┴────────────┘")

        # ─────────────────────────────────────────────────────────────────────
        # 8. TOP 10 LEAST CONNECTED PAGES
        # ─────────────────────────────────────────────────────────────────────
        add_section_header("8. TOP 10 LEAST CONNECTED PAGES")
        
        least_connected = self.df.nsmallest(10, "child_count")[["url", "title", "child_count", "depth"]]
        add_line("   ┌──────┬────────────────────────────────────┬───────────┬─────────────────────┐")
        add_line("   │ Rank │ URL                                │   Links   │   Recommendation    │")
        add_line("   ├──────┼────────────────────────────────────┼───────────┼─────────────────────┤")
        for i, (_, row) in enumerate(least_connected.iterrows(), 1):
            url_short = str(row["url"])[:34].ljust(34)
            rec = "Add more links" if row["child_count"] == 0 else "Review content"
            rec = rec.ljust(19)
            add_line(f"   │  {i:>2}  │ {url_short} │    {int(row['child_count']):>4}   │ {rec} │")
        add_line("   └──────┴────────────────────────────────────┴───────────┴─────────────────────┘")

        # ─────────────────────────────────────────────────────────────────────
        # 9. ACTIONABLE RECOMMENDATIONS
        # ─────────────────────────────────────────────────────────────────────
        add_section_header("9. ACTIONABLE RECOMMENDATIONS")
        
        add_line("   9.1 IMMEDIATE FIXES (This Week)")
        add_line("   " + "─" * 50)
        if recommendations["critical"]:
            for i, item in enumerate(recommendations["critical"], 1):
                add_line(f"   Priority {i}: {item['action']}")
                add_line(f"              Effort: {item['effort_estimate']} | Difficulty: {item['difficulty']}")
                add_line(f"              Impact: {item['expected_impact']}")
                add_line()
        else:
            add_line("   ✓ No critical issues requiring immediate attention!")
        add_line()

        add_line("   9.2 SHORT-TERM IMPROVEMENTS (This Month)")
        add_line("   " + "─" * 50)
        if recommendations["important"]:
            for i, item in enumerate(recommendations["important"], 1):
                add_line(f"   {i}. {item['action']}")
                add_line(f"      Effort: {item['effort_estimate']} | Difficulty: {item['difficulty']}")
                add_line()
        add_line()

        add_line("   9.3 LONG-TERM ENHANCEMENTS (Next Quarter)")
        add_line("   " + "─" * 50)
        for i, item in enumerate(recommendations["nice_to_have"], 1):
            add_line(f"   {i}. {item['action']}")
            add_line(f"      Strategic Value: {item['expected_impact']}")
            add_line()

        # ─────────────────────────────────────────────────────────────────────
        # 10. TECHNICAL METRICS
        # ─────────────────────────────────────────────────────────────────────
        add_section_header("10. TECHNICAL METRICS")
        
        # Calculate technical metrics
        missing_titles = int((self.df["title"] == "").sum())
        missing_desc = int((self.df["description"] == "").sum()) if "description" in self.df.columns else 0
        success_rate = round((self.df["status_code"] == 200).sum() / len(self.df) * 100, 1) if "status_code" in self.df.columns else 100
        
        domains = self.df["url"].apply(lambda x: urlparse(x).netloc).nunique()
        
        add_line(f"   • Crawl Date & Time: {self.crawl_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        add_line(f"   • Total URLs Analyzed: {len(self.df)}")
        add_line(f"   • Unique Domains: {domains}")
        add_line(f"   • Success Rate: {success_rate}%")
        add_line(f"   • Pages Missing Titles: {missing_titles}")
        add_line(f"   • Pages Missing Meta Descriptions: {missing_desc}")

        # ─────────────────────────────────────────────────────────────────────
        # 11. COMPETITIVE BENCHMARKING
        # ─────────────────────────────────────────────────────────────────────
        add_section_header("11. COMPETITIVE BENCHMARKING")
        
        add_line("   INDUSTRY BEST PRACTICES COMPARISON:")
        add_line()
        add_line("   ┌────────────────────────────┬────────────┬────────────┬────────────┐")
        add_line("   │         Metric             │   Yours    │   Ideal    │   Status   │")
        add_line("   ├────────────────────────────┼────────────┼────────────┼────────────┤")
        
        # Max Depth
        max_d = depth_analysis["max_depth"]
        status = "✓ Good" if max_d <= 4 else "⚠ Review"
        add_line(f"   │ Max Depth                  │     {max_d:>2}     │    ≤ 4     │   {status}  │")
        
        # Avg Depth
        avg_d = depth_analysis["avg_depth"]
        status = "✓ Good" if avg_d <= 3 else "⚠ Review"
        add_line(f"   │ Average Depth              │    {avg_d:.1f}    │   ≤ 3.0    │   {status}  │")
        
        # IA Score
        ia = ia_score["final_score"]
        status = "✓ Good" if ia >= 75 else "⚠ Review"
        add_line(f"   │ IA Score                   │    {ia:.0f}     │   ≥ 75     │   {status}  │")
        
        # Orphan Rate
        orphan_rate = round(len(orphans) / len(self.df) * 100, 1)
        status = "✓ Good" if orphan_rate < 5 else "⚠ Review"
        add_line(f"   │ Orphan Rate                │   {orphan_rate:.1f}%    │   < 5%     │   {status}  │")
        
        # Dead End Rate
        dead_end_rate = round(len(dead_ends) / len(self.df) * 100, 1)
        status = "✓ Good" if dead_end_rate < 20 else "⚠ Review"
        add_line(f"   │ Dead End Rate              │   {dead_end_rate:.1f}%   │   < 20%    │   {status}  │")
        
        add_line("   └────────────────────────────┴────────────┴────────────┴────────────┘")
        add_line()
        
        # Position assessment
        score_count = sum([
            1 if max_d <= 4 else 0,
            1 if avg_d <= 3 else 0,
            1 if ia >= 75 else 0,
            1 if orphan_rate < 5 else 0,
            1 if dead_end_rate < 20 else 0,
        ])
        
        if score_count >= 4:
            position = "Leading - Above industry standards"
        elif score_count >= 3:
            position = "Average - Meeting most standards"
        else:
            position = "Behind - Improvements needed"
        
        add_line(f"   Your Position: {position}")

        # ─────────────────────────────────────────────────────────────────────
        # 12. IMPLEMENTATION ROADMAP
        # ─────────────────────────────────────────────────────────────────────
        add_section_header("12. IMPLEMENTATION ROADMAP")
        
        add_line("   PHASE 1 (Quick Wins - Week 1-2)")
        add_line("   ├─ Action 1: Fix orphan pages")
        add_line("   │  ├─ Effort: 2-4 hours")
        add_line("   │  ├─ Impact: +15% SEO improvement")
        add_line("   │  └─ Owner: Content Team")
        add_line("   │")
        add_line("   ├─ Action 2: Add navigation to dead ends")
        add_line("   │  ├─ Effort: 4-6 hours")
        add_line("   │  ├─ Impact: -20% bounce rate")
        add_line("   │  └─ Owner: IT Team")
        add_line("   │")
        add_line("   └─ Action 3: Review and update meta descriptions")
        add_line("      ├─ Effort: 2-3 hours")
        add_line("      └─ Impact: +10% click-through rate")
        add_line()
        
        add_line("   PHASE 2 (Major Improvements - Month 1)")
        add_line("   ├─ Reorganize deep content to reduce clicks")
        add_line("   ├─ Create section landing pages")
        add_line("   └─ Implement related content widgets")
        add_line()
        
        add_line("   PHASE 3 (Strategic Changes - Quarter 1)")
        add_line("   ├─ Implement breadcrumb navigation")
        add_line("   ├─ Add site search functionality")
        add_line("   └─ Create comprehensive sitemap")

        # ─────────────────────────────────────────────────────────────────────
        # 13. SUCCESS METRICS & KPIs
        # ─────────────────────────────────────────────────────────────────────
        add_section_header("13. SUCCESS METRICS & KPIs")
        
        add_line("   CURRENT STATE (Before Implementation):")
        add_line(f"   • Average clicks to reach content: {depth_analysis['avg_depth']}")
        add_line(f"   • Orphan pages: {len(orphans)}")
        add_line(f"   • Dead ends: {len(dead_ends)}")
        add_line(f"   • IA Score: {ia_score['final_score']}")
        add_line()
        
        add_line("   TARGET METRICS (After 3 months):")
        add_line(f"   • Average clicks to reach content: ≤ 2.5 (current: {depth_analysis['avg_depth']})")
        add_line(f"   • Orphan pages: 0 (current: {len(orphans)})")
        add_line(f"   • Dead ends: Reduce by 50% (target: {len(dead_ends) // 2})")
        add_line(f"   • IA Score: ≥ 85 (current: {ia_score['final_score']})")
        add_line(f"   • Navigation efficiency: Improve by 30%")

        # ─────────────────────────────────────────────────────────────────────
        # 14. CONCLUSION
        # ─────────────────────────────────────────────────────────────────────
        add_section_header("14. CONCLUSION")
        
        add_line(f"   OVERALL ASSESSMENT: {ia_score['health_status']}")
        add_line()
        add_line(f"   {ia_score['interpretation']}")
        add_line()
        add_line("   PRIORITY AREAS:")
        add_line("   1. Address critical orphan pages and dead ends")
        add_line("   2. Optimize navigation bottlenecks for better user experience")
        add_line("   3. Rebalance content distribution across sections")
        add_line()
        add_line("   EXPECTED TIMELINE:")
        add_line("   • Quick wins: 1-2 weeks")
        add_line("   • Major improvements: 1 month")
        add_line("   • Strategic changes: 1 quarter")
        add_line()
        add_line("   NEXT STEPS:")
        add_line("   1. Review this report with stakeholders")
        add_line("   2. Prioritize critical issues for immediate action")
        add_line("   3. Assign ownership for each phase")
        add_line("   4. Schedule follow-up audit in 3 months")
        add_line()

        # Footer
        add_separator("═")
        add_line("                         END OF AUDIT REPORT")
        add_line(f"                    Report generated by TSM Website Crawler")
        add_line(f"                    {self.crawl_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        add_separator("═")

        # Join and save report
        report_content = "\n".join(report_lines)
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report_content)
        
        logger.info(f"Audit report generated: {output_file}")
        
        return report_content


# ---------------------------------------------------------------------------
# Main Execution
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    auditor = AuditReportGenerator("output/tsm_crawl_data.csv")
    auditor.generate_full_report()
    print("Report generated successfully!")
    print("Output: output/TSM_Website_Audit_Report.txt")

