"""
Analytics Module for Web Crawler Data
Generates comprehensive insights and metrics from crawled website data.
"""

import pandas as pd
import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict, Counter
import logging
from urllib.parse import urlparse
import re


# Setup logger
logger = logging.getLogger("TSMAnalytics")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def calculate_site_metrics(csv_file: str) -> Dict[str, Any]:
    """
    Calculate comprehensive site metrics from crawled data.
    
    Args:
        csv_file: Path to CSV file containing crawl data
        
    Returns:
        Dictionary containing:
        - total_pages: Total pages crawled
        - average_pages_per_section: Average pages per main section
        - site_depth_structure: Depth distribution analysis
        - most_important_pages: Top pages by link count
        - navigation_efficiency_score: Score from 0-100
    """
    try:
        logger.info(f"Calculating site metrics from {csv_file}")
        df = pd.read_csv(csv_file)
        
        if df.empty:
            logger.warning("CSV file is empty")
            return {}
        
        # Total pages crawled
        total_pages = len(df)
        
        # Average pages per section (depth 1 pages are main sections)
        depth_1_pages = df[df['depth'] == 1]
        num_sections = len(depth_1_pages) if len(depth_1_pages) > 0 else 1
        average_pages_per_section = total_pages / num_sections if num_sections > 0 else 0
        
        # Site depth structure
        depth_distribution = df['depth'].value_counts().sort_index().to_dict()
        max_depth = df['depth'].max()
        depth_structure = {
            "max_depth": int(max_depth),
            "depth_distribution": depth_distribution,
            "average_depth": float(df['depth'].mean()),
            "depth_variance": float(df['depth'].var())
        }
        
        # Most important pages (by link count)
        top_pages = df.nlargest(10, 'child_count')[['url', 'title', 'child_count', 'depth']].to_dict('records')
        most_important_pages = [
            {
                "url": page['url'],
                "title": page.get('title', 'No Title'),
                "link_count": int(page['child_count']),
                "depth": int(page['depth'])
            }
            for page in top_pages
        ]
        
        # Navigation efficiency score (0-100)
        # Factors:
        # - Depth distribution (shallow is better for UX)
        # - Link distribution (balanced is better)
        # - Orphan pages (fewer is better)
        # - Average links per page (moderate is better)
        
        avg_links = df['child_count'].mean()
        orphan_pages = len(df[df['child_count'] == 0])
        orphan_ratio = orphan_pages / total_pages if total_pages > 0 else 0
        
        # Score components (each 0-25 points)
        depth_score = max(0, 25 - (max_depth * 5))  # Lower depth = higher score
        link_distribution_score = 25 if 10 <= avg_links <= 50 else max(0, 25 - abs(avg_links - 30) / 2)
        orphan_score = max(0, 25 - (orphan_ratio * 100))
        connectivity_score = min(25, (total_pages - orphan_pages) / total_pages * 25) if total_pages > 0 else 0
        
        navigation_efficiency_score = round(depth_score + link_distribution_score + orphan_score + connectivity_score, 2)
        
        metrics = {
            "total_pages": total_pages,
            "average_pages_per_section": round(average_pages_per_section, 2),
            "site_depth_structure": depth_structure,
            "most_important_pages": most_important_pages,
            "navigation_efficiency_score": navigation_efficiency_score,
            "score_breakdown": {
                "depth_score": round(depth_score, 2),
                "link_distribution_score": round(link_distribution_score, 2),
                "orphan_score": round(orphan_score, 2),
                "connectivity_score": round(connectivity_score, 2)
            }
        }
        
        logger.info("Site metrics calculated successfully")
        return metrics
    
    except FileNotFoundError:
        logger.error(f"CSV file not found: {csv_file}")
        raise
    except Exception as e:
        logger.error(f"Error calculating site metrics: {e}")
        raise


def identify_site_sections(csv_file: str) -> Dict[str, Any]:
    """
    Identify main website sections and analyze their structure.
    
    Args:
        csv_file: Path to CSV file containing crawl data
        
    Returns:
        Dictionary containing:
        - depth_1_pages: Main section pages
        - page_count_per_section: Pages under each section
        - subsection_count: Number of subsections per section
        - content_distribution: How content is distributed
    """
    try:
        logger.info(f"Identifying site sections from {csv_file}")
        df = pd.read_csv(csv_file)
        
        if df.empty:
            logger.warning("CSV file is empty")
            return {}
        
        # Get depth 1 pages (main sections)
        depth_1_pages = df[df['depth'] == 1].copy()
        
        # Extract section names from URLs
        def extract_section_name(url: str) -> str:
            try:
                parsed = urlparse(url)
                path_parts = [p for p in parsed.path.split('/') if p]
                if path_parts:
                    return path_parts[0]
                return "home"
            except:
                return "unknown"
        
        depth_1_pages['section'] = depth_1_pages['url'].apply(extract_section_name)
        
        # Build parent-child relationships
        url_to_parent = dict(zip(df['url'], df['parent_url']))
        parent_to_children = defaultdict(list)
        
        for _, row in df.iterrows():
            parent = row['parent_url']
            if pd.notna(parent) and parent in url_to_parent:
                parent_to_children[parent].append(row['url'])
        
        # Calculate pages per section
        section_stats = {}
        for _, section_page in depth_1_pages.iterrows():
            section_url = section_page['url']
            section_name = section_page['section']
            
            # Count all pages under this section (depth >= 1, same section path)
            section_path = extract_section_name(section_url)
            section_pages = df[df['url'].str.contains(f'/{section_path}/', na=False) | 
                              (df['url'] == section_url)]
            
            # Count subsections (depth 2 pages under this section)
            subsections = []
            for child_url in parent_to_children.get(section_url, []):
                child_row = df[df['url'] == child_url]
                if not child_row.empty and child_row.iloc[0]['depth'] == 2:
                    subsections.append(child_url)
            
            section_stats[section_name] = {
                "url": str(section_url),
                "title": str(section_page.get('title', 'No Title')),
                "page_count": int(len(section_pages)),
                "subsection_count": int(len(subsections)),
                "total_links": int(section_page.get('child_count', 0)),
                "depth": int(section_page['depth'])
            }
        
        # Content distribution analysis
        total_pages = len(df)
        content_distribution = {
            "sections": len(section_stats),
            "pages_per_section_avg": round(total_pages / len(section_stats) if section_stats else 0, 2),
            "largest_section": max(section_stats.values(), key=lambda x: x['page_count'])['title'] if section_stats else None,
            "smallest_section": min(section_stats.values(), key=lambda x: x['page_count'])['title'] if section_stats else None
        }
        
        result = {
            "depth_1_pages": depth_1_pages[['url', 'title', 'child_count', 'depth']].to_dict('records'),
            "page_count_per_section": section_stats,
            "subsection_count": {name: stats['subsection_count'] for name, stats in section_stats.items()},
            "content_distribution": content_distribution
        }
        
        logger.info(f"Identified {len(section_stats)} main sections")
        return result
    
    except FileNotFoundError:
        logger.error(f"CSV file not found: {csv_file}")
        raise
    except Exception as e:
        logger.error(f"Error identifying site sections: {e}")
        raise


def analyze_information_architecture(csv_file: str) -> Dict[str, Any]:
    """
    Analyze the website's information architecture.
    
    Args:
        csv_file: Path to CSV file containing crawl data
        
    Returns:
        Dictionary containing:
        - site_structure_analysis: Overall structure assessment
        - navigation_hierarchy_assessment: Hierarchy quality
        - breadth_vs_depth_analysis: Navigation pattern analysis
        - recommendations: Improvement suggestions
    """
    try:
        logger.info(f"Analyzing information architecture from {csv_file}")
        df = pd.read_csv(csv_file)
        
        if df.empty:
            logger.warning("CSV file is empty")
            return {}
        
        # Site structure analysis
        total_pages = len(df)
        max_depth = df['depth'].max()
        avg_depth = df['depth'].mean()
        
        # Calculate breadth at each level
        breadth_by_depth = df.groupby('depth').size().to_dict()
        avg_breadth = sum(breadth_by_depth.values()) / len(breadth_by_depth) if breadth_by_depth else 0
        
        # Navigation hierarchy assessment
        # Check for balanced hierarchy
        depth_0_count = breadth_by_depth.get(0, 0)
        depth_1_count = breadth_by_depth.get(1, 0)
        depth_2_count = breadth_by_depth.get(2, 0)
        
        hierarchy_balance = "balanced" if depth_1_count > 0 and depth_2_count > 0 else "unbalanced"
        
        # Calculate fan-out ratio (children per parent)
        parent_child_ratio = {}
        for depth in range(max_depth):
            parents = df[df['depth'] == depth]
            children = df[df['depth'] == depth + 1]
            if len(parents) > 0:
                parent_child_ratio[depth] = len(children) / len(parents)
        
        avg_fan_out = sum(parent_child_ratio.values()) / len(parent_child_ratio) if parent_child_ratio else 0
        
        # Breadth vs Depth analysis
        total_breadth = sum(breadth_by_depth.values())
        depth_factor = max_depth
        breadth_factor = total_breadth / max_depth if max_depth > 0 else 0
        
        navigation_pattern = "wide" if breadth_factor > 20 else "deep" if depth_factor > 3 else "balanced"
        
        # Orphan pages analysis
        orphan_pages = len(df[df['child_count'] == 0])
        orphan_percentage = (orphan_pages / total_pages * 100) if total_pages > 0 else 0
        
        # Generate recommendations
        recommendations = []
        
        if max_depth > 4:
            recommendations.append("Consider reducing navigation depth. Deep hierarchies (>4 levels) can confuse users.")
        
        if orphan_percentage > 20:
            recommendations.append(f"High percentage of orphan pages ({orphan_percentage:.1f}%). Add internal links to improve discoverability.")
        
        if avg_fan_out > 15:
            recommendations.append("High fan-out ratio. Consider grouping related pages into subsections.")
        
        if avg_fan_out < 3 and max_depth > 2:
            recommendations.append("Low fan-out ratio. Consider flattening the navigation structure.")
        
        if navigation_pattern == "deep":
            recommendations.append("Site has deep navigation. Consider adding breadcrumbs and improving top-level navigation.")
        
        if navigation_pattern == "wide":
            recommendations.append("Site has wide navigation. Consider organizing content into logical categories.")
        
        # Check for broken links (status codes)
        failed_pages = df[df['status_code'].isna() | (df['status_code'] != 200)]
        if len(failed_pages) > 0:
            recommendations.append(f"Found {len(failed_pages)} pages with errors. Review and fix broken links.")
        
        result = {
            "site_structure_analysis": {
                "total_pages": total_pages,
                "max_depth": int(max_depth),
                "average_depth": round(avg_depth, 2),
                "breadth_by_depth": {int(k): int(v) for k, v in breadth_by_depth.items()},
                "average_breadth": round(avg_breadth, 2)
            },
            "navigation_hierarchy_assessment": {
                "hierarchy_balance": hierarchy_balance,
                "depth_distribution": {
                    "level_0": depth_0_count,
                    "level_1": depth_1_count,
                    "level_2": depth_2_count
                },
                "average_fan_out": round(avg_fan_out, 2),
                "fan_out_by_level": {int(k): round(v, 2) for k, v in parent_child_ratio.items()}
            },
            "breadth_vs_depth_analysis": {
                "navigation_pattern": navigation_pattern,
                "breadth_factor": round(breadth_factor, 2),
                "depth_factor": int(depth_factor),
                "orphan_pages": orphan_pages,
                "orphan_percentage": round(orphan_percentage, 2)
            },
            "recommendations": recommendations if recommendations else ["Site structure looks good! No major issues detected."]
        }
        
        logger.info("Information architecture analysis completed")
        return result
    
    except FileNotFoundError:
        logger.error(f"CSV file not found: {csv_file}")
        raise
    except Exception as e:
        logger.error(f"Error analyzing information architecture: {e}")
        raise


def generate_insights_report(csv_file: str, output_path: Optional[str] = None) -> str:
    """
    Generate a comprehensive insights report from crawled data.
    
    Args:
        csv_file: Path to CSV file containing crawl data
        output_path: Optional path to save report (default: output/insights_report.txt)
        
    Returns:
        Formatted report string
    """
    try:
        logger.info(f"Generating insights report from {csv_file}")
        
        # Calculate all metrics
        metrics = calculate_site_metrics(csv_file)
        sections = identify_site_sections(csv_file)
        ia_analysis = analyze_information_architecture(csv_file)
        
        df = pd.read_csv(csv_file)
        
        # Build report
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("TSM WEBSITE CRAWLER - COMPREHENSIVE INSIGHTS REPORT")
        report_lines.append("=" * 80)
        report_lines.append("")
        
        # Executive Summary
        report_lines.append("EXECUTIVE SUMMARY")
        report_lines.append("-" * 80)
        
        key_findings = []
        key_findings.append(f"✓ Total Pages Analyzed: {metrics.get('total_pages', 0)}")
        key_findings.append(f"✓ Navigation Efficiency Score: {metrics.get('navigation_efficiency_score', 0)}/100")
        key_findings.append(f"✓ Site Depth: {metrics.get('site_depth_structure', {}).get('max_depth', 0)} levels")
        key_findings.append(f"✓ Main Sections Identified: {sections.get('content_distribution', {}).get('sections', 0)}")
        
        for finding in key_findings:
            report_lines.append(finding)
        
        report_lines.append("")
        
        # Site Structure Overview
        report_lines.append("SITE STRUCTURE OVERVIEW")
        report_lines.append("-" * 80)
        
        depth_structure = metrics.get('site_depth_structure', {})
        report_lines.append(f"Maximum Depth: {depth_structure.get('max_depth', 0)} levels")
        report_lines.append(f"Average Depth: {depth_structure.get('average_depth', 0):.2f}")
        report_lines.append("")
        report_lines.append("Pages by Depth Level:")
        for depth, count in sorted(depth_structure.get('depth_distribution', {}).items()):
            report_lines.append(f"  Level {depth}: {count} pages")
        
        report_lines.append("")
        report_lines.append(f"Main Sections: {sections.get('content_distribution', {}).get('sections', 0)}")
        report_lines.append(f"Average Pages per Section: {sections.get('content_distribution', {}).get('pages_per_section_avg', 0):.2f}")
        report_lines.append("")
        
        # Navigation Efficiency Assessment
        report_lines.append("NAVIGATION EFFICIENCY ASSESSMENT")
        report_lines.append("-" * 80)
        
        score = metrics.get('navigation_efficiency_score', 0)
        score_breakdown = metrics.get('score_breakdown', {})
        
        report_lines.append(f"Overall Score: {score}/100")
        report_lines.append("")
        report_lines.append("Score Breakdown:")
        report_lines.append(f"  Depth Score: {score_breakdown.get('depth_score', 0):.2f}/25")
        report_lines.append(f"  Link Distribution Score: {score_breakdown.get('link_distribution_score', 0):.2f}/25")
        report_lines.append(f"  Orphan Page Score: {score_breakdown.get('orphan_score', 0):.2f}/25")
        report_lines.append(f"  Connectivity Score: {score_breakdown.get('connectivity_score', 0):.2f}/25")
        report_lines.append("")
        
        # Navigation pattern
        nav_pattern = ia_analysis.get('breadth_vs_depth_analysis', {}).get('navigation_pattern', 'unknown')
        report_lines.append(f"Navigation Pattern: {nav_pattern.upper()}")
        report_lines.append("")
        
        # Top Pages Analysis
        report_lines.append("TOP PAGES ANALYSIS")
        report_lines.append("-" * 80)
        report_lines.append("Most Important Pages (by link count):")
        report_lines.append("")
        
        top_pages = metrics.get('most_important_pages', [])[:5]
        for i, page in enumerate(top_pages, 1):
            report_lines.append(f"{i}. {page.get('title', 'No Title')}")
            report_lines.append(f"   URL: {page.get('url', 'N/A')}")
            report_lines.append(f"   Links: {page.get('link_count', 0)} | Depth: {page.get('depth', 0)}")
            report_lines.append("")
        
        # Recommendations
        report_lines.append("RECOMMENDATIONS FOR BETTER UX")
        report_lines.append("-" * 80)
        
        recommendations = ia_analysis.get('recommendations', [])
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                report_lines.append(f"{i}. {rec}")
        else:
            report_lines.append("No specific recommendations. Site structure appears well-organized.")
        
        report_lines.append("")
        
        # Data Quality Metrics
        report_lines.append("DATA QUALITY METRICS")
        report_lines.append("-" * 80)
        
        total_pages = len(df)
        successful_pages = len(df[df['status_code'] == 200])
        failed_pages = total_pages - successful_pages
        pages_with_titles = len(df[df['title'].notna()])
        pages_with_descriptions = len(df[df['description'].notna()])
        
        report_lines.append(f"Total Pages Crawled: {total_pages}")
        report_lines.append(f"Successfully Fetched: {successful_pages} ({successful_pages/total_pages*100:.1f}%)")
        report_lines.append(f"Failed Fetches: {failed_pages} ({failed_pages/total_pages*100:.1f}%)")
        report_lines.append(f"Pages with Titles: {pages_with_titles} ({pages_with_titles/total_pages*100:.1f}%)")
        report_lines.append(f"Pages with Descriptions: {pages_with_descriptions} ({pages_with_descriptions/total_pages*100:.1f}%)")
        report_lines.append("")
        
        # Visualization Suggestions
        report_lines.append("VISUALIZATION SUGGESTIONS")
        report_lines.append("-" * 80)
        report_lines.append("Recommended visualizations for deeper analysis:")
        report_lines.append("  1. Site hierarchy tree diagram (already generated)")
        report_lines.append("  2. Depth distribution bar chart (already generated)")
        report_lines.append("  3. Section size comparison pie chart")
        report_lines.append("  4. Link network graph with clustering")
        report_lines.append("  5. Navigation flow diagram")
        report_lines.append("  6. Page importance heatmap")
        report_lines.append("")
        
        # Footer
        report_lines.append("=" * 80)
        report_lines.append("Report generated by TSM Website Crawler Analytics Module")
        report_lines.append("=" * 80)
        
        report_text = "\n".join(report_lines)
        
        # Save to file if output path provided
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_text)
            logger.info(f"Insights report saved to {output_path}")
        else:
            # Default output path
            default_path = Path("output/insights_report.txt")
            default_path.parent.mkdir(exist_ok=True)
            with open(default_path, 'w', encoding='utf-8') as f:
                f.write(report_text)
            logger.info(f"Insights report saved to {default_path}")
        
        return report_text
    
    except Exception as e:
        logger.error(f"Error generating insights report: {e}")
        raise


def main():
    """Main execution function for analytics module."""
    csv_file = "output/tsm_crawl_data.csv"
    
    try:
        # Generate comprehensive report
        report = generate_insights_report(csv_file)
        print(report)
        
        # Also save JSON data for programmatic access
        metrics = calculate_site_metrics(csv_file)
        sections = identify_site_sections(csv_file)
        ia_analysis = analyze_information_architecture(csv_file)
        
        analytics_data = {
            "metrics": metrics,
            "sections": sections,
            "information_architecture": ia_analysis
        }
        
        # Convert numpy/pandas types to native Python types for JSON serialization
        def convert_to_native(obj):
            """Recursively convert numpy/pandas types to native Python types."""
            if isinstance(obj, dict):
                return {str(key): convert_to_native(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_native(item) for item in obj]
            elif isinstance(obj, (np.integer, np.int64, np.int32)):
                return int(obj)
            elif isinstance(obj, (np.floating, np.float64, np.float32)):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif pd.isna(obj):
                return None
            elif isinstance(obj, (pd.Int64Dtype, pd.Float64Dtype)):
                return None
            else:
                return obj
        
        analytics_data = convert_to_native(analytics_data)
        
        json_path = Path("output/analytics_data.json")
        json_path.parent.mkdir(exist_ok=True)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(analytics_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Analytics data saved to {json_path}")
        
    except Exception as e:
        logger.error(f"Error in analytics module: {e}")
        raise


if __name__ == "__main__":
    main()

