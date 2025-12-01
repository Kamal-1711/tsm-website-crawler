"""
Product Analytics Module for TSM Website Crawler
=================================================

This module builds on top of the crawl data and analytics to provide
product-style insights: user journeys, content gaps, information
architecture scoring, competitive comparison, and basic SEO audits.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd

from .analytics import calculate_site_metrics

import logging
from urllib.parse import urlparse


logger = logging.getLogger("TSMProductAnalytics")
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
# Internal helpers
# ---------------------------------------------------------------------------


def _load_crawl_df(csv_file: str | Path) -> pd.DataFrame:
    """Load crawl data CSV into a cleaned DataFrame."""
    csv_path = Path(csv_file)
    if not csv_path.exists():
        raise FileNotFoundError(f"Crawl CSV not found: {csv_path}")

    df = pd.read_csv(csv_path)
    if df.empty:
        raise ValueError("Crawl CSV is empty")

    # Normalise core columns
    for col in ("depth", "child_count", "status_code"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    # Ensure string columns are strings
    for col in ("url", "parent_url", "title", "description", "heading"):
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str)

    return df


def _extract_section(url: str) -> str:
    """Extract first path segment as 'section'."""
    try:
        parsed = urlparse(url)
        parts = [p for p in parsed.path.split("/") if p]
        return parts[0] if parts else "home"
    except Exception:
        return "unknown"


def _build_parent_child_graph(df: pd.DataFrame) -> Dict[str, List[str]]:
    """Build a simple parent→children adjacency list from crawl data."""
    graph: Dict[str, List[str]] = defaultdict(list)
    for _, row in df.iterrows():
        parent = row.get("parent_url", "") or ""
        url = row.get("url", "") or ""
        if parent:
            graph[parent].append(url)
    return graph


def _find_home_url(df: pd.DataFrame) -> Optional[str]:
    """Return the root/home URL (depth 0) if present."""
    if "depth" not in df.columns:
        return None
    roots = df[df["depth"] == 0]
    if roots.empty:
        return None
    return str(roots.iloc[0]["url"])


# ---------------------------------------------------------------------------
# 1. User Journey Analysis
# ---------------------------------------------------------------------------


def analyze_user_journey(csv_file: str | Path) -> Dict[str, Any]:
    """
    Perform a structural user-journey style analysis.

    Since we don't have real user sessions, we approximate journeys using
    the crawl tree (parent_url relationships) and typical path lengths.

    Returns:
        {
          "most_common_paths": [...],
          "depth_distribution": {...},
          "exit_pages": [...],
          "exit_stats": {...},
        }
    """
    df = _load_crawl_df(csv_file)
    logger.info("Running user journey analysis")

    graph = _build_parent_child_graph(df)
    home_url = _find_home_url(df)

    # ------------------------------------------------------------------
    # Path analysis – enumerate paths from root up to length 3–4
    # ------------------------------------------------------------------
    paths: List[List[str]] = []

    def dfs(current: str, path: List[str], max_depth: int = 3) -> None:
        if len(path) > max_depth:
            return
        paths.append(path.copy())
        for child in graph.get(current, []):
            if child in path:
                # Avoid cycles just in case
                continue
            dfs(child, path + [child], max_depth=max_depth)

    if home_url:
        dfs(home_url, [home_url], max_depth=3)

    path_counter: Counter[str] = Counter()
    for p in paths:
        if len(p) > 1:
            label = "  ->  ".join(p)
            path_counter[label] += 1

    most_common_paths = [
        {"path": p, "count": c} for p, c in path_counter.most_common(10)
    ]

    # ------------------------------------------------------------------
    # Depth distribution – where do "users" (pages) go?
    # ------------------------------------------------------------------
    depth_distribution = (
        df["depth"].value_counts().sort_index().to_dict()
        if "depth" in df.columns
        else {}
    )

    # ------------------------------------------------------------------
    # Exit points – pages with no children (child_count == 0)
    # ------------------------------------------------------------------
    exits = df[df["child_count"] == 0].copy() if "child_count" in df.columns else df
    exits["section"] = exits["url"].apply(_extract_section)

    exit_points = exits.nlargest(20, "depth")[
        ["url", "title", "depth", "section"]
    ].to_dict("records")

    exit_stats = {
        "total_exits": int(len(exits)),
        "exit_rate": round(len(exits) / len(df) * 100, 2),
        "exits_by_depth": exits["depth"].value_counts().sort_index().to_dict(),
        "exits_by_section": exits["section"].value_counts().to_dict(),
    }

    return {
        "most_common_paths": most_common_paths,
        "depth_distribution": depth_distribution,
        "exit_points": exit_points,
        "exit_stats": exit_stats,
    }


# ---------------------------------------------------------------------------
# 2. Content Gap Analysis
# ---------------------------------------------------------------------------


def content_gap_analysis(csv_file: str | Path) -> Dict[str, Any]:
    """
    Identify structural content gaps and imbalances.

    Returns:
        {
          "orphan_pages": [...],
          "section_stats": {...},
          "imbalanced_sections": {...},
          "recommendations": [...],
        }
    """
    df = _load_crawl_df(csv_file)
    logger.info("Running content gap analysis")

    # Orphan pages: no parent and/or no children
    orphans = df[
        (df["parent_url"] == "")
        | (df["parent_url"].isna())
        | (df["child_count"] == 0)
    ].copy()

    orphan_pages = orphans[
        ["url", "title", "depth", "child_count", "parent_url"]
    ].to_dict("records")

    # Section-level analysis
    df["section"] = df["url"].apply(_extract_section)
    section_group = df.groupby("section")

    section_stats: Dict[str, Dict[str, Any]] = {}
    for section, group in section_group:
        section_stats[section] = {
            "pages": int(len(group)),
            "avg_depth": float(group["depth"].mean()),
            "max_depth": int(group["depth"].max()),
            "avg_child_count": float(group["child_count"].mean()),
        }

    total_pages = len(df)
    avg_pages_per_section = (
        total_pages / len(section_stats) if section_stats else 0
    )

    imbalanced_sections: Dict[str, Dict[str, Any]] = {}
    for name, stats in section_stats.items():
        pages = stats["pages"]
        if pages > avg_pages_per_section * 1.5 or pages < avg_pages_per_section * 0.5:
            imbalance_type = (
                "overrepresented" if pages > avg_pages_per_section else "underrepresented"
            )
            imbalanced_sections[name] = {
                **stats,
                "imbalance_type": imbalance_type,
            }

    recommendations: List[str] = []
    if imbalanced_sections:
        recommendations.append(
            "Rebalance content: some sections have significantly more or fewer "
            "pages than the site average. Consider merging or splitting sections."
        )
    if len(orphan_pages) > 0:
        recommendations.append(
            "Add internal links to orphan pages so users and search engines can "
            "discover them more easily."
        )

    if not recommendations:
        recommendations.append(
            "Content distribution appears reasonably balanced. No major gaps detected."
        )

    return {
        "orphan_pages": orphan_pages,
        "section_stats": section_stats,
        "imbalanced_sections": imbalanced_sections,
        "recommendations": recommendations,
    }


# ---------------------------------------------------------------------------
# 3. Information Architecture Score
# ---------------------------------------------------------------------------


def information_architecture_score(csv_file: str | Path) -> Dict[str, Any]:
    """
    Compute an information architecture (IA) score from 0–100.

    Components:
      - depth_score: shallower hierarchies score higher
      - balance_score: balanced content across sections
      - connectivity_score: good internal linking, few orphans
      - reachability_score: pages within 2–3 clicks from home
    """
    df = _load_crawl_df(csv_file)
    logger.info("Computing information architecture score")

    total_pages = len(df)
    max_depth = int(df["depth"].max()) if "depth" in df.columns else 0
    avg_depth = float(df["depth"].mean()) if "depth" in df.columns else 0.0

    # Depth score (ideal max depth <= 3)
    depth_score = max(0.0, 25.0 - max(0, max_depth - 3) * 6.0)

    # Balance score based on Gini coefficient of page counts per section
    df["section"] = df["url"].apply(_extract_section)
    section_counts = df["section"].value_counts()
    if len(section_counts) > 1:
        values = section_counts.to_numpy(dtype=float)
        values_sorted = np.sort(values)
        n = len(values_sorted)
        cumulative = np.cumsum(values_sorted)
        gini = (n + 1 - 2 * (cumulative / cumulative[-1]).sum()) / n
        balance_score = max(0.0, 25.0 * (1.0 - gini))  # lower Gini is better
    else:
        balance_score = 20.0

    # Connectivity score – combination of orphan ratio and average child_count
    orphan_pages = df[df["child_count"] == 0]
    orphan_ratio = len(orphan_pages) / total_pages if total_pages > 0 else 0
    avg_children = df["child_count"].mean()

    orphan_component = max(0.0, 15.0 - orphan_ratio * 30.0)  # 0–15
    # Ideal avg_children roughly between 5 and 60
    if avg_children <= 0:
        density_component = 0.0
    elif 5 <= avg_children <= 60:
        density_component = 10.0
    else:
        density_component = max(0.0, 10.0 - abs(avg_children - 30.0) / 10.0)

    connectivity_score = orphan_component + density_component

    # Reachability score – percentage of pages within 3 clicks from home
    reachable_within_3 = df[df["depth"] <= 3]
    reach_ratio = len(reachable_within_3) / total_pages if total_pages > 0 else 0
    reachability_score = reach_ratio * 25.0

    total_score = round(
        depth_score + balance_score + connectivity_score + reachability_score, 2
    )

    return {
        "total_score": total_score,
        "max_depth": max_depth,
        "average_depth": round(avg_depth, 2),
        "components": {
            "depth_score": round(depth_score, 2),
            "balance_score": round(balance_score, 2),
            "connectivity_score": round(connectivity_score, 2),
            "reachability_score": round(reachability_score, 2),
        },
        "benchmarks": {
            "ideal_max_depth": 3,
            "ideal_reachability_within_3_clicks": ">= 90%",
            "ideal_orphan_ratio": "< 10%",
        },
    }


# ---------------------------------------------------------------------------
# 4. Competitive Analysis Mode
# ---------------------------------------------------------------------------


def competitive_analysis_mode(
    sites: Dict[str, str | Path],
) -> Dict[str, Any]:
    """
    Compare multiple institutions' structures using existing metrics.

    Args:
        sites: Mapping of site label -> CSV path

    Returns:
        {
          "sites": {name: metrics},
          "rankings": {...},
        }
    """
    logger.info("Running competitive analysis mode")

    site_metrics: Dict[str, Dict[str, Any]] = {}
    for name, csv_path in sites.items():
        try:
            metrics = calculate_site_metrics(str(csv_path))
            ia = information_architecture_score(csv_path)
            site_metrics[name] = {
                "site_metrics": metrics,
                "ia_score": ia,
            }
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Failed to analyse %s: %s", name, exc)

    # Build simple rankings by a few key metrics
    def _get(metric_path: Iterable[str], default: float = 0.0) -> float:
        for name, data in site_metrics.items():
            break
        # metric_path like ["site_metrics", "navigation_efficiency_score"]
        values: List[Tuple[str, float]] = []
        for name, data in site_metrics.items():
            val: Any = data
            for key in metric_path:
                val = val.get(key, {})
            try:
                values.append((name, float(val)))
            except (TypeError, ValueError):
                values.append((name, default))
        # sort descending
        values.sort(key=lambda x: x[1], reverse=True)
        return values

    rankings = {
        "by_navigation_efficiency": _get(["site_metrics", "navigation_efficiency_score"]),
        "by_ia_score": _get(["ia_score", "total_score"]),
        "by_total_pages": _get(["site_metrics", "total_pages"]),
    }

    return {
        "sites": site_metrics,
        "rankings": rankings,
    }


# ---------------------------------------------------------------------------
# 5. SEO Audit Integration
# ---------------------------------------------------------------------------


def seo_audit(csv_file: str | Path) -> Dict[str, Any]:
    """
    Run a lightweight on-site SEO audit based on crawl data.

    Checks:
      - presence of title, meta description, and h1 heading
      - basic URL quality (readability, length, query strings)
      - anchor text quality is approximated by title length/quality,
        since anchor text itself is not stored in the crawl.
    """
    df = _load_crawl_df(csv_file)
    logger.info("Running SEO audit")

    total_pages = len(df)

    missing_title = df["title"].eq("").sum()
    missing_description = df["description"].eq("").sum() if "description" in df else 0
    missing_heading = df["heading"].eq("").sum() if "heading" in df else 0

    # URL quality heuristics
    def url_quality(url: str) -> Dict[str, Any]:
        parsed = urlparse(url)
        path = parsed.path or "/"
        issues: List[str] = []
        if "?" in url:
            issues.append("has_query_string")
        if len(path) > 80:
            issues.append("long_path")
        if "_" in path:
            issues.append("underscores_instead_of_hyphens")
        return {
            "is_lowercase": url == url.lower(),
            "issues": issues,
        }

    url_checks = df["url"].apply(url_quality)
    lowercase_ratio = sum(1 for x in url_checks if x["is_lowercase"]) / total_pages

    issue_counter: Counter[str] = Counter()
    for item in url_checks:
        issue_counter.update(item["issues"])

    # Anchor text quality proxy: pages with very short or generic titles
    bad_title_phrases = {"home", "untitled", "page", "index"}
    short_or_generic_titles = df[
        (df["title"].str.len() < 5)
        | (df["title"].str.lower().isin(bad_title_phrases))
    ]

    return {
        "metadata": {
            "total_pages": total_pages,
            "missing_title": int(missing_title),
            "missing_description": int(missing_description),
            "missing_heading": int(missing_heading),
        },
        "url_quality": {
            "lowercase_ratio": round(lowercase_ratio * 100, 2),
            "issue_counts": dict(issue_counter),
        },
        "anchor_text_proxy": {
            "weak_title_count": int(len(short_or_generic_titles)),
            "weak_title_examples": short_or_generic_titles.head(10)[
                ["url", "title"]
            ].to_dict("records"),
            "note": (
                "Anchor text quality is approximated using page titles, since "
                "individual link anchor text is not available in the crawl data."
            ),
        },
    }


# ---------------------------------------------------------------------------
# Convenience entrypoint
# ---------------------------------------------------------------------------


def generate_product_insights(
    csv_file: str | Path,
    competitors: Optional[Dict[str, str | Path]] = None,
) -> Dict[str, Any]:
    """
    Run all product analytics in one call.

    Args:
        csv_file: Path to main site's crawl CSV.
        competitors: Optional mapping of competitor label -> CSV path.
    """
    insights: Dict[str, Any] = {}

    insights["user_journey"] = analyze_user_journey(csv_file)
    insights["content_gaps"] = content_gap_analysis(csv_file)
    insights["information_architecture"] = information_architecture_score(csv_file)
    insights["seo_audit"] = seo_audit(csv_file)

    if competitors:
        insights["competitive_analysis"] = competitive_analysis_mode(competitors)

    return insights


if __name__ == "__main__":  # pragma: no cover - manual run helper
    # Simple manual test
    default_csv = Path("output/tsm_crawl_data.csv")
    if default_csv.exists():
        import json

        summary = generate_product_insights(default_csv)
        print("=== PRODUCT ANALYTICS SUMMARY (TSM) ===")
        print(json.dumps(summary["information_architecture"], indent=2))
    else:
        print("Crawl CSV not found at", default_csv)

"""
Product Analytics Module for TSM Website Crawler
=================================================

This module builds on top of the crawl data and analytics to provide
product-style insights: user journeys, content gaps, information
architecture scoring, competitive comparison, and basic SEO audits.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd

from .analytics import calculate_site_metrics

import logging
from urllib.parse import urlparse


logger = logging.getLogger("TSMProductAnalytics")
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
# Internal helpers
# ---------------------------------------------------------------------------


def _load_crawl_df(csv_file: str | Path) -> pd.DataFrame:
    """Load crawl data CSV into a cleaned DataFrame."""
    csv_path = Path(csv_file)
    if not csv_path.exists():
        raise FileNotFoundError(f"Crawl CSV not found: {csv_path}")

    df = pd.read_csv(csv_path)
    if df.empty:
        raise ValueError("Crawl CSV is empty")

    # Normalise core columns
    for col in ("depth", "child_count", "status_code"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    # Ensure string columns are strings
    for col in ("url", "parent_url", "title", "description", "heading"):
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str)

    return df


def _extract_section(url: str) -> str:
    """Extract first path segment as 'section'."""
    try:
        parsed = urlparse(url)
        parts = [p for p in parsed.path.split("/") if p]
        return parts[0] if parts else "home"
    except Exception:
        return "unknown"


def _build_parent_child_graph(df: pd.DataFrame) -> Dict[str, List[str]]:
    """Build a simple parent→children adjacency list from crawl data."""
    graph: Dict[str, List[str]] = defaultdict(list)
    for _, row in df.iterrows():
        parent = row.get("parent_url", "") or ""
        url = row.get("url", "") or ""
        if parent:
            graph[parent].append(url)
    return graph


def _find_home_url(df: pd.DataFrame) -> Optional[str]:
    """Return the root/home URL (depth 0) if present."""
    if "depth" not in df.columns:
        return None
    roots = df[df["depth"] == 0]
    if roots.empty:
        return None
    return str(roots.iloc[0]["url"])


# ---------------------------------------------------------------------------
# 1. User Journey Analysis
# ---------------------------------------------------------------------------


def analyze_user_journey(csv_file: str | Path) -> Dict[str, Any]:
    """
    Perform a structural user-journey style analysis.

    Since we don't have real user sessions, we approximate journeys using
    the crawl tree (parent_url relationships) and typical path lengths.

    Returns:
        {
          "most_common_paths": [...],
          "depth_distribution": {...},
          "exit_pages": [...],
          "exit_stats": {...},
        }
    """
    df = _load_crawl_df(csv_file)
    logger.info("Running user journey analysis")

    graph = _build_parent_child_graph(df)
    home_url = _find_home_url(df)

    # ------------------------------------------------------------------
    # Path analysis – enumerate paths from root up to length 3–4
    # ------------------------------------------------------------------
    paths: List[List[str]] = []

    def dfs(current: str, path: List[str], max_depth: int = 3) -> None:
        if len(path) > max_depth:
            return
        paths.append(path.copy())
        for child in graph.get(current, []):
            if child in path:
                # Avoid cycles just in case
                continue
            dfs(child, path + [child], max_depth=max_depth)

    if home_url:
        dfs(home_url, [home_url], max_depth=3)

    path_counter: Counter[str] = Counter()
    for p in paths:
        if len(p) > 1:
            label = "  ->  ".join(p)
            path_counter[label] += 1

    most_common_paths = [
        {"path": p, "count": c} for p, c in path_counter.most_common(10)
    ]

    # ------------------------------------------------------------------
    # Depth distribution – where do "users" (pages) go?
    # ------------------------------------------------------------------
    depth_distribution = (
        df["depth"].value_counts().sort_index().to_dict()
        if "depth" in df.columns
        else {}
    )

    # ------------------------------------------------------------------
    # Exit points – pages with no children (child_count == 0)
    # ------------------------------------------------------------------
    exits = df[df["child_count"] == 0].copy() if "child_count" in df.columns else df
    exits["section"] = exits["url"].apply(_extract_section)

    exit_points = exits.nlargest(20, "depth")[
        ["url", "title", "depth", "section"]
    ].to_dict("records")

    exit_stats = {
        "total_exits": int(len(exits)),
        "exit_rate": round(len(exits) / len(df) * 100, 2),
        "exits_by_depth": exits["depth"].value_counts().sort_index().to_dict(),
        "exits_by_section": exits["section"].value_counts().to_dict(),
    }

    return {
        "most_common_paths": most_common_paths,
        "depth_distribution": depth_distribution,
        "exit_points": exit_points,
        "exit_stats": exit_stats,
    }


# ---------------------------------------------------------------------------
# 2. Content Gap Analysis
# ---------------------------------------------------------------------------


def content_gap_analysis(csv_file: str | Path) -> Dict[str, Any]:
    """
    Identify structural content gaps and imbalances.

    Returns:
        {
          "orphan_pages": [...],
          "section_stats": {...},
          "imbalanced_sections": {...},
          "recommendations": [...],
        }
    """
    df = _load_crawl_df(csv_file)
    logger.info("Running content gap analysis")

    # Orphan pages: no parent and/or no children
    orphans = df[
        (df["parent_url"] == "")
        | (df["parent_url"].isna())
        | (df["child_count"] == 0)
    ].copy()

    orphan_pages = orphans[
        ["url", "title", "depth", "child_count", "parent_url"]
    ].to_dict("records")

    # Section-level analysis
    df["section"] = df["url"].apply(_extract_section)
    section_group = df.groupby("section")

    section_stats: Dict[str, Dict[str, Any]] = {}
    for section, group in section_group:
        section_stats[section] = {
            "pages": int(len(group)),
            "avg_depth": float(group["depth"].mean()),
            "max_depth": int(group["depth"].max()),
            "avg_child_count": float(group["child_count"].mean()),
        }

    total_pages = len(df)
    avg_pages_per_section = (
        total_pages / len(section_stats) if section_stats else 0
    )

    imbalanced_sections: Dict[str, Dict[str, Any]] = {}
    for name, stats in section_stats.items():
        pages = stats["pages"]
        if pages > avg_pages_per_section * 1.5 or pages < avg_pages_per_section * 0.5:
            imbalance_type = (
                "overrepresented" if pages > avg_pages_per_section else "underrepresented"
            )
            imbalanced_sections[name] = {
                **stats,
                "imbalance_type": imbalance_type,
            }

    recommendations: List[str] = []
    if imbalanced_sections:
        recommendations.append(
            "Rebalance content: some sections have significantly more or fewer "
            "pages than the site average. Consider merging or splitting sections."
        )
    if len(orphan_pages) > 0:
        recommendations.append(
            "Add internal links to orphan pages so users and search engines can "
            "discover them more easily."
        )

    if not recommendations:
        recommendations.append(
            "Content distribution appears reasonably balanced. No major gaps detected."
        )

    return {
        "orphan_pages": orphan_pages,
        "section_stats": section_stats,
        "imbalanced_sections": imbalanced_sections,
        "recommendations": recommendations,
    }


# ---------------------------------------------------------------------------
# 3. Information Architecture Score
# ---------------------------------------------------------------------------


def information_architecture_score(csv_file: str | Path) -> Dict[str, Any]:
    """
    Compute an information architecture (IA) score from 0–100.

    Components:
      - depth_score: shallower hierarchies score higher
      - balance_score: balanced content across sections
      - connectivity_score: good internal linking, few orphans
      - reachability_score: pages within 2–3 clicks of home
    """
    df = _load_crawl_df(csv_file)
    logger.info("Computing information architecture score")

    total_pages = len(df)
    max_depth = int(df["depth"].max()) if "depth" in df.columns else 0
    avg_depth = float(df["depth"].mean()) if "depth" in df.columns else 0.0

    # Depth score (ideal max depth <= 3)
    depth_score = max(0.0, 25.0 - max(0, max_depth - 3) * 6.0)

    # Balance score based on Gini coefficient of page counts per section
    df["section"] = df["url"].apply(_extract_section)
    section_counts = df["section"].value_counts()
    if len(section_counts) > 1:
        values = section_counts.to_numpy(dtype=float)
        values_sorted = np.sort(values)
        n = len(values_sorted)
        cumulative = np.cumsum(values_sorted)
        gini = (n + 1 - 2 * (cumulative / cumulative[-1]).sum()) / n
        balance_score = max(0.0, 25.0 * (1.0 - gini))  # lower Gini is better
    else:
        balance_score = 20.0

    # Connectivity score – combination of orphan ratio and average child_count
    orphan_pages = df[df["child_count"] == 0]
    orphan_ratio = len(orphan_pages) / total_pages if total_pages > 0 else 0
    avg_children = df["child_count"].mean()

    orphan_component = max(0.0, 15.0 - orphan_ratio * 30.0)  # 0–15
    # Ideal avg_children roughly between 5 and 60
    if avg_children <= 0:
        density_component = 0.0
    elif 5 <= avg_children <= 60:
        density_component = 10.0
    else:
        density_component = max(0.0, 10.0 - abs(avg_children - 30.0) / 10.0)

    connectivity_score = orphan_component + density_component

    # Reachability score – percentage of pages within 3 clicks from home
    reachable_within_3 = df[df["depth"] <= 3]
    reach_ratio = len(reachable_within_3) / total_pages if total_pages > 0 else 0
    reachability_score = reach_ratio * 25.0

    total_score = round(
        depth_score + balance_score + connectivity_score + reachability_score, 2
    )

    return {
        "total_score": total_score,
        "max_depth": max_depth,
        "average_depth": round(avg_depth, 2),
        "components": {
            "depth_score": round(depth_score, 2),
            "balance_score": round(balance_score, 2),
            "connectivity_score": round(connectivity_score, 2),
            "reachability_score": round(reachability_score, 2),
        },
        "benchmarks": {
            "ideal_max_depth": 3,
            "ideal_reachability_within_3_clicks": ">= 90%",
            "ideal_orphan_ratio": "< 10%",
        },
    }


# ---------------------------------------------------------------------------
# 4. Competitive Analysis Mode
# ---------------------------------------------------------------------------


def competitive_analysis_mode(
    sites: Dict[str, str | Path],
) -> Dict[str, Any]:
    """
    Compare multiple institutions' structures using existing metrics.

    Args:
        sites: Mapping of site label -> CSV path

    Returns:
        {
          "sites": {name: metrics},
          "rankings": {...},
        }
    """
    logger.info("Running competitive analysis mode")

    site_metrics: Dict[str, Dict[str, Any]] = {}
    for name, csv_path in sites.items():
        try:
            metrics = calculate_site_metrics(str(csv_path))
            ia = information_architecture_score(csv_path)
            site_metrics[name] = {
                "site_metrics": metrics,
                "ia_score": ia,
            }
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Failed to analyse %s: %s", name, exc)

    # Build simple rankings by a few key metrics
    def _get(metric_path: Iterable[str], default: float = 0.0) -> float:
        for name, data in site_metrics.items():
            break
        # metric_path like ["site_metrics", "navigation_efficiency_score"]
        values: List[Tuple[str, float]] = []
        for name, data in site_metrics.items():
            val: Any = data
            for key in metric_path:
                val = val.get(key, {})
            try:
                values.append((name, float(val)))
            except (TypeError, ValueError):
                values.append((name, default))
        # sort descending
        values.sort(key=lambda x: x[1], reverse=True)
        return values

    rankings = {
        "by_navigation_efficiency": _get(["site_metrics", "navigation_efficiency_score"]),
        "by_ia_score": _get(["ia_score", "total_score"]),
        "by_total_pages": _get(["site_metrics", "total_pages"]),
    }

    return {
        "sites": site_metrics,
        "rankings": rankings,
    }


# ---------------------------------------------------------------------------
# 5. SEO Audit Integration
# ---------------------------------------------------------------------------


def seo_audit(csv_file: str | Path) -> Dict[str, Any]:
    """
    Run a lightweight on-site SEO audit based on crawl data.

    Checks:
      - presence of title, meta description, and h1 heading
      - basic URL quality (readability, length, query strings)
      - anchor text quality is approximated by title length/quality,
        since anchor text itself is not stored in the crawl.
    """
    df = _load_crawl_df(csv_file)
    logger.info("Running SEO audit")

    total_pages = len(df)

    missing_title = df["title"].eq("").sum()
    missing_description = df["description"].eq("").sum() if "description" in df else 0
    missing_heading = df["heading"].eq("").sum() if "heading" in df else 0

    # URL quality heuristics
    def url_quality(url: str) -> Dict[str, Any]:
        parsed = urlparse(url)
        path = parsed.path or "/"
        issues: List[str] = []
        if "?" in url:
            issues.append("has_query_string")
        if len(path) > 80:
            issues.append("long_path")
        if "_" in path:
            issues.append("underscores_instead_of_hyphens")
        return {
            "is_lowercase": url == url.lower(),
            "issues": issues,
        }

    url_checks = df["url"].apply(url_quality)
    lowercase_ratio = sum(1 for x in url_checks if x["is_lowercase"]) / total_pages

    issue_counter: Counter[str] = Counter()
    for item in url_checks:
        issue_counter.update(item["issues"])

    # Anchor text quality proxy: pages with very short or generic titles
    bad_title_phrases = {"home", "untitled", "page", "index"}
    short_or_generic_titles = df[
        (df["title"].str.len() < 5)
        | (df["title"].str.lower().isin(bad_title_phrases))
    ]

    return {
        "metadata": {
            "total_pages": total_pages,
            "missing_title": int(missing_title),
            "missing_description": int(missing_description),
            "missing_heading": int(missing_heading),
        },
        "url_quality": {
            "lowercase_ratio": round(lowercase_ratio * 100, 2),
            "issue_counts": dict(issue_counter),
        },
        "anchor_text_proxy": {
            "weak_title_count": int(len(short_or_generic_titles)),
            "weak_title_examples": short_or_generic_titles.head(10)[
                ["url", "title"]
            ].to_dict("records"),
            "note": (
                "Anchor text quality is approximated using page titles, since "
                "individual link anchor text is not available in the crawl data."
            ),
        },
    }


# ---------------------------------------------------------------------------
# Convenience entrypoint
# ---------------------------------------------------------------------------


def generate_product_insights(
    csv_file: str | Path,
    competitors: Optional[Dict[str, str | Path]] = None,
) -> Dict[str, Any]:
    """
    Run all product analytics in one call.

    Args:
        csv_file: Path to main site's crawl CSV.
        competitors: Optional mapping of competitor label -> CSV path.
    """
    insights: Dict[str, Any] = {}

    insights["user_journey"] = analyze_user_journey(csv_file)
    insights["content_gaps"] = content_gap_analysis(csv_file)
    insights["information_architecture"] = information_architecture_score(csv_file)
    insights["seo_audit"] = seo_audit(csv_file)

    if competitors:
        insights["competitive_analysis"] = competitive_analysis_mode(competitors)

    return insights


if __name__ == "__main__":  # pragma: no cover - manual run helper
    # Simple manual test
    default_csv = Path("output/tsm_crawl_data.csv")
    if default_csv.exists():
        summary = generate_product_insights(default_csv)
        print("=== PRODUCT ANALYTICS SUMMARY (TSM) ===")
        print(json.dumps(summary["information_architecture"], indent=2))
    else:
        print("Crawl CSV not found at", default_csv)


