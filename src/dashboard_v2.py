"""
TSM Website Structure Analysis Dashboard (v2)
==============================================

A comprehensive Flask-based interactive dashboard that integrates:
- Audit report insights
- Network hierarchy visualization
- Depth distribution charts
- Statistics and analytics

Author: TSM Web Crawler Project
"""

from __future__ import annotations

import json
import logging
import os
import statistics as stats_module
from datetime import datetime
from io import BytesIO, StringIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import networkx as nx
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from flask import Flask, Response, jsonify, render_template_string, request, send_file

# Import audit report generator
from src.audit_report import AuditReportGenerator

# ---------------------------------------------------------------------------
# Logging Setup
# ---------------------------------------------------------------------------

logger = logging.getLogger("TSMDashboard")
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
# Flask App Setup
# ---------------------------------------------------------------------------

app = Flask(__name__, static_folder="static")

# Enable CORS for future API integrations
try:
    from flask_cors import CORS
    CORS(app)
except ImportError:
    logger.warning("flask-cors not installed. CORS not enabled.")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CSV_FILE_PATH = Path(__file__).parent.parent / "output" / "tsm_crawl_data.csv"
REPORT_OUTPUT_PATH = Path(__file__).parent.parent / "output" / "TSM_Website_Audit_Report.txt"

# ---------------------------------------------------------------------------
# Data Loading Functions
# ---------------------------------------------------------------------------


def load_crawl_data() -> pd.DataFrame:
    """Load crawl data from CSV file."""
    if not CSV_FILE_PATH.exists():
        logger.error(f"CSV file not found: {CSV_FILE_PATH}")
        return pd.DataFrame()

    df = pd.read_csv(CSV_FILE_PATH)

    # Normalize columns
    for col in ("depth", "child_count", "status_code"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    for col in ("url", "parent_url", "title", "description", "heading"):
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str)

    return df


def load_dashboard_data() -> Dict[str, Any]:
    """
    Load all data at startup.
    
    Returns:
        Dictionary containing:
        - df_crawl: pandas DataFrame from CSV
        - audit_data: dictionary from audit report
        - graph: NetworkX graph object
        - stats: dictionary of statistics
    """
    df = load_crawl_data()
    
    if df.empty:
        return {
            "df_crawl": df,
            "audit_data": {},
            "graph": nx.DiGraph(),
            "stats": {},
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    # Generate audit data
    try:
        auditor = AuditReportGenerator(str(CSV_FILE_PATH))
        audit_data = {
            "ia_score": auditor.calculate_ia_score(),
            "orphan_pages": auditor.identify_orphan_pages(),
            "dead_ends": auditor.identify_dead_ends(),
            "content_distribution": auditor.analyze_content_distribution(),
            "bottlenecks": auditor.find_navigation_bottlenecks(),
            "top_pages": auditor.get_top_pages(10),
            "depth_analysis": auditor.get_depth_analysis(),
            "user_journey": auditor.analyze_user_journey(),
            "recommendations": auditor.generate_recommendations(),
        }
    except Exception as e:
        logger.error(f"Error generating audit data: {e}")
        audit_data = {}

    # Build NetworkX graph
    graph = nx.DiGraph()
    for _, row in df.iterrows():
        url = row["url"]
        parent = row.get("parent_url", "")
        graph.add_node(
            url,
            title=row.get("title", ""),
            depth=int(row.get("depth", 0)),
            child_count=int(row.get("child_count", 0)),
            status_code=int(row.get("status_code", 200)),
        )
        if parent:
            graph.add_edge(parent, url)

    # Calculate statistics
    stats = {
        "total_pages": len(df),
        "avg_depth": round(df["depth"].mean(), 2) if len(df) > 0 else 0,
        "max_depth": int(df["depth"].max()) if len(df) > 0 else 0,
        "avg_links": round(df["child_count"].mean(), 1) if len(df) > 0 else 0,
        "total_links": int(df["child_count"].sum()) if len(df) > 0 else 0,
        "pages_by_depth": df["depth"].value_counts().sort_index().to_dict() if len(df) > 0 else {},
        "pages_by_status": df["status_code"].value_counts().to_dict() if "status_code" in df.columns else {},
    }

    return {
        "df_crawl": df,
        "audit_data": audit_data,
        "graph": graph,
        "stats": stats,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


# Global data cache
_dashboard_data: Optional[Dict[str, Any]] = None


def get_dashboard_data() -> Dict[str, Any]:
    """Get cached dashboard data or load it."""
    global _dashboard_data
    if _dashboard_data is None:
        _dashboard_data = load_dashboard_data()
    return _dashboard_data


def refresh_dashboard_data() -> Dict[str, Any]:
    """Force refresh of dashboard data."""
    global _dashboard_data
    _dashboard_data = load_dashboard_data()
    return _dashboard_data


# ---------------------------------------------------------------------------
# Visualization Functions
# ---------------------------------------------------------------------------


def create_network_graph_plotly(df: pd.DataFrame, max_nodes: int = 100) -> str:
    """
    Create an interactive network graph using Plotly.
    
    Args:
        df: DataFrame with crawl data
        max_nodes: Maximum number of nodes to display
        
    Returns:
        Plotly figure as JSON string
    """
    if df.empty:
        return "{}"

    # Limit nodes for performance
    df_limited = df.head(max_nodes)

    # Build graph
    G = nx.DiGraph()
    for _, row in df_limited.iterrows():
        url = row["url"]
        parent = row.get("parent_url", "")
        G.add_node(url, **{
            "title": row.get("title", ""),
            "depth": int(row.get("depth", 0)),
            "child_count": int(row.get("child_count", 0)),
        })
        if parent and parent in [r["url"] for _, r in df_limited.iterrows()]:
            G.add_edge(parent, url)

    # Use spring layout
    try:
        pos = nx.spring_layout(G, k=2, iterations=50, seed=42)
    except Exception:
        pos = {node: (i % 10, i // 10) for i, node in enumerate(G.nodes())}

    # Create edge traces
    edge_x = []
    edge_y = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        line=dict(width=0.5, color="#888"),
        hoverinfo="none",
        mode="lines",
    )

    # Create node traces
    node_x = []
    node_y = []
    node_text = []
    node_color = []
    node_size = []

    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)

        data = G.nodes[node]
        title = data.get("title", "No Title")[:40]
        depth = data.get("depth", 0)
        children = data.get("child_count", 0)

        node_text.append(f"<b>{title}</b><br>URL: {node[:50]}...<br>Depth: {depth}<br>Links: {children}")
        node_color.append(depth)
        node_size.append(max(10, min(50, 10 + children * 0.5)))

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers",
        hoverinfo="text",
        text=node_text,
        marker=dict(
            showscale=True,
            colorscale="Blues",
            reversescale=True,
            color=node_color,
            size=node_size,
            colorbar=dict(
                thickness=15,
                title=dict(text="Depth", side="right"),
                xanchor="left",
            ),
            line=dict(width=2, color="#fff"),
        ),
    )

    fig = go.Figure(
        data=[edge_trace, node_trace],
        layout=go.Layout(
            title=dict(text="Website Structure Network", font=dict(size=16)),
            showlegend=False,
            hovermode="closest",
            margin=dict(b=20, l=5, r=5, t=40),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        ),
    )

    return fig.to_json()


def create_depth_bar_chart(stats: Dict[str, Any]) -> str:
    """Create a bar chart showing pages per depth level."""
    pages_by_depth = stats.get("pages_by_depth", {})

    if not pages_by_depth:
        return "{}"

    depths = list(pages_by_depth.keys())
    counts = list(pages_by_depth.values())

    fig = go.Figure(
        data=[
            go.Bar(
                x=[f"Depth {d}" for d in depths],
                y=counts,
                marker_color=["#3B82F6" if d <= 3 else "#F59E0B" if d <= 4 else "#EF4444" for d in depths],
                text=counts,
                textposition="auto",
            )
        ],
        layout=go.Layout(
            title=dict(text="Pages by Depth Level", font=dict(size=14)),
            xaxis_title="Depth Level",
            yaxis_title="Number of Pages",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=40, r=20, t=40, b=40),
        ),
    )

    return fig.to_json()


def create_section_pie_chart(audit_data: Dict[str, Any]) -> str:
    """Create a pie chart showing content distribution by section."""
    content_dist = audit_data.get("content_distribution", {})
    sections = content_dist.get("sections", [])

    if not sections:
        return "{}"

    # Take top 10 sections
    top_sections = sections[:10]
    labels = [s["name"] for s in top_sections]
    values = [s["page_count"] for s in top_sections]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.4,
                textinfo="label+percent",
                textposition="outside",
                marker=dict(
                    colors=px.colors.qualitative.Set3[:len(labels)],
                ),
            )
        ],
        layout=go.Layout(
            title=dict(text="Content Distribution by Section", font=dict(size=14)),
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.2),
            margin=dict(l=20, r=20, t=40, b=60),
            paper_bgcolor="rgba(0,0,0,0)",
        ),
    )

    return fig.to_json()


def create_status_code_chart(stats: Dict[str, Any]) -> str:
    """Create a bar chart showing pages by status code."""
    pages_by_status = stats.get("pages_by_status", {})

    if not pages_by_status:
        return "{}"

    statuses = [str(s) for s in pages_by_status.keys()]
    counts = list(pages_by_status.values())

    colors = []
    for s in pages_by_status.keys():
        if s == 200:
            colors.append("#10B981")
        elif 300 <= s < 400:
            colors.append("#F59E0B")
        else:
            colors.append("#EF4444")

    fig = go.Figure(
        data=[
            go.Bar(
                x=statuses,
                y=counts,
                marker_color=colors,
                text=counts,
                textposition="auto",
            )
        ],
        layout=go.Layout(
            title=dict(text="Pages by Status Code", font=dict(size=14)),
            xaxis_title="Status Code",
            yaxis_title="Number of Pages",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=40, r=20, t=40, b=40),
        ),
    )

    return fig.to_json()


# ---------------------------------------------------------------------------
# HTML Template
# ---------------------------------------------------------------------------

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TSM Website Structure Dashboard</title>
    
    <!-- Plotly.js -->
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    
    <!-- Google Fonts -->
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    
    <style>
        :root {
            --primary: #3B82F6;
            --primary-dark: #2563EB;
            --danger: #EF4444;
            --success: #10B981;
            --warning: #F59E0B;
            --gray-50: #F9FAFB;
            --gray-100: #F3F4F6;
            --gray-200: #E5E7EB;
            --gray-300: #D1D5DB;
            --gray-400: #9CA3AF;
            --gray-500: #6B7280;
            --gray-600: #4B5563;
            --gray-700: #374151;
            --gray-800: #1F2937;
            --gray-900: #111827;
            --bg-primary: #F9FAFB;
            --bg-card: #FFFFFF;
            --text-primary: #111827;
            --text-secondary: #6B7280;
            --border: #E5E7EB;
            --shadow: 0 1px 3px rgba(0,0,0,0.1), 0 1px 2px rgba(0,0,0,0.06);
            --shadow-lg: 0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05);
        }
        
        .dark {
            --bg-primary: #111827;
            --bg-card: #1F2937;
            --text-primary: #F9FAFB;
            --text-secondary: #9CA3AF;
            --border: #374151;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background-color: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            transition: background-color 0.3s, color 0.3s;
        }
        
        /* Header */
        .header {
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: white;
            padding: 1.5rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 1rem;
        }
        
        .header-title h1 {
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 0.25rem;
        }
        
        .header-title p {
            font-size: 0.875rem;
            opacity: 0.9;
        }
        
        .header-actions {
            display: flex;
            gap: 0.75rem;
            align-items: center;
        }
        
        .btn {
            padding: 0.5rem 1rem;
            border-radius: 0.5rem;
            font-size: 0.875rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
            border: none;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .btn-primary {
            background: white;
            color: var(--primary);
        }
        
        .btn-primary:hover {
            background: var(--gray-100);
        }
        
        .btn-secondary {
            background: rgba(255,255,255,0.2);
            color: white;
        }
        
        .btn-secondary:hover {
            background: rgba(255,255,255,0.3);
        }
        
        .theme-toggle {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: rgba(255,255,255,0.2);
            border: none;
            color: white;
            cursor: pointer;
            font-size: 1.25rem;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: background 0.2s;
        }
        
        .theme-toggle:hover {
            background: rgba(255,255,255,0.3);
        }
        
        /* Navigation Tabs */
        .nav-tabs {
            background: var(--bg-card);
            border-bottom: 1px solid var(--border);
            padding: 0 2rem;
            display: flex;
            gap: 0;
            overflow-x: auto;
        }
        
        .nav-tab {
            padding: 1rem 1.5rem;
            font-size: 0.875rem;
            font-weight: 500;
            color: var(--text-secondary);
            cursor: pointer;
            border-bottom: 2px solid transparent;
            transition: all 0.2s;
            white-space: nowrap;
        }
        
        .nav-tab:hover {
            color: var(--primary);
        }
        
        .nav-tab.active {
            color: var(--primary);
            border-bottom-color: var(--primary);
        }
        
        /* Main Content */
        .main-content {
            padding: 1.5rem 2rem;
            max-width: 1600px;
            margin: 0 auto;
        }
        
        /* Summary Cards */
        .summary-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 1.5rem;
        }
        
        .card {
            background: var(--bg-card);
            border-radius: 0.75rem;
            padding: 1.25rem;
            box-shadow: var(--shadow);
            border: 1px solid var(--border);
            transition: box-shadow 0.2s, transform 0.2s;
        }
        
        .card:hover {
            box-shadow: var(--shadow-lg);
            transform: translateY(-2px);
        }
        
        .card-label {
            font-size: 0.75rem;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-secondary);
            margin-bottom: 0.5rem;
        }
        
        .card-value {
            font-size: 2rem;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 0.25rem;
        }
        
        .card-subtext {
            font-size: 0.75rem;
            color: var(--text-secondary);
        }
        
        .card-value.success { color: var(--success); }
        .card-value.warning { color: var(--warning); }
        .card-value.danger { color: var(--danger); }
        
        /* Tab Content */
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
        
        /* Grid Layouts */
        .grid-2 {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 1.5rem;
        }
        
        .grid-3 {
            display: grid;
            grid-template-columns: 30% 40% 30%;
            gap: 1.5rem;
        }
        
        @media (max-width: 1024px) {
            .grid-2, .grid-3 {
                grid-template-columns: 1fr;
            }
        }
        
        /* Chart Container */
        .chart-container {
            background: var(--bg-card);
            border-radius: 0.75rem;
            padding: 1rem;
            box-shadow: var(--shadow);
            border: 1px solid var(--border);
            min-height: 400px;
        }
        
        .chart-container.large {
            min-height: 600px;
        }
        
        /* Data Table */
        .data-table-container {
            background: var(--bg-card);
            border-radius: 0.75rem;
            box-shadow: var(--shadow);
            border: 1px solid var(--border);
            overflow: hidden;
        }
        
        .table-controls {
            padding: 1rem;
            display: flex;
            gap: 1rem;
            flex-wrap: wrap;
            align-items: center;
            border-bottom: 1px solid var(--border);
        }
        
        .search-input {
            flex: 1;
            min-width: 200px;
            padding: 0.5rem 1rem;
            border: 1px solid var(--border);
            border-radius: 0.5rem;
            font-size: 0.875rem;
            background: var(--bg-primary);
            color: var(--text-primary);
        }
        
        .filter-select {
            padding: 0.5rem 1rem;
            border: 1px solid var(--border);
            border-radius: 0.5rem;
            font-size: 0.875rem;
            background: var(--bg-primary);
            color: var(--text-primary);
        }
        
        .data-table {
            width: 100%;
            border-collapse: collapse;
        }
        
        .data-table th,
        .data-table td {
            padding: 0.75rem 1rem;
            text-align: left;
            border-bottom: 1px solid var(--border);
            font-size: 0.875rem;
        }
        
        .data-table th {
            background: var(--bg-primary);
            font-weight: 600;
            color: var(--text-secondary);
            cursor: pointer;
            user-select: none;
        }
        
        .data-table th:hover {
            background: var(--gray-200);
        }
        
        .dark .data-table th:hover {
            background: var(--gray-700);
        }
        
        .data-table tbody tr:hover {
            background: var(--gray-50);
        }
        
        .dark .data-table tbody tr:hover {
            background: var(--gray-800);
        }
        
        .data-table .url-cell {
            max-width: 300px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        
        .pagination {
            padding: 1rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-top: 1px solid var(--border);
        }
        
        .pagination-info {
            font-size: 0.875rem;
            color: var(--text-secondary);
        }
        
        .pagination-controls {
            display: flex;
            gap: 0.5rem;
        }
        
        .page-btn {
            padding: 0.5rem 0.75rem;
            border: 1px solid var(--border);
            border-radius: 0.375rem;
            background: var(--bg-card);
            color: var(--text-primary);
            cursor: pointer;
            font-size: 0.875rem;
        }
        
        .page-btn:hover:not(:disabled) {
            background: var(--gray-100);
        }
        
        .page-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .page-btn.active {
            background: var(--primary);
            color: white;
            border-color: var(--primary);
        }
        
        /* Audit Report Section */
        .report-section {
            background: var(--bg-card);
            border-radius: 0.75rem;
            box-shadow: var(--shadow);
            border: 1px solid var(--border);
            margin-bottom: 1rem;
        }
        
        .report-header {
            padding: 1rem 1.25rem;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
            cursor: pointer;
        }
        
        .report-header h3 {
            font-size: 1rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .report-content {
            padding: 1.25rem;
            display: none;
        }
        
        .report-section.expanded .report-content {
            display: block;
        }
        
        .report-section.expanded .expand-icon {
            transform: rotate(180deg);
        }
        
        .expand-icon {
            transition: transform 0.2s;
        }
        
        /* Metrics Grid */
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
            margin-bottom: 1rem;
        }
        
        .metric-item {
            text-align: center;
            padding: 1rem;
            background: var(--bg-primary);
            border-radius: 0.5rem;
        }
        
        .metric-value {
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--primary);
        }
        
        .metric-label {
            font-size: 0.75rem;
            color: var(--text-secondary);
            margin-top: 0.25rem;
        }
        
        /* Issue List */
        .issue-list {
            list-style: none;
        }
        
        .issue-item {
            padding: 0.75rem 1rem;
            border-left: 3px solid var(--warning);
            background: var(--bg-primary);
            margin-bottom: 0.5rem;
            border-radius: 0 0.5rem 0.5rem 0;
        }
        
        .issue-item.critical {
            border-left-color: var(--danger);
        }
        
        .issue-item.success {
            border-left-color: var(--success);
        }
        
        /* Recommendations */
        .recommendation-list {
            list-style: none;
        }
        
        .recommendation-item {
            padding: 1rem;
            background: var(--bg-primary);
            border-radius: 0.5rem;
            margin-bottom: 0.75rem;
            border: 1px solid var(--border);
        }
        
        .recommendation-priority {
            display: inline-block;
            padding: 0.25rem 0.5rem;
            border-radius: 0.25rem;
            font-size: 0.75rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }
        
        .priority-critical {
            background: var(--danger);
            color: white;
        }
        
        .priority-important {
            background: var(--warning);
            color: white;
        }
        
        .priority-nice {
            background: var(--success);
            color: white;
        }
        
        /* Status Badge */
        .status-badge {
            display: inline-block;
            padding: 0.25rem 0.5rem;
            border-radius: 0.25rem;
            font-size: 0.75rem;
            font-weight: 500;
        }
        
        .status-success {
            background: rgba(16, 185, 129, 0.1);
            color: var(--success);
        }
        
        .status-warning {
            background: rgba(245, 158, 11, 0.1);
            color: var(--warning);
        }
        
        .status-danger {
            background: rgba(239, 68, 68, 0.1);
            color: var(--danger);
        }
        
        /* Footer */
        .footer {
            padding: 1.5rem 2rem;
            text-align: center;
            color: var(--text-secondary);
            font-size: 0.875rem;
            border-top: 1px solid var(--border);
            margin-top: 2rem;
        }
        
        /* Loading Spinner */
        .loading {
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 3rem;
        }
        
        .spinner {
            width: 40px;
            height: 40px;
            border: 3px solid var(--border);
            border-top-color: var(--primary);
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .header {
                padding: 1rem;
            }
            
            .header-title h1 {
                font-size: 1.25rem;
            }
            
            .main-content {
                padding: 1rem;
            }
            
            .nav-tabs {
                padding: 0 1rem;
            }
            
            .nav-tab {
                padding: 0.75rem 1rem;
            }
        }
        
        /* Scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: var(--bg-primary);
        }
        
        ::-webkit-scrollbar-thumb {
            background: var(--gray-400);
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: var(--gray-500);
        }
    </style>
</head>
<body>
    <!-- Header -->
    <header class="header">
        <div class="header-title">
            <h1>🌐 TSM Website Structure Dashboard</h1>
            <p>Comprehensive Website Audit & Insights</p>
        </div>
        <div class="header-actions">
            <span style="font-size: 0.75rem; opacity: 0.8;">Last Updated: {{ timestamp }}</span>
            <button class="btn btn-secondary" onclick="refreshData()">
                🔄 Refresh
            </button>
            <button class="btn btn-primary" onclick="exportReport()">
                📥 Export Report
            </button>
            <button class="theme-toggle" onclick="toggleTheme()" title="Toggle Dark Mode">
                🌙
            </button>
        </div>
    </header>
    
    <!-- Navigation Tabs -->
    <nav class="nav-tabs">
        <div class="nav-tab active" data-tab="overview">📊 Overview</div>
        <div class="nav-tab" data-tab="network">🕸️ Network</div>
        <div class="nav-tab" data-tab="statistics">📈 Statistics</div>
        <div class="nav-tab" data-tab="audit">📋 Audit Report</div>
        <div class="nav-tab" data-tab="data">📁 Data Table</div>
    </nav>
    
    <!-- Main Content -->
    <main class="main-content">
        <!-- Summary Cards -->
        <div class="summary-cards">
            <div class="card">
                <div class="card-label">Total Pages</div>
                <div class="card-value">{{ stats.total_pages }}</div>
                <div class="card-subtext">Comprehensive crawl</div>
            </div>
            <div class="card">
                <div class="card-label">Architecture Score</div>
                <div class="card-value {{ 'success' if ia_score.final_score >= 75 else 'warning' if ia_score.final_score >= 50 else 'danger' }}">
                    {{ ia_score.final_score }}/100
                </div>
                <div class="card-subtext">{{ ia_score.health_status }}</div>
            </div>
            <div class="card">
                <div class="card-label">Average Depth</div>
                <div class="card-value {{ 'success' if stats.avg_depth <= 3 else 'warning' if stats.avg_depth <= 4 else 'danger' }}">
                    {{ stats.avg_depth }}
                </div>
                <div class="card-subtext">{{ 'Optimal' if stats.avg_depth <= 4 else 'Needs Optimization' }}</div>
            </div>
            <div class="card">
                <div class="card-label">Health Status</div>
                <div class="card-value {{ 'success' if ia_score.health_status == 'Excellent' or ia_score.health_status == 'Good' else 'warning' if ia_score.health_status == 'Needs Improvement' else 'danger' }}">
                    {{ ia_score.health_status }}
                </div>
                <div class="card-subtext">Based on composite score</div>
            </div>
        </div>
        
        <!-- Tab: Overview -->
        <div class="tab-content active" id="tab-overview">
            <div class="grid-3">
                <!-- Left Column -->
                <div>
                    <div class="card" style="margin-bottom: 1rem;">
                        <h3 style="font-size: 1rem; font-weight: 600; margin-bottom: 1rem;">📊 Key Metrics</h3>
                        <div class="metrics-grid">
                            <div class="metric-item">
                                <div class="metric-value">{{ stats.max_depth }}</div>
                                <div class="metric-label">Max Depth</div>
                            </div>
                            <div class="metric-item">
                                <div class="metric-value">{{ stats.avg_links }}</div>
                                <div class="metric-label">Avg Links</div>
                            </div>
                            <div class="metric-item">
                                <div class="metric-value">{{ orphan_count }}</div>
                                <div class="metric-label">Orphan Pages</div>
                            </div>
                            <div class="metric-item">
                                <div class="metric-value">{{ dead_end_count }}</div>
                                <div class="metric-label">Dead Ends</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="card">
                        <h3 style="font-size: 1rem; font-weight: 600; margin-bottom: 1rem;">🏆 Top Pages</h3>
                        <ul class="issue-list">
                            {% for page in top_pages[:5] %}
                            <li class="issue-item success">
                                <strong>{{ page.title[:30] }}...</strong><br>
                                <small style="color: var(--text-secondary);">{{ page.child_count }} links</small>
                            </li>
                            {% endfor %}
                        </ul>
                    </div>
                </div>
                
                <!-- Center Column - Network Graph -->
                <div class="chart-container">
                    <div id="network-chart-overview" style="width: 100%; height: 100%;"></div>
                </div>
                
                <!-- Right Column -->
                <div>
                    <div class="card" style="margin-bottom: 1rem;">
                        <h3 style="font-size: 1rem; font-weight: 600; margin-bottom: 1rem;">⚠️ Issues Found</h3>
                        <ul class="issue-list">
                            {% if orphan_count > 0 %}
                            <li class="issue-item critical">{{ orphan_count }} orphan pages need internal links</li>
                            {% endif %}
                            {% if dead_end_count > 0 %}
                            <li class="issue-item">{{ dead_end_count }} dead-end pages need navigation</li>
                            {% endif %}
                            {% if bottleneck_count > 0 %}
                            <li class="issue-item">{{ bottleneck_count }} pages hard to reach</li>
                            {% endif %}
                            {% if orphan_count == 0 and dead_end_count == 0 and bottleneck_count == 0 %}
                            <li class="issue-item success">No critical issues found!</li>
                            {% endif %}
                        </ul>
                    </div>
                    
                    <div class="card">
                        <h3 style="font-size: 1rem; font-weight: 600; margin-bottom: 1rem;">💡 Quick Wins</h3>
                        <ul class="recommendation-list">
                            {% for rec in recommendations.critical[:2] %}
                            <li class="recommendation-item">
                                <span class="recommendation-priority priority-critical">Critical</span>
                                <p style="font-size: 0.875rem;">{{ rec.action }}</p>
                            </li>
                            {% endfor %}
                            {% for rec in recommendations.important[:2] %}
                            <li class="recommendation-item">
                                <span class="recommendation-priority priority-important">Important</span>
                                <p style="font-size: 0.875rem;">{{ rec.action }}</p>
                            </li>
                            {% endfor %}
                        </ul>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Tab: Network -->
        <div class="tab-content" id="tab-network">
            <div class="chart-container large">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <h3 style="font-size: 1rem; font-weight: 600;">🕸️ Interactive Network Visualization</h3>
                    <div>
                        <button class="btn btn-secondary" onclick="resetNetworkView()">Reset View</button>
                        <button class="btn btn-primary" onclick="exportNetworkPNG()">Export PNG</button>
                    </div>
                </div>
                <div id="network-chart-full" style="width: 100%; height: 550px;"></div>
            </div>
            
            <div class="card" style="margin-top: 1rem;">
                <h3 style="font-size: 1rem; font-weight: 600; margin-bottom: 0.5rem;">📍 Legend</h3>
                <div style="display: flex; gap: 2rem; flex-wrap: wrap; font-size: 0.875rem;">
                    <div><span style="display: inline-block; width: 12px; height: 12px; background: #3B82F6; border-radius: 50%; margin-right: 0.5rem;"></span> Depth 0-1 (Homepage/Main)</div>
                    <div><span style="display: inline-block; width: 12px; height: 12px; background: #60A5FA; border-radius: 50%; margin-right: 0.5rem;"></span> Depth 2-3 (Section Pages)</div>
                    <div><span style="display: inline-block; width: 12px; height: 12px; background: #93C5FD; border-radius: 50%; margin-right: 0.5rem;"></span> Depth 4+ (Deep Pages)</div>
                    <div><span style="font-size: 0.75rem; color: var(--text-secondary);">Node size = Link count</span></div>
                </div>
            </div>
        </div>
        
        <!-- Tab: Statistics -->
        <div class="tab-content" id="tab-statistics">
            <div class="grid-2">
                <div class="chart-container">
                    <div id="depth-chart" style="width: 100%; height: 350px;"></div>
                </div>
                <div class="chart-container">
                    <div id="section-chart" style="width: 100%; height: 350px;"></div>
                </div>
            </div>
            
            <div class="summary-cards" style="margin-top: 1.5rem;">
                <div class="card">
                    <div class="card-label">Breadth</div>
                    <div class="card-value">{{ (stats.total_pages / (stats.max_depth + 1)) | round(1) }}</div>
                    <div class="card-subtext">Avg pages per depth</div>
                </div>
                <div class="card">
                    <div class="card-label">Depth Range</div>
                    <div class="card-value">0 - {{ stats.max_depth }}</div>
                    <div class="card-subtext">Min to Max depth</div>
                </div>
                <div class="card">
                    <div class="card-label">Link Density</div>
                    <div class="card-value">{{ stats.avg_links }}</div>
                    <div class="card-subtext">Avg links per page</div>
                </div>
                <div class="card">
                    <div class="card-label">Connectivity</div>
                    <div class="card-value success">{{ ia_score.breakdown.connectivity_score }}%</div>
                    <div class="card-subtext">Pages reachable from home</div>
                </div>
            </div>
            
            <div class="card" style="margin-top: 1.5rem;">
                <h3 style="font-size: 1rem; font-weight: 600; margin-bottom: 1rem;">📊 Detailed Statistics</h3>
                <div style="overflow-x: auto;">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Metric</th>
                                <th>Current Value</th>
                                <th>Best Practice</th>
                                <th>Status</th>
                                <th>Recommendation</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>Max Depth</td>
                                <td>{{ stats.max_depth }}</td>
                                <td>≤ 4</td>
                                <td><span class="status-badge {{ 'status-success' if stats.max_depth <= 4 else 'status-warning' }}">{{ 'Good' if stats.max_depth <= 4 else 'Review' }}</span></td>
                                <td>{{ 'Optimal depth' if stats.max_depth <= 4 else 'Consider restructuring deep pages' }}</td>
                            </tr>
                            <tr>
                                <td>Average Depth</td>
                                <td>{{ stats.avg_depth }}</td>
                                <td>≤ 3.0</td>
                                <td><span class="status-badge {{ 'status-success' if stats.avg_depth <= 3 else 'status-warning' }}">{{ 'Good' if stats.avg_depth <= 3 else 'Review' }}</span></td>
                                <td>{{ 'Content easily accessible' if stats.avg_depth <= 3 else 'Move important content higher' }}</td>
                            </tr>
                            <tr>
                                <td>IA Score</td>
                                <td>{{ ia_score.final_score }}</td>
                                <td>≥ 75</td>
                                <td><span class="status-badge {{ 'status-success' if ia_score.final_score >= 75 else 'status-warning' if ia_score.final_score >= 50 else 'status-danger' }}">{{ ia_score.health_status }}</span></td>
                                <td>{{ ia_score.interpretation }}</td>
                            </tr>
                            <tr>
                                <td>Orphan Pages</td>
                                <td>{{ orphan_count }}</td>
                                <td>0</td>
                                <td><span class="status-badge {{ 'status-success' if orphan_count == 0 else 'status-danger' }}">{{ 'Good' if orphan_count == 0 else 'Fix Required' }}</span></td>
                                <td>{{ 'No orphan pages' if orphan_count == 0 else 'Add internal links to orphan pages' }}</td>
                            </tr>
                            <tr>
                                <td>Dead Ends</td>
                                <td>{{ dead_end_count }}</td>
                                <td>< 10%</td>
                                <td><span class="status-badge {{ 'status-success' if dead_end_count < stats.total_pages * 0.1 else 'status-warning' }}">{{ 'Good' if dead_end_count < stats.total_pages * 0.1 else 'Review' }}</span></td>
                                <td>{{ 'Acceptable dead end rate' if dead_end_count < stats.total_pages * 0.1 else 'Add navigation to dead-end pages' }}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        
        <!-- Tab: Audit Report -->
        <div class="tab-content" id="tab-audit">
            <div style="display: flex; justify-content: flex-end; gap: 0.5rem; margin-bottom: 1rem;">
                <button class="btn btn-secondary" onclick="window.open('/download-report?format=txt')">📄 Export TXT</button>
                <button class="btn btn-primary" onclick="window.print()">🖨️ Print</button>
            </div>
            
            <!-- Executive Summary -->
            <div class="report-section expanded">
                <div class="report-header" onclick="toggleSection(this)">
                    <h3>📋 Executive Summary</h3>
                    <span class="expand-icon">▼</span>
                </div>
                <div class="report-content">
                    <div class="metrics-grid">
                        <div class="metric-item">
                            <div class="metric-value">{{ ia_score.final_score }}/100</div>
                            <div class="metric-label">IA Score</div>
                        </div>
                        <div class="metric-item">
                            <div class="metric-value">{{ stats.total_pages }}</div>
                            <div class="metric-label">Total Pages</div>
                        </div>
                        <div class="metric-item">
                            <div class="metric-value">{{ stats.max_depth }}</div>
                            <div class="metric-label">Max Depth</div>
                        </div>
                        <div class="metric-item">
                            <div class="metric-value">{{ ia_score.health_status }}</div>
                            <div class="metric-label">Status</div>
                        </div>
                    </div>
                    <p style="margin-top: 1rem; color: var(--text-secondary);">{{ ia_score.interpretation }}</p>
                </div>
            </div>
            
            <!-- Critical Issues -->
            <div class="report-section">
                <div class="report-header" onclick="toggleSection(this)">
                    <h3>⚠️ Critical Issues ({{ orphan_count + dead_end_count + bottleneck_count }})</h3>
                    <span class="expand-icon">▼</span>
                </div>
                <div class="report-content">
                    <ul class="issue-list">
                        {% if orphan_count > 0 %}
                        <li class="issue-item critical">
                            <strong>Orphan Pages: {{ orphan_count }}</strong><br>
                            Pages with no inbound links. Add internal links to improve SEO and discoverability.
                        </li>
                        {% endif %}
                        {% if dead_end_count > 0 %}
                        <li class="issue-item">
                            <strong>Dead-End Pages: {{ dead_end_count }}</strong><br>
                            Pages with no outbound navigation. Add related links or call-to-actions.
                        </li>
                        {% endif %}
                        {% if bottleneck_count > 0 %}
                        <li class="issue-item">
                            <strong>Navigation Bottlenecks: {{ bottleneck_count }}</strong><br>
                            Pages requiring more than 3 clicks to reach. Consider restructuring.
                        </li>
                        {% endif %}
                        {% if orphan_count == 0 and dead_end_count == 0 and bottleneck_count == 0 %}
                        <li class="issue-item success">
                            <strong>No Critical Issues Found!</strong><br>
                            Your website structure is well-organized.
                        </li>
                        {% endif %}
                    </ul>
                </div>
            </div>
            
            <!-- Recommendations -->
            <div class="report-section">
                <div class="report-header" onclick="toggleSection(this)">
                    <h3>💡 Recommendations</h3>
                    <span class="expand-icon">▼</span>
                </div>
                <div class="report-content">
                    {% if recommendations.critical %}
                    <h4 style="margin-bottom: 0.75rem; color: var(--danger);">🔴 Critical (Do This Week)</h4>
                    <ul class="recommendation-list">
                        {% for rec in recommendations.critical %}
                        <li class="recommendation-item">
                            <span class="recommendation-priority priority-critical">Critical</span>
                            <p><strong>{{ rec.action }}</strong></p>
                            <p style="font-size: 0.875rem; color: var(--text-secondary);">
                                Effort: {{ rec.effort_estimate }} | Impact: {{ rec.expected_impact }}
                            </p>
                        </li>
                        {% endfor %}
                    </ul>
                    {% endif %}
                    
                    {% if recommendations.important %}
                    <h4 style="margin: 1.5rem 0 0.75rem; color: var(--warning);">🟡 Important (Do This Month)</h4>
                    <ul class="recommendation-list">
                        {% for rec in recommendations.important %}
                        <li class="recommendation-item">
                            <span class="recommendation-priority priority-important">Important</span>
                            <p><strong>{{ rec.action }}</strong></p>
                            <p style="font-size: 0.875rem; color: var(--text-secondary);">
                                Effort: {{ rec.effort_estimate }} | Difficulty: {{ rec.difficulty }}
                            </p>
                        </li>
                        {% endfor %}
                    </ul>
                    {% endif %}
                    
                    {% if recommendations.nice_to_have %}
                    <h4 style="margin: 1.5rem 0 0.75rem; color: var(--success);">🟢 Nice to Have (Long Term)</h4>
                    <ul class="recommendation-list">
                        {% for rec in recommendations.nice_to_have %}
                        <li class="recommendation-item">
                            <span class="recommendation-priority priority-nice">Nice to Have</span>
                            <p><strong>{{ rec.action }}</strong></p>
                            <p style="font-size: 0.875rem; color: var(--text-secondary);">
                                Strategic Value: {{ rec.expected_impact }}
                            </p>
                        </li>
                        {% endfor %}
                    </ul>
                    {% endif %}
                </div>
            </div>
            
            <!-- Implementation Roadmap -->
            <div class="report-section">
                <div class="report-header" onclick="toggleSection(this)">
                    <h3>🗺️ Implementation Roadmap</h3>
                    <span class="expand-icon">▼</span>
                </div>
                <div class="report-content">
                    <div style="padding: 1rem; background: var(--bg-primary); border-radius: 0.5rem; font-family: monospace; font-size: 0.875rem;">
                        <strong>PHASE 1 (Week 1-2): Quick Wins</strong><br>
                        ├─ Fix orphan pages<br>
                        ├─ Add navigation to dead ends<br>
                        └─ Update meta descriptions<br><br>
                        
                        <strong>PHASE 2 (Month 1): Major Improvements</strong><br>
                        ├─ Reorganize deep content<br>
                        ├─ Create section landing pages<br>
                        └─ Implement related content widgets<br><br>
                        
                        <strong>PHASE 3 (Quarter 1): Strategic Changes</strong><br>
                        ├─ Implement breadcrumb navigation<br>
                        ├─ Add site search functionality<br>
                        └─ Create comprehensive sitemap
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Tab: Data Table -->
        <div class="tab-content" id="tab-data">
            <div class="data-table-container">
                <div class="table-controls">
                    <input type="text" class="search-input" id="tableSearch" placeholder="🔍 Search URLs, titles..." onkeyup="filterTable()">
                    <select class="filter-select" id="depthFilter" onchange="filterTable()">
                        <option value="">All Depths</option>
                        {% for depth in range(stats.max_depth + 1) %}
                        <option value="{{ depth }}">Depth {{ depth }}</option>
                        {% endfor %}
                    </select>
                    <select class="filter-select" id="statusFilter" onchange="filterTable()">
                        <option value="">All Status</option>
                        <option value="200">200 OK</option>
                        <option value="404">404 Not Found</option>
                        <option value="500">500 Error</option>
                    </select>
                    <button class="btn btn-primary" onclick="window.open('/download-data')">📥 Export CSV</button>
                </div>
                
                <div style="overflow-x: auto;">
                    <table class="data-table" id="dataTable">
                        <thead>
                            <tr>
                                <th onclick="sortTable(0)">URL ↕</th>
                                <th onclick="sortTable(1)">Title ↕</th>
                                <th onclick="sortTable(2)">Depth ↕</th>
                                <th onclick="sortTable(3)">Links ↕</th>
                                <th onclick="sortTable(4)">Status ↕</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for row in table_data %}
                            <tr data-depth="{{ row.depth }}" data-status="{{ row.status_code }}">
                                <td class="url-cell" title="{{ row.url }}">{{ row.url[:60] }}{% if row.url|length > 60 %}...{% endif %}</td>
                                <td>{{ row.title[:40] }}{% if row.title|length > 40 %}...{% endif %}</td>
                                <td>{{ row.depth }}</td>
                                <td>{{ row.child_count }}</td>
                                <td>
                                    <span class="status-badge {{ 'status-success' if row.status_code == 200 else 'status-warning' if row.status_code < 400 else 'status-danger' }}">
                                        {{ row.status_code }}
                                    </span>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                
                <div class="pagination">
                    <div class="pagination-info">
                        Showing <span id="showingCount">{{ table_data|length }}</span> of {{ stats.total_pages }} entries
                    </div>
                    <div class="pagination-controls">
                        <button class="page-btn" onclick="changePage(-1)">← Previous</button>
                        <button class="page-btn active">1</button>
                        <button class="page-btn" onclick="changePage(1)">Next →</button>
                    </div>
                </div>
            </div>
        </div>
    </main>
    
    <!-- Footer -->
    <footer class="footer">
        <p>TSM Website Structure Dashboard | Data crawled: {{ timestamp }}</p>
        <p style="margin-top: 0.5rem; font-size: 0.75rem;">
            Built with Flask, Plotly, and NetworkX | 
            <a href="/api/statistics" style="color: var(--primary);">API</a> | 
            <a href="#" style="color: var(--primary);">Documentation</a>
        </p>
    </footer>
    
    <script>
        // Chart data from server
        const networkDataOverview = {{ network_graph_json | safe }};
        const networkDataFull = {{ network_graph_json | safe }};
        const depthChartData = {{ depth_chart_json | safe }};
        const sectionChartData = {{ section_chart_json | safe }};
        
        // Initialize charts
        document.addEventListener('DOMContentLoaded', function() {
            // Overview network graph
            if (networkDataOverview && Object.keys(networkDataOverview).length > 0) {
                Plotly.newPlot('network-chart-overview', networkDataOverview.data, networkDataOverview.layout, {responsive: true});
            }
            
            // Depth chart
            if (depthChartData && Object.keys(depthChartData).length > 0) {
                Plotly.newPlot('depth-chart', depthChartData.data, depthChartData.layout, {responsive: true});
            }
            
            // Section chart
            if (sectionChartData && Object.keys(sectionChartData).length > 0) {
                Plotly.newPlot('section-chart', sectionChartData.data, sectionChartData.layout, {responsive: true});
            }
        });
        
        // Tab navigation
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.addEventListener('click', function() {
                // Remove active from all tabs
                document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                
                // Add active to clicked tab
                this.classList.add('active');
                document.getElementById('tab-' + this.dataset.tab).classList.add('active');
                
                // Initialize full network graph when network tab is selected
                if (this.dataset.tab === 'network' && networkDataFull) {
                    setTimeout(() => {
                        Plotly.newPlot('network-chart-full', networkDataFull.data, {
                            ...networkDataFull.layout,
                            height: 550
                        }, {responsive: true});
                    }, 100);
                }
            });
        });
        
        // Theme toggle
        function toggleTheme() {
            document.body.classList.toggle('dark');
            const btn = document.querySelector('.theme-toggle');
            btn.textContent = document.body.classList.contains('dark') ? '☀️' : '🌙';
            
            // Re-render charts with new theme
            const bgColor = document.body.classList.contains('dark') ? 'rgba(31, 41, 55, 0)' : 'rgba(0,0,0,0)';
            Plotly.relayout('network-chart-overview', {'paper_bgcolor': bgColor, 'plot_bgcolor': bgColor});
            Plotly.relayout('depth-chart', {'paper_bgcolor': bgColor, 'plot_bgcolor': bgColor});
            Plotly.relayout('section-chart', {'paper_bgcolor': bgColor, 'plot_bgcolor': bgColor});
        }
        
        // Report section toggle
        function toggleSection(header) {
            header.parentElement.classList.toggle('expanded');
        }
        
        // Table filtering
        function filterTable() {
            const search = document.getElementById('tableSearch').value.toLowerCase();
            const depthFilter = document.getElementById('depthFilter').value;
            const statusFilter = document.getElementById('statusFilter').value;
            
            const rows = document.querySelectorAll('#dataTable tbody tr');
            let visibleCount = 0;
            
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                const depth = row.dataset.depth;
                const status = row.dataset.status;
                
                const matchSearch = text.includes(search);
                const matchDepth = !depthFilter || depth === depthFilter;
                const matchStatus = !statusFilter || status === statusFilter;
                
                if (matchSearch && matchDepth && matchStatus) {
                    row.style.display = '';
                    visibleCount++;
                } else {
                    row.style.display = 'none';
                }
            });
            
            document.getElementById('showingCount').textContent = visibleCount;
        }
        
        // Table sorting
        let sortDirection = {};
        function sortTable(columnIndex) {
            const table = document.getElementById('dataTable');
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            
            sortDirection[columnIndex] = !sortDirection[columnIndex];
            const dir = sortDirection[columnIndex] ? 1 : -1;
            
            rows.sort((a, b) => {
                let aVal = a.cells[columnIndex].textContent.trim();
                let bVal = b.cells[columnIndex].textContent.trim();
                
                // Check if numeric
                if (!isNaN(aVal) && !isNaN(bVal)) {
                    return (parseFloat(aVal) - parseFloat(bVal)) * dir;
                }
                
                return aVal.localeCompare(bVal) * dir;
            });
            
            rows.forEach(row => tbody.appendChild(row));
        }
        
        // Refresh data
        function refreshData() {
            window.location.href = '/?refresh=1';
        }
        
        // Export report
        function exportReport() {
            window.open('/download-report?format=txt');
        }
        
        // Reset network view
        function resetNetworkView() {
            Plotly.relayout('network-chart-full', {
                'xaxis.autorange': true,
                'yaxis.autorange': true
            });
        }
        
        // Export network as PNG
        function exportNetworkPNG() {
            Plotly.downloadImage('network-chart-full', {
                format: 'png',
                width: 1200,
                height: 800,
                filename: 'tsm_network_graph'
            });
        }
        
        // Pagination (simplified)
        function changePage(delta) {
            // In a full implementation, this would handle actual pagination
            console.log('Page change:', delta);
        }
    </script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.route("/")
def dashboard_home():
    """
    Main dashboard with all visualizations.
    
    Query params:
        refresh: If set, force refresh data
    """
    # Check for refresh
    if request.args.get("refresh"):
        refresh_dashboard_data()

    data = get_dashboard_data()
    df = data["df_crawl"]
    audit_data = data["audit_data"]
    stats = data["stats"]

    # Get audit metrics
    ia_score = audit_data.get("ia_score", {"final_score": 0, "health_status": "Unknown", "interpretation": "", "breakdown": {"connectivity_score": 0}})
    orphan_pages = audit_data.get("orphan_pages", [])
    dead_ends = audit_data.get("dead_ends", [])
    bottlenecks = audit_data.get("bottlenecks", [])
    top_pages = audit_data.get("top_pages", [])
    recommendations = audit_data.get("recommendations", {"critical": [], "important": [], "nice_to_have": []})

    # Generate charts
    network_graph_json = create_network_graph_plotly(df, max_nodes=80)
    depth_chart_json = create_depth_bar_chart(stats)
    section_chart_json = create_section_pie_chart(audit_data)

    # Prepare table data
    table_data = df.to_dict("records") if not df.empty else []

    return render_template_string(
        DASHBOARD_HTML,
        timestamp=data["timestamp"],
        stats=stats,
        ia_score=ia_score,
        orphan_count=len(orphan_pages),
        dead_end_count=len(dead_ends),
        bottleneck_count=len(bottlenecks),
        top_pages=top_pages,
        recommendations=recommendations,
        network_graph_json=network_graph_json,
        depth_chart_json=depth_chart_json,
        section_chart_json=section_chart_json,
        table_data=table_data[:100],  # Limit for performance
    )


@app.route("/api/network-data")
def api_network_data():
    """
    Serve network data for Plotly.
    
    Returns:
        JSON with nodes, edges, and layout
    """
    data = get_dashboard_data()
    df = data["df_crawl"]

    if df.empty:
        return jsonify({"error": "No data available"}), 404

    nodes = []
    edges = []

    for idx, row in df.iterrows():
        nodes.append({
            "id": row["url"],
            "label": row.get("title", "")[:30],
            "depth": int(row.get("depth", 0)),
            "children_count": int(row.get("child_count", 0)),
        })

        parent = row.get("parent_url", "")
        if parent:
            edges.append({
                "source": parent,
                "target": row["url"],
            })

    return jsonify({
        "nodes": nodes,
        "edges": edges,
        "layout": {
            "title": "Website Structure Network",
            "height": 600,
            "width": 800,
        },
    })


@app.route("/api/statistics")
def api_statistics():
    """
    Serve statistical data.
    
    Returns:
        JSON with comprehensive statistics
    """
    data = get_dashboard_data()
    stats = data["stats"]
    audit_data = data["audit_data"]

    return jsonify({
        "total_pages": stats.get("total_pages", 0),
        "avg_depth": stats.get("avg_depth", 0),
        "max_depth": stats.get("max_depth", 0),
        "pages_by_depth": stats.get("pages_by_depth", {}),
        "pages_by_status": stats.get("pages_by_status", {}),
        "avg_links": stats.get("avg_links", 0),
        "top_pages": audit_data.get("top_pages", []),
        "orphan_pages": len(audit_data.get("orphan_pages", [])),
        "dead_ends": len(audit_data.get("dead_ends", [])),
        "ia_score": audit_data.get("ia_score", {}),
        "architecture_assessment": audit_data.get("depth_analysis", {}).get("assessment", ""),
    })


@app.route("/api/audit-summary")
def api_audit_summary():
    """
    Serve audit report summary.
    
    Returns:
        JSON with executive summary and recommendations
    """
    data = get_dashboard_data()
    audit_data = data["audit_data"]

    return jsonify({
        "executive_summary": {
            "ia_score": audit_data.get("ia_score", {}),
            "total_pages": data["stats"].get("total_pages", 0),
            "max_depth": data["stats"].get("max_depth", 0),
        },
        "critical_issues": {
            "orphan_pages": len(audit_data.get("orphan_pages", [])),
            "dead_ends": len(audit_data.get("dead_ends", [])),
            "bottlenecks": len(audit_data.get("bottlenecks", [])),
        },
        "recommendations": audit_data.get("recommendations", {}),
        "content_distribution": audit_data.get("content_distribution", {}),
        "user_journey": audit_data.get("user_journey", {}),
    })


@app.route("/download-report")
def download_report():
    """
    Download full audit report.
    
    Query params:
        format: txt (default)
    """
    fmt = request.args.get("format", "txt")

    # Generate report if not exists
    if not REPORT_OUTPUT_PATH.exists():
        try:
            auditor = AuditReportGenerator(str(CSV_FILE_PATH))
            auditor.generate_full_report(str(REPORT_OUTPUT_PATH))
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return jsonify({"error": "Failed to generate report"}), 500

    if fmt == "txt":
        return send_file(
            REPORT_OUTPUT_PATH,
            mimetype="text/plain",
            as_attachment=True,
            download_name="TSM_Website_Audit_Report.txt",
        )

    return jsonify({"error": "Unsupported format"}), 400


@app.route("/download-data")
def download_data():
    """
    Download crawled data as CSV.
    """
    if not CSV_FILE_PATH.exists():
        return jsonify({"error": "Data file not found"}), 404

    return send_file(
        CSV_FILE_PATH,
        mimetype="text/csv",
        as_attachment=True,
        download_name="tsm_crawl_data.csv",
    )


@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors."""
    return jsonify({"error": "Resource not found"}), 404


@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors."""
    logger.error(f"Server error: {e}")
    return jsonify({"error": "Internal server error"}), 500


# ---------------------------------------------------------------------------
# App Factory
# ---------------------------------------------------------------------------


def create_app() -> Flask:
    """
    Application factory for creating Flask app.
    
    Returns:
        Configured Flask application
    """
    # Pre-load data
    get_dashboard_data()
    return app


# ---------------------------------------------------------------------------
# Main Execution
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("TSM Website Structure Dashboard")
    print("=" * 60)
    print("Starting server...")
    print("Dashboard URL: http://localhost:5000")
    print("API Endpoints:")
    print("  - /api/network-data")
    print("  - /api/statistics")
    print("  - /api/audit-summary")
    print("  - /download-report")
    print("  - /download-data")
    print("=" * 60)
    print("Press Ctrl+C to stop")
    print()

    app.run(debug=True, host="0.0.0.0", port=5000)

