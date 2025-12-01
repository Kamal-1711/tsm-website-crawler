"""
Enhanced Flask Dashboard with shadcn/ui Components
===================================================

Modern, professional dashboard using Tailwind CSS, shadcn/ui-inspired components,
and Plotly for interactive visualizations.

Author: TSM Web Crawler Project
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import networkx as nx
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from flask import Flask, Response, jsonify, render_template_string, request, send_file

# Import audit report generator
from src.audit_report import AuditReportGenerator

# Import mindmap functions
from src.mindmap import generate_mindmap_data, get_depth_color, get_section_icon, extract_section_name

# ---------------------------------------------------------------------------
# Logging Setup
# ---------------------------------------------------------------------------

logger = logging.getLogger("TSMDashboardShadcn")
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

app = Flask(__name__)
app.config['DEBUG'] = True

# Enable CORS
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

    for col in ("depth", "child_count", "status_code"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    for col in ("url", "parent_url", "title", "description", "heading"):
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str)

    return df


def load_dashboard_data() -> Dict[str, Any]:
    """Load all dashboard data."""
    df = load_crawl_data()
    
    if df.empty:
        return {
            "df_crawl": df,
            "audit_data": {},
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

    # Calculate statistics
    stats = {
        "total_pages": len(df),
        "avg_depth": round(df["depth"].mean(), 2) if len(df) > 0 else 0,
        "max_depth": int(df["depth"].max()) if len(df) > 0 else 0,
        "avg_links": round(df["child_count"].mean(), 1) if len(df) > 0 else 0,
        "total_links": int(df["child_count"].sum()) if len(df) > 0 else 0,
        "pages_by_depth": df["depth"].value_counts().sort_index().to_dict() if len(df) > 0 else {},
        "pages_by_status": df["status_code"].value_counts().to_dict() if "status_code" in df.columns else {},
        "deep_pages": int((df["depth"] >= 5).sum()) if len(df) > 0 else 0,
    }

    return {
        "df_crawl": df,
        "audit_data": audit_data,
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


def create_network_graph_plotly(df: pd.DataFrame, max_nodes: int = 80) -> str:
    """Create an interactive network graph using Plotly with dark theme."""
    if df.empty:
        return "{}"

    df_limited = df.head(max_nodes)

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

    try:
        pos = nx.spring_layout(G, k=2, iterations=50, seed=42)
    except Exception:
        pos = {node: (i % 10, i // 10) for i, node in enumerate(G.nodes())}

    edge_x, edge_y = [], []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.5, color="#475569"),
        hoverinfo="none",
        mode="lines",
    )

    node_x, node_y, node_text, node_color, node_size = [], [], [], [], []

    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)

        data = G.nodes[node]
        title = data.get("title", "No Title")[:40]
        depth = data.get("depth", 0)
        children = data.get("child_count", 0)

        node_text.append(f"<b>{title}</b><br>Depth: {depth}<br>Links: {children}")
        node_color.append(depth)
        node_size.append(max(8, min(40, 8 + children * 0.4)))

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode="markers",
        hoverinfo="text",
        text=node_text,
        marker=dict(
            showscale=True,
            colorscale=[[0, "#3B82F6"], [0.5, "#8B5CF6"], [1, "#EC4899"]],
            color=node_color,
            size=node_size,
            colorbar=dict(
                thickness=15,
                title=dict(text="Depth", side="right", font=dict(color="#94A3B8")),
                xanchor="left",
                tickfont=dict(color="#94A3B8"),
            ),
            line=dict(width=1, color="#1E293B"),
        ),
    )

    fig = go.Figure(
        data=[edge_trace, node_trace],
        layout=go.Layout(
            showlegend=False,
            hovermode="closest",
            margin=dict(b=0, l=0, r=0, t=0),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor="#0F172A",
            paper_bgcolor="#0F172A",
        ),
    )

    return fig.to_json()


def create_depth_bar_chart(stats: Dict[str, Any]) -> str:
    """Create a bar chart showing pages per depth level with dark theme."""
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
                marker_color=["#3B82F6" if d <= 2 else "#F59E0B" if d <= 4 else "#EF4444" for d in depths],
                text=counts,
                textposition="auto",
                textfont=dict(color="#E2E8F0"),
            )
        ],
        layout=go.Layout(
            margin=dict(l=40, r=20, t=20, b=40),
            plot_bgcolor="#0F172A",
            paper_bgcolor="#0F172A",
            xaxis=dict(
                tickfont=dict(color="#94A3B8"),
                gridcolor="#334155",
            ),
            yaxis=dict(
                tickfont=dict(color="#94A3B8"),
                gridcolor="#334155",
            ),
        ),
    )

    return fig.to_json()


def create_section_pie_chart(audit_data: Dict[str, Any]) -> str:
    """Create a pie chart showing content distribution with dark theme."""
    content_dist = audit_data.get("content_distribution", {})
    sections = content_dist.get("sections", [])
    if not sections:
        return "{}"

    top_sections = sections[:8]
    labels = [s["name"] for s in top_sections]
    values = [s["page_count"] for s in top_sections]

    colors = ["#3B82F6", "#8B5CF6", "#EC4899", "#F59E0B", "#10B981", "#06B6D4", "#6366F1", "#84CC16"]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.5,
                textinfo="label+percent",
                textposition="outside",
                textfont=dict(color="#E2E8F0", size=11),
                marker=dict(colors=colors[:len(labels)], line=dict(color="#0F172A", width=2)),
            )
        ],
        layout=go.Layout(
            margin=dict(l=20, r=20, t=20, b=20),
            showlegend=False,
            paper_bgcolor="#0F172A",
            plot_bgcolor="#0F172A",
        ),
    )

    return fig.to_json()


def create_status_donut_chart(stats: Dict[str, Any]) -> str:
    """Create a donut chart for status codes."""
    pages_by_status = stats.get("pages_by_status", {})
    if not pages_by_status:
        return "{}"

    labels = [str(s) for s in pages_by_status.keys()]
    values = list(pages_by_status.values())

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
            go.Pie(
                labels=labels,
                values=values,
                hole=0.6,
                textinfo="label+value",
                textfont=dict(color="#E2E8F0"),
                marker=dict(colors=colors, line=dict(color="#0F172A", width=2)),
            )
        ],
        layout=go.Layout(
            margin=dict(l=20, r=20, t=20, b=20),
            showlegend=False,
            paper_bgcolor="#0F172A",
            plot_bgcolor="#0F172A",
            annotations=[dict(text="Status", x=0.5, y=0.5, font=dict(size=14, color="#94A3B8"), showarrow=False)],
        ),
    )

    return fig.to_json()


def create_mindmap_plotly(df: pd.DataFrame, max_nodes: int = 100) -> str:
    """Create an interactive mind map visualization using Plotly with radial layout."""
    if df.empty:
        return "{}"

    df_limited = df.head(max_nodes)

    # Build graph
    G = nx.DiGraph()
    
    for _, row in df_limited.iterrows():
        url = row["url"]
        parent = row.get("parent_url", "") or ""
        
        G.add_node(url, **{
            "title": row.get("title", "") or extract_section_name(url),
            "depth": int(row.get("depth", 0)),
            "child_count": int(row.get("child_count", 0)),
            "status_code": int(row.get("status_code", 200)),
        })
        
        if parent and parent in [r["url"] for _, r in df_limited.iterrows()]:
            G.add_edge(parent, url)

    # Find root nodes
    root_nodes = [n for n in G.nodes() if G.in_degree(n) == 0]
    root = root_nodes[0] if root_nodes else (list(G.nodes())[0] if G.nodes() else None)

    if not root:
        return "{}"

    # Calculate radial positions
    import math
    
    def calculate_radial_positions(graph, root_node):
        """Calculate positions in a radial layout."""
        pos = {}
        visited = set()
        
        # BFS to assign positions
        levels = {}
        queue = [(root_node, 0)]
        visited.add(root_node)
        
        while queue:
            node, level = queue.pop(0)
            if level not in levels:
                levels[level] = []
            levels[level].append(node)
            
            for neighbor in graph.successors(node):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, level + 1))
        
        # Position nodes radially
        pos[root_node] = (0, 0)
        
        for level, nodes in levels.items():
            if level == 0:
                continue
            
            radius = level * 1.5
            angle_step = 2 * math.pi / max(len(nodes), 1)
            
            for i, node in enumerate(nodes):
                angle = i * angle_step - math.pi / 2
                x = radius * math.cos(angle)
                y = radius * math.sin(angle)
                pos[node] = (x, y)
        
        return pos

    try:
        pos = calculate_radial_positions(G, root)
    except Exception:
        pos = nx.spring_layout(G, k=2, iterations=50, seed=42)

    # Create edge traces
    edge_x, edge_y = [], []
    
    for edge in G.edges():
        if edge[0] in pos and edge[1] in pos:
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        line=dict(width=1, color="#475569"),
        hoverinfo="none",
        mode="lines",
        name="Connections",
    )

    # Create node traces by depth
    node_traces = []
    depth_names = {
        0: "🏠 Homepage",
        1: "📁 Main Sections",
        2: "📄 Subsections",
        3: "📝 Detail Pages",
        4: "📎 Deep Pages",
    }
    
    for depth in range(6):
        nodes_at_depth = [n for n in G.nodes() if G.nodes[n].get("depth", 0) == depth and n in pos]
        
        if not nodes_at_depth:
            continue
        
        node_x, node_y, node_text, node_size = [], [], [], []
        
        for node in nodes_at_depth:
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            
            data = G.nodes[node]
            title = data.get("title", "")[:40]
            child_count = data.get("child_count", 0)
            status = data.get("status_code", 200)
            icon = get_section_icon(title)
            
            hover_text = (
                f"<b>{icon} {title}</b><br>"
                f"<span style='color:#94A3B8'>URL:</span> {node[:60]}{'...' if len(node) > 60 else ''}<br>"
                f"<span style='color:#94A3B8'>Depth:</span> {depth}<br>"
                f"<span style='color:#94A3B8'>Children:</span> {child_count}<br>"
                f"<span style='color:#94A3B8'>Status:</span> {status}"
            )
            node_text.append(hover_text)
            
            # Size based on child count
            size = 25 + min(child_count * 2, 45)
            node_size.append(size)
        
        depth_name = depth_names.get(depth, f"Level {depth}")
        
        node_trace = go.Scatter(
            x=node_x,
            y=node_y,
            mode="markers",
            hoverinfo="text",
            text=node_text,
            name=depth_name,
            marker=dict(
                color=get_depth_color(depth),
                size=node_size,
                line=dict(width=2, color="#0F172A"),
                opacity=0.9,
            ),
        )
        node_traces.append(node_trace)

    # Create figure
    fig = go.Figure(
        data=[edge_trace] + node_traces,
        layout=go.Layout(
            showlegend=True,
            legend=dict(
                font=dict(color="#E2E8F0", size=12),
                bgcolor="rgba(30, 41, 59, 0.9)",
                bordercolor="#475569",
                borderwidth=1,
                x=0.02,
                y=0.98,
                xanchor="left",
                yanchor="top",
            ),
            hovermode="closest",
            paper_bgcolor="#0F172A",
            plot_bgcolor="#0F172A",
            xaxis=dict(
                showgrid=False,
                zeroline=False,
                showticklabels=False,
            ),
            yaxis=dict(
                showgrid=False,
                zeroline=False,
                showticklabels=False,
            ),
            margin=dict(l=20, r=20, t=20, b=20),
        ),
    )

    return fig.to_json()


def create_treemap_chart(df: pd.DataFrame) -> str:
    """Create a treemap visualization of the website structure."""
    if df.empty:
        return "{}"

    # Group by depth and extract section from URL
    section_data = []
    
    for _, row in df.iterrows():
        url = row["url"]
        depth = int(row.get("depth", 0))
        child_count = int(row.get("child_count", 0))
        title = row.get("title", "") or extract_section_name(url)
        
        # Extract first path segment as section
        try:
            path_parts = [p for p in urlparse(url).path.split("/") if p]
            section = path_parts[0].replace("-", " ").replace("_", " ").title() if path_parts else "Homepage"
        except Exception:
            section = "Other"
        
        section_data.append({
            "section": section[:20],
            "title": title[:30],
            "depth": depth,
            "children": child_count + 1,
        })

    section_df = pd.DataFrame(section_data)
    
    # Aggregate by section
    agg_df = section_df.groupby("section").agg({
        "children": "sum",
        "depth": "mean",
    }).reset_index()
    
    agg_df = agg_df.nlargest(12, "children")

    colors = ["#3B82F6", "#8B5CF6", "#EC4899", "#F59E0B", "#10B981", "#06B6D4", 
              "#6366F1", "#84CC16", "#F97316", "#14B8A6", "#A855F7", "#EF4444"]

    fig = go.Figure(
        data=[
            go.Treemap(
                labels=agg_df["section"].tolist(),
                parents=[""] * len(agg_df),
                values=agg_df["children"].tolist(),
                textinfo="label+value",
                textfont=dict(size=14, color="#E2E8F0"),
                marker=dict(
                    colors=colors[:len(agg_df)],
                    line=dict(width=2, color="#0F172A"),
                ),
                hovertemplate="<b>%{label}</b><br>Pages: %{value}<extra></extra>",
            )
        ],
        layout=go.Layout(
            margin=dict(l=10, r=10, t=10, b=10),
            paper_bgcolor="#0F172A",
            plot_bgcolor="#0F172A",
        ),
    )

    return fig.to_json()


# ---------------------------------------------------------------------------
# HTML Template with shadcn/ui Components
# ---------------------------------------------------------------------------

SHADCN_DASHBOARD_HTML = '''
<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TSM Website Structure Dashboard</title>
    
    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    
    <!-- Plotly.js -->
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    
    <!-- Font Awesome -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <!-- Google Fonts -->
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    
    <!-- Tailwind Config -->
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    fontFamily: {
                        sans: ['Inter', 'system-ui', 'sans-serif'],
                    },
                    colors: {
                        slate: {
                            850: '#172033',
                        }
                    }
                }
            }
        }
    </script>
    
    <style>
        /* Custom scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        ::-webkit-scrollbar-track {
            background: #1E293B;
        }
        ::-webkit-scrollbar-thumb {
            background: #475569;
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #64748B;
        }
        
        /* Smooth transitions */
        * {
            transition-property: color, background-color, border-color, box-shadow;
            transition-duration: 150ms;
        }
        
        /* Tab content animation */
        .tab-content {
            display: none;
            animation: fadeIn 0.3s ease;
        }
        .tab-content.active {
            display: block;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(8px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        /* Card hover effect */
        .card-hover:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
        }
        
        /* Gradient text */
        .gradient-text {
            background: linear-gradient(135deg, #3B82F6 0%, #8B5CF6 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        /* Pulse animation for live indicator */
        .pulse {
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        /* Progress bar animation */
        .progress-bar {
            transition: width 1s ease-in-out;
        }
        
        /* Table row hover */
        .table-row-hover:hover {
            background-color: rgba(59, 130, 246, 0.1);
        }
        
        /* Light mode overrides */
        html:not(.dark) body {
            background-color: #F8FAFC;
        }
        html:not(.dark) .bg-slate-900 {
            background-color: #FFFFFF;
        }
        html:not(.dark) .bg-slate-800 {
            background-color: #F1F5F9;
        }
        html:not(.dark) .text-slate-50 {
            color: #0F172A;
        }
        html:not(.dark) .text-slate-400 {
            color: #64748B;
        }
        html:not(.dark) .border-slate-700 {
            border-color: #E2E8F0;
        }
    </style>
</head>
<body class="bg-slate-900 text-slate-50 font-sans min-h-screen">
    <!-- Header -->
    <header class="sticky top-0 z-50 w-full border-b border-slate-700 bg-slate-900/95 backdrop-blur supports-[backdrop-filter]:bg-slate-900/60">
        <div class="container mx-auto flex h-16 max-w-screen-2xl items-center justify-between px-4">
            <!-- Left: Logo + Title -->
            <div class="flex items-center gap-3">
                <div class="rounded-xl bg-gradient-to-br from-blue-600 to-purple-600 p-2.5 shadow-lg shadow-blue-500/20">
                    <i class="fas fa-globe text-white text-xl"></i>
                </div>
                <div>
                    <h1 class="text-lg font-bold text-slate-50">TSM Website Structure</h1>
                    <p class="text-xs text-slate-400">Analysis Dashboard</p>
                </div>
            </div>
            
            <!-- Center: Status -->
            <div class="hidden md:flex items-center gap-4">
                <div class="flex items-center gap-2">
                    <span class="relative flex h-2 w-2">
                        <span class="pulse absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                        <span class="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                    </span>
                    <span class="text-sm text-slate-400">Live</span>
                </div>
                <div class="h-4 w-px bg-slate-700"></div>
                <div class="text-sm">
                    <span class="text-slate-400">Updated:</span>
                    <span class="text-blue-400 font-medium ml-1">{{ timestamp }}</span>
                </div>
            </div>
            
            <!-- Right: Controls -->
            <div class="flex items-center gap-2">
                <button onclick="refreshData()" class="inline-flex items-center justify-center rounded-lg p-2.5 text-slate-400 hover:text-slate-50 hover:bg-slate-800 transition-colors" title="Refresh Data">
                    <i class="fas fa-sync-alt"></i>
                </button>
                <button onclick="toggleTheme()" class="inline-flex items-center justify-center rounded-lg p-2.5 text-slate-400 hover:text-slate-50 hover:bg-slate-800 transition-colors" title="Toggle Theme" id="themeBtn">
                    <i class="fas fa-moon"></i>
                </button>
                <div class="relative group">
                    <button class="inline-flex items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-blue-700 transition-colors shadow-lg shadow-blue-500/20">
                        <i class="fas fa-download"></i>
                        <span class="hidden sm:inline">Export</span>
                    </button>
                    <div class="absolute right-0 mt-2 w-48 rounded-lg bg-slate-800 border border-slate-700 shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-50">
                        <a href="/download-report" class="flex items-center gap-2 px-4 py-2.5 text-sm text-slate-300 hover:bg-slate-700 rounded-t-lg">
                            <i class="fas fa-file-alt w-4"></i> Export Report (TXT)
                        </a>
                        <a href="/download-data" class="flex items-center gap-2 px-4 py-2.5 text-sm text-slate-300 hover:bg-slate-700 rounded-b-lg">
                            <i class="fas fa-table w-4"></i> Export Data (CSV)
                        </a>
                    </div>
                </div>
            </div>
        </div>
    </header>
    
    <!-- Main Content -->
    <main class="container mx-auto max-w-screen-2xl px-4 py-6">
        <!-- Tabs Navigation -->
        <div class="border-b border-slate-700 mb-6">
            <nav class="flex gap-1 overflow-x-auto pb-px" role="tablist">
                <button role="tab" aria-selected="true" data-tab="overview" class="tab-btn px-4 py-3 text-sm font-medium border-b-2 border-blue-500 text-blue-400 hover:text-blue-300 transition-colors whitespace-nowrap">
                    <i class="fas fa-chart-line mr-2"></i>Overview
                </button>
                <button role="tab" aria-selected="false" data-tab="network" class="tab-btn px-4 py-3 text-sm font-medium border-b-2 border-transparent text-slate-400 hover:text-slate-300 transition-colors whitespace-nowrap">
                    <i class="fas fa-project-diagram mr-2"></i>Network
                </button>
                <button role="tab" aria-selected="false" data-tab="statistics" class="tab-btn px-4 py-3 text-sm font-medium border-b-2 border-transparent text-slate-400 hover:text-slate-300 transition-colors whitespace-nowrap">
                    <i class="fas fa-chart-bar mr-2"></i>Statistics
                </button>
                <button role="tab" aria-selected="false" data-tab="audit" class="tab-btn px-4 py-3 text-sm font-medium border-b-2 border-transparent text-slate-400 hover:text-slate-300 transition-colors whitespace-nowrap">
                    <i class="fas fa-clipboard-check mr-2"></i>Audit Report
                </button>
                <button role="tab" aria-selected="false" data-tab="data" class="tab-btn px-4 py-3 text-sm font-medium border-b-2 border-transparent text-slate-400 hover:text-slate-300 transition-colors whitespace-nowrap">
                    <i class="fas fa-table mr-2"></i>Data Table
                </button>
                <button role="tab" aria-selected="false" data-tab="mindmap" class="tab-btn px-4 py-3 text-sm font-medium border-b-2 border-transparent text-slate-400 hover:text-slate-300 transition-colors whitespace-nowrap">
                    <i class="fas fa-sitemap mr-2"></i>Mind Map
                </button>
            </nav>
        </div>
        
        <!-- ============================================================ -->
        <!-- TAB 1: OVERVIEW -->
        <!-- ============================================================ -->
        <div class="tab-content active" id="tab-overview">
            <!-- Summary Cards -->
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                <!-- Card 1: Total Pages -->
                <div class="rounded-xl border border-slate-700 bg-slate-800 p-5 card-hover transition-all">
                    <div class="flex items-start justify-between">
                        <div>
                            <p class="text-sm font-medium text-slate-400">Total Pages</p>
                            <p class="text-3xl font-bold text-slate-50 mt-1">{{ stats.total_pages }}</p>
                            <p class="text-xs text-slate-500 mt-1">Comprehensive crawl</p>
                        </div>
                        <div class="rounded-lg bg-blue-500/10 p-3">
                            <i class="fas fa-globe text-xl text-blue-400"></i>
                        </div>
                    </div>
                </div>
                
                <!-- Card 2: IA Score -->
                <div class="rounded-xl border border-slate-700 bg-slate-800 p-5 card-hover transition-all">
                    <div class="flex items-start justify-between">
                        <div>
                            <p class="text-sm font-medium text-slate-400">Architecture Score</p>
                            <p class="text-3xl font-bold mt-1 {{ 'text-green-400' if ia_score.final_score >= 75 else 'text-amber-400' if ia_score.final_score >= 50 else 'text-red-400' }}">
                                {{ ia_score.final_score }}<span class="text-lg text-slate-500">/100</span>
                            </p>
                            <p class="text-xs text-slate-500 mt-1">{{ ia_score.health_status }}</p>
                        </div>
                        <div class="rounded-lg {{ 'bg-green-500/10' if ia_score.final_score >= 75 else 'bg-amber-500/10' if ia_score.final_score >= 50 else 'bg-red-500/10' }} p-3">
                            <i class="fas fa-star text-xl {{ 'text-green-400' if ia_score.final_score >= 75 else 'text-amber-400' if ia_score.final_score >= 50 else 'text-red-400' }}"></i>
                        </div>
                    </div>
                    <div class="mt-3 h-1.5 rounded-full bg-slate-700 overflow-hidden">
                        <div class="h-full rounded-full progress-bar {{ 'bg-green-500' if ia_score.final_score >= 75 else 'bg-amber-500' if ia_score.final_score >= 50 else 'bg-red-500' }}" style="width: {{ ia_score.final_score }}%"></div>
                    </div>
                </div>
                
                <!-- Card 3: Average Depth -->
                <div class="rounded-xl border border-slate-700 bg-slate-800 p-5 card-hover transition-all">
                    <div class="flex items-start justify-between">
                        <div>
                            <p class="text-sm font-medium text-slate-400">Average Depth</p>
                            <p class="text-3xl font-bold text-slate-50 mt-1">{{ stats.avg_depth }}</p>
                            <p class="text-xs text-slate-500 mt-1">{{ 'Optimal' if stats.avg_depth <= 3 else 'Needs optimization' }}</p>
                        </div>
                        <div class="rounded-lg bg-amber-500/10 p-3">
                            <i class="fas fa-layer-group text-xl text-amber-400"></i>
                        </div>
                    </div>
                </div>
                
                <!-- Card 4: Health Status -->
                <div class="rounded-xl border border-slate-700 bg-slate-800 p-5 card-hover transition-all">
                    <div class="flex items-start justify-between">
                        <div>
                            <p class="text-sm font-medium text-slate-400">Health Status</p>
                            <div class="mt-2">
                                <span class="inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-medium {{ 'bg-green-500/10 text-green-400' if ia_score.health_status in ['Excellent', 'Good'] else 'bg-amber-500/10 text-amber-400' if ia_score.health_status == 'Needs Improvement' else 'bg-red-500/10 text-red-400' }}">
                                    <i class="fas {{ 'fa-check-circle' if ia_score.health_status in ['Excellent', 'Good'] else 'fa-exclamation-circle' }}"></i>
                                    {{ ia_score.health_status }}
                                </span>
                            </div>
                            <p class="text-xs text-slate-500 mt-2">Overall website health</p>
                        </div>
                        <div class="rounded-lg {{ 'bg-green-500/10' if ia_score.health_status in ['Excellent', 'Good'] else 'bg-amber-500/10' }} p-3">
                            <i class="fas fa-heartbeat text-xl {{ 'text-green-400' if ia_score.health_status in ['Excellent', 'Good'] else 'text-amber-400' }}"></i>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Three Column Layout -->
            <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
                <!-- Left Column: Metrics + Top Pages -->
                <div class="lg:col-span-3 space-y-4">
                    <!-- Key Metrics -->
                    <div class="rounded-xl border border-slate-700 bg-slate-800 p-5">
                        <h3 class="text-base font-semibold text-slate-50 mb-4 flex items-center gap-2">
                            <i class="fas fa-chart-pie text-blue-400"></i>
                            Key Metrics
                        </h3>
                        <div class="space-y-3">
                            <div class="flex justify-between items-center py-2 border-b border-slate-700/50">
                                <span class="text-sm text-slate-400">Max Depth</span>
                                <span class="text-sm font-semibold text-slate-200">{{ stats.max_depth }}</span>
                            </div>
                            <div class="flex justify-between items-center py-2 border-b border-slate-700/50">
                                <span class="text-sm text-slate-400">Orphan Pages</span>
                                <span class="text-sm font-semibold {{ 'text-green-400' if orphan_count == 0 else 'text-red-400' }}">{{ orphan_count }}</span>
                            </div>
                            <div class="flex justify-between items-center py-2 border-b border-slate-700/50">
                                <span class="text-sm text-slate-400">Dead Ends</span>
                                <span class="text-sm font-semibold {{ 'text-green-400' if dead_end_count < 5 else 'text-amber-400' }}">{{ dead_end_count }}</span>
                            </div>
                            <div class="flex justify-between items-center py-2 border-b border-slate-700/50">
                                <span class="text-sm text-slate-400">Bottlenecks</span>
                                <span class="text-sm font-semibold {{ 'text-green-400' if bottleneck_count == 0 else 'text-amber-400' }}">{{ bottleneck_count }}</span>
                            </div>
                            <div class="flex justify-between items-center py-2">
                                <span class="text-sm text-slate-400">Avg Links/Page</span>
                                <span class="text-sm font-semibold text-blue-400">{{ stats.avg_links }}</span>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Top Pages -->
                    <div class="rounded-xl border border-slate-700 bg-slate-800 p-5">
                        <h3 class="text-base font-semibold text-slate-50 mb-4 flex items-center gap-2">
                            <i class="fas fa-trophy text-amber-400"></i>
                            Top Pages
                        </h3>
                        <div class="space-y-2">
                            {% for page in top_pages[:5] %}
                            <div class="p-3 rounded-lg bg-slate-700/30 hover:bg-slate-700/50 transition-colors">
                                <p class="text-sm font-medium text-slate-200 truncate" title="{{ page.title }}">
                                    {{ page.title[:30] }}{% if page.title|length > 30 %}...{% endif %}
                                </p>
                                <div class="flex items-center gap-2 mt-1">
                                    <span class="text-xs text-blue-400">
                                        <i class="fas fa-link mr-1"></i>{{ page.child_count }} links
                                    </span>
                                    <span class="text-xs text-slate-500">•</span>
                                    <span class="text-xs text-slate-500">Rank #{{ loop.index }}</span>
                                </div>
                            </div>
                            {% endfor %}
                        </div>
                    </div>
                </div>
                
                <!-- Center Column: Network Graph -->
                <div class="lg:col-span-5">
                    <div class="rounded-xl border border-slate-700 bg-slate-800 p-5 h-full">
                        <div class="flex items-center justify-between mb-4">
                            <h3 class="text-base font-semibold text-slate-50 flex items-center gap-2">
                                <i class="fas fa-project-diagram text-blue-400"></i>
                                Site Structure
                            </h3>
                            <div class="flex gap-1">
                                <button onclick="resetNetworkView()" class="p-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-slate-400 hover:text-slate-200 transition-colors" title="Reset View">
                                    <i class="fas fa-compress-arrows-alt text-sm"></i>
                                </button>
                            </div>
                        </div>
                        <div class="relative rounded-lg bg-slate-900 overflow-hidden" style="height: 400px;">
                            <div id="networkGraphOverview" style="width: 100%; height: 100%;"></div>
                        </div>
                        <!-- Legend -->
                        <div class="flex flex-wrap gap-4 mt-4 text-xs text-slate-400">
                            <div class="flex items-center gap-1.5">
                                <span class="w-3 h-3 rounded-full bg-blue-500"></span>
                                <span>Shallow (0-1)</span>
                            </div>
                            <div class="flex items-center gap-1.5">
                                <span class="w-3 h-3 rounded-full bg-purple-500"></span>
                                <span>Medium (2-3)</span>
                            </div>
                            <div class="flex items-center gap-1.5">
                                <span class="w-3 h-3 rounded-full bg-pink-500"></span>
                                <span>Deep (4+)</span>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Right Column: Issues + Recommendations -->
                <div class="lg:col-span-4 space-y-4">
                    <!-- Issues Alert -->
                    {% if orphan_count > 0 or dead_end_count > 0 or bottleneck_count > 0 %}
                    <div class="rounded-xl border border-amber-500/30 bg-amber-500/10 p-4">
                        <div class="flex items-start gap-3">
                            <div class="rounded-lg bg-amber-500/20 p-2">
                                <i class="fas fa-exclamation-triangle text-amber-400"></i>
                            </div>
                            <div>
                                <h4 class="text-sm font-semibold text-amber-300">Issues Detected</h4>
                                <p class="text-xs text-amber-200/70 mt-1">
                                    Found {{ orphan_count + dead_end_count + bottleneck_count }} issues that need attention.
                                </p>
                            </div>
                        </div>
                    </div>
                    {% else %}
                    <div class="rounded-xl border border-green-500/30 bg-green-500/10 p-4">
                        <div class="flex items-start gap-3">
                            <div class="rounded-lg bg-green-500/20 p-2">
                                <i class="fas fa-check-circle text-green-400"></i>
                            </div>
                            <div>
                                <h4 class="text-sm font-semibold text-green-300">All Clear!</h4>
                                <p class="text-xs text-green-200/70 mt-1">
                                    No critical issues detected. Your site structure looks healthy.
                                </p>
                            </div>
                        </div>
                    </div>
                    {% endif %}
                    
                    <!-- Issues List -->
                    <div class="rounded-xl border border-slate-700 bg-slate-800 p-5">
                        <h3 class="text-base font-semibold text-slate-50 mb-4 flex items-center gap-2">
                            <i class="fas fa-exclamation-circle text-red-400"></i>
                            Issues Found
                        </h3>
                        <div class="space-y-2">
                            {% if orphan_count > 0 %}
                            <div class="flex items-center gap-3 p-3 rounded-lg bg-red-500/10 border-l-2 border-red-500">
                                <i class="fas fa-unlink text-red-400"></i>
                                <div>
                                    <p class="text-sm font-medium text-slate-200">{{ orphan_count }} orphan pages</p>
                                    <p class="text-xs text-slate-400">No inbound links</p>
                                </div>
                            </div>
                            {% endif %}
                            {% if dead_end_count > 0 %}
                            <div class="flex items-center gap-3 p-3 rounded-lg bg-amber-500/10 border-l-2 border-amber-500">
                                <i class="fas fa-sign-out-alt text-amber-400"></i>
                                <div>
                                    <p class="text-sm font-medium text-slate-200">{{ dead_end_count }} dead ends</p>
                                    <p class="text-xs text-slate-400">No outbound navigation</p>
                                </div>
                            </div>
                            {% endif %}
                            {% if bottleneck_count > 0 %}
                            <div class="flex items-center gap-3 p-3 rounded-lg bg-yellow-500/10 border-l-2 border-yellow-500">
                                <i class="fas fa-hourglass-half text-yellow-400"></i>
                                <div>
                                    <p class="text-sm font-medium text-slate-200">{{ bottleneck_count }} bottlenecks</p>
                                    <p class="text-xs text-slate-400">Hard to reach pages</p>
                                </div>
                            </div>
                            {% endif %}
                            {% if orphan_count == 0 and dead_end_count == 0 and bottleneck_count == 0 %}
                            <div class="flex items-center gap-3 p-3 rounded-lg bg-green-500/10 border-l-2 border-green-500">
                                <i class="fas fa-check text-green-400"></i>
                                <div>
                                    <p class="text-sm font-medium text-slate-200">No issues found</p>
                                    <p class="text-xs text-slate-400">Structure is well-organized</p>
                                </div>
                            </div>
                            {% endif %}
                        </div>
                    </div>
                    
                    <!-- Quick Wins -->
                    <div class="rounded-xl border border-slate-700 bg-slate-800 p-5">
                        <h3 class="text-base font-semibold text-slate-50 mb-4 flex items-center gap-2">
                            <i class="fas fa-lightbulb text-yellow-400"></i>
                            Quick Wins
                        </h3>
                        <div class="space-y-2">
                            {% for rec in recommendations.critical[:2] %}
                            <div class="p-3 rounded-lg bg-slate-700/30">
                                <div class="flex items-center gap-2 mb-1">
                                    <span class="inline-flex items-center rounded px-2 py-0.5 text-xs font-medium bg-red-500/20 text-red-400">
                                        Critical
                                    </span>
                                </div>
                                <p class="text-sm text-slate-300">{{ rec.action }}</p>
                            </div>
                            {% endfor %}
                            {% for rec in recommendations.important[:2] %}
                            <div class="p-3 rounded-lg bg-slate-700/30">
                                <div class="flex items-center gap-2 mb-1">
                                    <span class="inline-flex items-center rounded px-2 py-0.5 text-xs font-medium bg-amber-500/20 text-amber-400">
                                        Important
                                    </span>
                                </div>
                                <p class="text-sm text-slate-300">{{ rec.action }}</p>
                            </div>
                            {% endfor %}
                            {% if not recommendations.critical and not recommendations.important %}
                            <div class="p-3 rounded-lg bg-green-500/10">
                                <p class="text-sm text-green-300">
                                    <i class="fas fa-check-circle mr-2"></i>
                                    No urgent actions needed!
                                </p>
                            </div>
                            {% endif %}
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- ============================================================ -->
        <!-- TAB 2: NETWORK -->
        <!-- ============================================================ -->
        <div class="tab-content" id="tab-network">
            <div class="rounded-xl border border-slate-700 bg-slate-800 p-6">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-lg font-semibold text-slate-50 flex items-center gap-2">
                        <i class="fas fa-project-diagram text-blue-400"></i>
                        Interactive Network Visualization
                    </h3>
                    <div class="flex gap-2">
                        <button onclick="zoomIn()" class="px-3 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-slate-300 text-sm transition-colors">
                            <i class="fas fa-search-plus mr-1"></i> Zoom In
                        </button>
                        <button onclick="zoomOut()" class="px-3 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-slate-300 text-sm transition-colors">
                            <i class="fas fa-search-minus mr-1"></i> Zoom Out
                        </button>
                        <button onclick="resetNetworkView()" class="px-3 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-slate-300 text-sm transition-colors">
                            <i class="fas fa-sync-alt mr-1"></i> Reset
                        </button>
                        <button onclick="exportNetworkPNG()" class="px-3 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-sm transition-colors">
                            <i class="fas fa-download mr-1"></i> Export PNG
                        </button>
                    </div>
                </div>
                <div class="rounded-lg bg-slate-900 overflow-hidden" style="height: 600px;">
                    <div id="networkGraphFull" style="width: 100%; height: 100%;"></div>
                </div>
                
                <!-- Legend -->
                <div class="flex flex-wrap gap-6 mt-4 p-4 rounded-lg bg-slate-700/30">
                    <div class="flex items-center gap-2">
                        <span class="w-4 h-4 rounded-full bg-blue-500"></span>
                        <span class="text-sm text-slate-300">Depth 0-1 (Homepage/Main)</span>
                    </div>
                    <div class="flex items-center gap-2">
                        <span class="w-4 h-4 rounded-full bg-purple-500"></span>
                        <span class="text-sm text-slate-300">Depth 2-3 (Section Pages)</span>
                    </div>
                    <div class="flex items-center gap-2">
                        <span class="w-4 h-4 rounded-full bg-pink-500"></span>
                        <span class="text-sm text-slate-300">Depth 4+ (Deep Pages)</span>
                    </div>
                    <div class="flex items-center gap-2 text-slate-400 text-sm">
                        <i class="fas fa-info-circle"></i>
                        Node size represents link count
                    </div>
                </div>
            </div>
        </div>
        
        <!-- ============================================================ -->
        <!-- TAB 3: STATISTICS -->
        <!-- ============================================================ -->
        <div class="tab-content" id="tab-statistics">
            <!-- Charts Row -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                <!-- Depth Distribution -->
                <div class="rounded-xl border border-slate-700 bg-slate-800 p-6">
                    <h3 class="text-base font-semibold text-slate-50 mb-4 flex items-center gap-2">
                        <i class="fas fa-chart-bar text-blue-400"></i>
                        Pages by Depth Level
                    </h3>
                    <div id="depthChart" style="height: 300px;"></div>
                </div>
                
                <!-- Section Distribution -->
                <div class="rounded-xl border border-slate-700 bg-slate-800 p-6">
                    <h3 class="text-base font-semibold text-slate-50 mb-4 flex items-center gap-2">
                        <i class="fas fa-chart-pie text-purple-400"></i>
                        Content Distribution
                    </h3>
                    <div id="sectionChart" style="height: 300px;"></div>
                </div>
            </div>
            
            <!-- Metrics Cards -->
            <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                <div class="rounded-xl border border-slate-700 bg-slate-800 p-5 text-center">
                    <p class="text-3xl font-bold text-blue-400">{{ (stats.total_pages / (stats.max_depth + 1)) | round(1) }}</p>
                    <p class="text-sm text-slate-400 mt-1">Breadth (avg/depth)</p>
                </div>
                <div class="rounded-xl border border-slate-700 bg-slate-800 p-5 text-center">
                    <p class="text-3xl font-bold text-purple-400">0 - {{ stats.max_depth }}</p>
                    <p class="text-sm text-slate-400 mt-1">Depth Range</p>
                </div>
                <div class="rounded-xl border border-slate-700 bg-slate-800 p-5 text-center">
                    <p class="text-3xl font-bold text-amber-400">{{ stats.avg_links }}</p>
                    <p class="text-sm text-slate-400 mt-1">Link Density</p>
                </div>
                <div class="rounded-xl border border-slate-700 bg-slate-800 p-5 text-center">
                    <p class="text-3xl font-bold text-green-400">{{ ia_score.breakdown.connectivity_score }}%</p>
                    <p class="text-sm text-slate-400 mt-1">Connectivity</p>
                </div>
            </div>
            
            <!-- Metrics Table -->
            <div class="rounded-xl border border-slate-700 bg-slate-800 overflow-hidden">
                <div class="p-5 border-b border-slate-700">
                    <h3 class="text-base font-semibold text-slate-50 flex items-center gap-2">
                        <i class="fas fa-table text-blue-400"></i>
                        Detailed Metrics Comparison
                    </h3>
                </div>
                <div class="overflow-x-auto">
                    <table class="w-full">
                        <thead class="bg-slate-700/50">
                            <tr>
                                <th class="px-5 py-3 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider">Metric</th>
                                <th class="px-5 py-3 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider">Current</th>
                                <th class="px-5 py-3 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider">Best Practice</th>
                                <th class="px-5 py-3 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider">Status</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-slate-700">
                            <tr class="table-row-hover">
                                <td class="px-5 py-4 text-sm font-medium text-slate-200">Max Depth</td>
                                <td class="px-5 py-4 text-sm text-slate-300">{{ stats.max_depth }}</td>
                                <td class="px-5 py-4 text-sm text-slate-400">≤ 4</td>
                                <td class="px-5 py-4">
                                    {% if stats.max_depth <= 4 %}
                                    <span class="inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium bg-green-500/10 text-green-400">
                                        <i class="fas fa-check"></i> Good
                                    </span>
                                    {% else %}
                                    <span class="inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium bg-amber-500/10 text-amber-400">
                                        <i class="fas fa-exclamation"></i> Review
                                    </span>
                                    {% endif %}
                                </td>
                            </tr>
                            <tr class="table-row-hover">
                                <td class="px-5 py-4 text-sm font-medium text-slate-200">Average Depth</td>
                                <td class="px-5 py-4 text-sm text-slate-300">{{ stats.avg_depth }}</td>
                                <td class="px-5 py-4 text-sm text-slate-400">≤ 3.0</td>
                                <td class="px-5 py-4">
                                    {% if stats.avg_depth <= 3 %}
                                    <span class="inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium bg-green-500/10 text-green-400">
                                        <i class="fas fa-check"></i> Good
                                    </span>
                                    {% else %}
                                    <span class="inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium bg-amber-500/10 text-amber-400">
                                        <i class="fas fa-exclamation"></i> Review
                                    </span>
                                    {% endif %}
                                </td>
                            </tr>
                            <tr class="table-row-hover">
                                <td class="px-5 py-4 text-sm font-medium text-slate-200">IA Score</td>
                                <td class="px-5 py-4 text-sm text-slate-300">{{ ia_score.final_score }}/100</td>
                                <td class="px-5 py-4 text-sm text-slate-400">≥ 75</td>
                                <td class="px-5 py-4">
                                    {% if ia_score.final_score >= 75 %}
                                    <span class="inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium bg-green-500/10 text-green-400">
                                        <i class="fas fa-check"></i> {{ ia_score.health_status }}
                                    </span>
                                    {% elif ia_score.final_score >= 50 %}
                                    <span class="inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium bg-amber-500/10 text-amber-400">
                                        <i class="fas fa-exclamation"></i> {{ ia_score.health_status }}
                                    </span>
                                    {% else %}
                                    <span class="inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium bg-red-500/10 text-red-400">
                                        <i class="fas fa-times"></i> {{ ia_score.health_status }}
                                    </span>
                                    {% endif %}
                                </td>
                            </tr>
                            <tr class="table-row-hover">
                                <td class="px-5 py-4 text-sm font-medium text-slate-200">Orphan Pages</td>
                                <td class="px-5 py-4 text-sm text-slate-300">{{ orphan_count }}</td>
                                <td class="px-5 py-4 text-sm text-slate-400">0</td>
                                <td class="px-5 py-4">
                                    {% if orphan_count == 0 %}
                                    <span class="inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium bg-green-500/10 text-green-400">
                                        <i class="fas fa-check"></i> Good
                                    </span>
                                    {% else %}
                                    <span class="inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium bg-red-500/10 text-red-400">
                                        <i class="fas fa-times"></i> Fix Required
                                    </span>
                                    {% endif %}
                                </td>
                            </tr>
                            <tr class="table-row-hover">
                                <td class="px-5 py-4 text-sm font-medium text-slate-200">Dead Ends</td>
                                <td class="px-5 py-4 text-sm text-slate-300">{{ dead_end_count }}</td>
                                <td class="px-5 py-4 text-sm text-slate-400">< 10%</td>
                                <td class="px-5 py-4">
                                    {% if dead_end_count < stats.total_pages * 0.1 %}
                                    <span class="inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium bg-green-500/10 text-green-400">
                                        <i class="fas fa-check"></i> Good
                                    </span>
                                    {% else %}
                                    <span class="inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium bg-amber-500/10 text-amber-400">
                                        <i class="fas fa-exclamation"></i> Review
                                    </span>
                                    {% endif %}
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        
        <!-- ============================================================ -->
        <!-- TAB 4: AUDIT REPORT -->
        <!-- ============================================================ -->
        <div class="tab-content" id="tab-audit">
            <!-- Export Controls -->
            <div class="flex justify-end gap-2 mb-6">
                <a href="/download-report" class="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-slate-300 text-sm transition-colors">
                    <i class="fas fa-file-alt"></i> Export TXT
                </a>
                <button onclick="window.print()" class="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-sm transition-colors">
                    <i class="fas fa-print"></i> Print Report
                </button>
            </div>
            
            <!-- Executive Summary -->
            <div class="rounded-xl border border-slate-700 bg-slate-800 mb-4 overflow-hidden">
                <button onclick="toggleSection(this)" class="w-full flex items-center justify-between p-5 hover:bg-slate-700/50 transition-colors">
                    <h3 class="text-base font-semibold text-slate-50 flex items-center gap-2">
                        <i class="fas fa-clipboard-list text-blue-400"></i>
                        Executive Summary
                    </h3>
                    <i class="fas fa-chevron-down text-slate-400 transition-transform section-icon"></i>
                </button>
                <div class="section-content px-5 pb-5">
                    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
                        <div class="p-4 rounded-lg bg-slate-700/30 text-center">
                            <p class="text-2xl font-bold text-blue-400">{{ ia_score.final_score }}/100</p>
                            <p class="text-xs text-slate-400 mt-1">IA Score</p>
                        </div>
                        <div class="p-4 rounded-lg bg-slate-700/30 text-center">
                            <p class="text-2xl font-bold text-slate-200">{{ stats.total_pages }}</p>
                            <p class="text-xs text-slate-400 mt-1">Total Pages</p>
                        </div>
                        <div class="p-4 rounded-lg bg-slate-700/30 text-center">
                            <p class="text-2xl font-bold text-slate-200">{{ stats.max_depth }}</p>
                            <p class="text-xs text-slate-400 mt-1">Max Depth</p>
                        </div>
                        <div class="p-4 rounded-lg bg-slate-700/30 text-center">
                            <p class="text-2xl font-bold {{ 'text-green-400' if ia_score.health_status in ['Excellent', 'Good'] else 'text-amber-400' }}">{{ ia_score.health_status }}</p>
                            <p class="text-xs text-slate-400 mt-1">Status</p>
                        </div>
                    </div>
                    <p class="text-sm text-slate-400">{{ ia_score.interpretation }}</p>
                </div>
            </div>
            
            <!-- Critical Issues -->
            <div class="rounded-xl border border-slate-700 bg-slate-800 mb-4 overflow-hidden">
                <button onclick="toggleSection(this)" class="w-full flex items-center justify-between p-5 hover:bg-slate-700/50 transition-colors">
                    <h3 class="text-base font-semibold text-slate-50 flex items-center gap-2">
                        <i class="fas fa-exclamation-circle text-red-400"></i>
                        Critical Issues ({{ orphan_count + dead_end_count + bottleneck_count }})
                    </h3>
                    <i class="fas fa-chevron-down text-slate-400 transition-transform section-icon"></i>
                </button>
                <div class="section-content px-5 pb-5 hidden">
                    <div class="space-y-3">
                        {% if orphan_count > 0 %}
                        <div class="p-4 rounded-lg bg-red-500/10 border-l-4 border-red-500">
                            <p class="text-sm font-medium text-slate-200"><i class="fas fa-unlink mr-2 text-red-400"></i>Orphan Pages: {{ orphan_count }}</p>
                            <p class="text-xs text-slate-400 mt-1">Pages with no inbound links. Add internal links to improve SEO.</p>
                        </div>
                        {% endif %}
                        {% if dead_end_count > 0 %}
                        <div class="p-4 rounded-lg bg-amber-500/10 border-l-4 border-amber-500">
                            <p class="text-sm font-medium text-slate-200"><i class="fas fa-sign-out-alt mr-2 text-amber-400"></i>Dead-End Pages: {{ dead_end_count }}</p>
                            <p class="text-xs text-slate-400 mt-1">Pages with no outbound navigation. Add related links.</p>
                        </div>
                        {% endif %}
                        {% if bottleneck_count > 0 %}
                        <div class="p-4 rounded-lg bg-yellow-500/10 border-l-4 border-yellow-500">
                            <p class="text-sm font-medium text-slate-200"><i class="fas fa-hourglass-half mr-2 text-yellow-400"></i>Navigation Bottlenecks: {{ bottleneck_count }}</p>
                            <p class="text-xs text-slate-400 mt-1">Pages requiring more than 3 clicks to reach.</p>
                        </div>
                        {% endif %}
                        {% if orphan_count == 0 and dead_end_count == 0 and bottleneck_count == 0 %}
                        <div class="p-4 rounded-lg bg-green-500/10 border-l-4 border-green-500">
                            <p class="text-sm font-medium text-slate-200"><i class="fas fa-check-circle mr-2 text-green-400"></i>No Critical Issues Found!</p>
                            <p class="text-xs text-slate-400 mt-1">Your website structure is well-organized.</p>
                        </div>
                        {% endif %}
                    </div>
                </div>
            </div>
            
            <!-- Recommendations -->
            <div class="rounded-xl border border-slate-700 bg-slate-800 mb-4 overflow-hidden">
                <button onclick="toggleSection(this)" class="w-full flex items-center justify-between p-5 hover:bg-slate-700/50 transition-colors">
                    <h3 class="text-base font-semibold text-slate-50 flex items-center gap-2">
                        <i class="fas fa-lightbulb text-yellow-400"></i>
                        Recommendations
                    </h3>
                    <i class="fas fa-chevron-down text-slate-400 transition-transform section-icon"></i>
                </button>
                <div class="section-content px-5 pb-5 hidden">
                    {% if recommendations.critical %}
                    <h4 class="text-sm font-semibold text-red-400 mb-3"><i class="fas fa-fire mr-2"></i>Critical (Do This Week)</h4>
                    <div class="space-y-2 mb-4">
                        {% for rec in recommendations.critical %}
                        <div class="p-3 rounded-lg bg-slate-700/30">
                            <span class="inline-flex items-center rounded px-2 py-0.5 text-xs font-medium bg-red-500/20 text-red-400 mb-2">Critical</span>
                            <p class="text-sm text-slate-300">{{ rec.action }}</p>
                            <p class="text-xs text-slate-500 mt-1">Effort: {{ rec.effort_estimate }} | Impact: {{ rec.expected_impact }}</p>
                        </div>
                        {% endfor %}
                    </div>
                    {% endif %}
                    
                    {% if recommendations.important %}
                    <h4 class="text-sm font-semibold text-amber-400 mb-3"><i class="fas fa-exclamation-triangle mr-2"></i>Important (Do This Month)</h4>
                    <div class="space-y-2 mb-4">
                        {% for rec in recommendations.important %}
                        <div class="p-3 rounded-lg bg-slate-700/30">
                            <span class="inline-flex items-center rounded px-2 py-0.5 text-xs font-medium bg-amber-500/20 text-amber-400 mb-2">Important</span>
                            <p class="text-sm text-slate-300">{{ rec.action }}</p>
                            <p class="text-xs text-slate-500 mt-1">Effort: {{ rec.effort_estimate }} | Difficulty: {{ rec.difficulty }}</p>
                        </div>
                        {% endfor %}
                    </div>
                    {% endif %}
                    
                    {% if recommendations.nice_to_have %}
                    <h4 class="text-sm font-semibold text-green-400 mb-3"><i class="fas fa-star mr-2"></i>Nice to Have (Long Term)</h4>
                    <div class="space-y-2">
                        {% for rec in recommendations.nice_to_have %}
                        <div class="p-3 rounded-lg bg-slate-700/30">
                            <span class="inline-flex items-center rounded px-2 py-0.5 text-xs font-medium bg-green-500/20 text-green-400 mb-2">Enhancement</span>
                            <p class="text-sm text-slate-300">{{ rec.action }}</p>
                        </div>
                        {% endfor %}
                    </div>
                    {% endif %}
                </div>
            </div>
            
            <!-- Score Breakdown -->
            <div class="rounded-xl border border-slate-700 bg-slate-800 overflow-hidden">
                <button onclick="toggleSection(this)" class="w-full flex items-center justify-between p-5 hover:bg-slate-700/50 transition-colors">
                    <h3 class="text-base font-semibold text-slate-50 flex items-center gap-2">
                        <i class="fas fa-chart-line text-green-400"></i>
                        IA Score Breakdown
                    </h3>
                    <i class="fas fa-chevron-down text-slate-400 transition-transform section-icon"></i>
                </button>
                <div class="section-content px-5 pb-5 hidden">
                    <div class="grid grid-cols-3 gap-4">
                        <div class="p-4 rounded-lg bg-slate-700/30 text-center">
                            <p class="text-2xl font-bold text-blue-400">{{ ia_score.breakdown.depth_score }}</p>
                            <p class="text-xs text-slate-400 mt-1">Depth Score</p>
                            <div class="mt-2 h-1 rounded-full bg-slate-600 overflow-hidden">
                                <div class="h-full bg-blue-500" style="width: {{ ia_score.breakdown.depth_score }}%"></div>
                            </div>
                        </div>
                        <div class="p-4 rounded-lg bg-slate-700/30 text-center">
                            <p class="text-2xl font-bold text-purple-400">{{ ia_score.breakdown.balance_score }}</p>
                            <p class="text-xs text-slate-400 mt-1">Balance Score</p>
                            <div class="mt-2 h-1 rounded-full bg-slate-600 overflow-hidden">
                                <div class="h-full bg-purple-500" style="width: {{ ia_score.breakdown.balance_score }}%"></div>
                            </div>
                        </div>
                        <div class="p-4 rounded-lg bg-slate-700/30 text-center">
                            <p class="text-2xl font-bold text-green-400">{{ ia_score.breakdown.connectivity_score }}</p>
                            <p class="text-xs text-slate-400 mt-1">Connectivity Score</p>
                            <div class="mt-2 h-1 rounded-full bg-slate-600 overflow-hidden">
                                <div class="h-full bg-green-500" style="width: {{ ia_score.breakdown.connectivity_score }}%"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- ============================================================ -->
        <!-- TAB 5: DATA TABLE -->
        <!-- ============================================================ -->
        <div class="tab-content" id="tab-data">
            <div class="rounded-xl border border-slate-700 bg-slate-800 overflow-hidden">
                <!-- Table Controls -->
                <div class="p-4 border-b border-slate-700 flex flex-wrap gap-3 items-center bg-slate-800/50">
                    <div class="flex-1 min-w-[200px]">
                        <input type="text" id="tableSearch" placeholder="Search URLs, titles..." 
                            class="w-full px-4 py-2.5 rounded-lg bg-slate-700 border border-slate-600 text-slate-200 placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 text-sm"
                            onkeyup="filterTable()">
                    </div>
                    <select id="depthFilter" onchange="filterTable()" class="px-4 py-2.5 rounded-lg bg-slate-700 border border-slate-600 text-slate-200 text-sm focus:outline-none focus:border-blue-500">
                        <option value="">All Depths</option>
                        {% for depth in range(stats.max_depth + 1) %}
                        <option value="{{ depth }}">Depth {{ depth }}</option>
                        {% endfor %}
                    </select>
                    <select id="statusFilter" onchange="filterTable()" class="px-4 py-2.5 rounded-lg bg-slate-700 border border-slate-600 text-slate-200 text-sm focus:outline-none focus:border-blue-500">
                        <option value="">All Status</option>
                        <option value="200">200 OK</option>
                        <option value="404">404 Not Found</option>
                    </select>
                    <a href="/download-data" class="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-sm transition-colors">
                        <i class="fas fa-download"></i> Export CSV
                    </a>
                </div>
                
                <!-- Table -->
                <div class="overflow-x-auto max-h-[600px]">
                    <table class="w-full">
                        <thead class="bg-slate-700/50 sticky top-0">
                            <tr>
                                <th onclick="sortTable(0)" class="px-5 py-3 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider cursor-pointer hover:bg-slate-700">
                                    URL <i class="fas fa-sort ml-1 text-slate-500"></i>
                                </th>
                                <th onclick="sortTable(1)" class="px-5 py-3 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider cursor-pointer hover:bg-slate-700">
                                    Title <i class="fas fa-sort ml-1 text-slate-500"></i>
                                </th>
                                <th onclick="sortTable(2)" class="px-5 py-3 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider cursor-pointer hover:bg-slate-700">
                                    Depth <i class="fas fa-sort ml-1 text-slate-500"></i>
                                </th>
                                <th onclick="sortTable(3)" class="px-5 py-3 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider cursor-pointer hover:bg-slate-700">
                                    Links <i class="fas fa-sort ml-1 text-slate-500"></i>
                                </th>
                                <th onclick="sortTable(4)" class="px-5 py-3 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider cursor-pointer hover:bg-slate-700">
                                    Status <i class="fas fa-sort ml-1 text-slate-500"></i>
                                </th>
                            </tr>
                        </thead>
                        <tbody id="dataTableBody" class="divide-y divide-slate-700">
                            {% for row in table_data %}
                            <tr class="table-row-hover" data-depth="{{ row.depth }}" data-status="{{ row.status_code }}">
                                <td class="px-5 py-3 text-sm">
                                    <a href="{{ row.url }}" target="_blank" class="text-blue-400 hover:text-blue-300 truncate block max-w-xs" title="{{ row.url }}">
                                        {{ row.url[:50] }}{% if row.url|length > 50 %}...{% endif %}
                                    </a>
                                </td>
                                <td class="px-5 py-3 text-sm text-slate-300 truncate max-w-xs" title="{{ row.title }}">
                                    {{ row.title[:40] }}{% if row.title|length > 40 %}...{% endif %}
                                </td>
                                <td class="px-5 py-3 text-sm">
                                    <span class="inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium bg-blue-500/10 text-blue-400">
                                        {{ row.depth }}
                                    </span>
                                </td>
                                <td class="px-5 py-3 text-sm text-slate-300">{{ row.child_count }}</td>
                                <td class="px-5 py-3 text-sm">
                                    {% if row.status_code == 200 %}
                                    <span class="inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium bg-green-500/10 text-green-400">
                                        <i class="fas fa-check"></i> {{ row.status_code }}
                                    </span>
                                    {% elif row.status_code < 400 %}
                                    <span class="inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium bg-amber-500/10 text-amber-400">
                                        {{ row.status_code }}
                                    </span>
                                    {% else %}
                                    <span class="inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium bg-red-500/10 text-red-400">
                                        <i class="fas fa-times"></i> {{ row.status_code }}
                                    </span>
                                    {% endif %}
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                
                <!-- Pagination Info -->
                <div class="p-4 border-t border-slate-700 flex justify-between items-center text-sm text-slate-400">
                    <span>Showing <span id="visibleCount">{{ table_data|length }}</span> of {{ stats.total_pages }} entries</span>
                </div>
            </div>
        </div>
        
        <!-- ============================================================ -->
        <!-- TAB 6: MIND MAP -->
        <!-- ============================================================ -->
        <div class="tab-content" id="tab-mindmap">
            <!-- Mind Map Controls -->
            <div class="flex flex-wrap gap-3 items-center mb-6">
                <div class="flex gap-2">
                    <button onclick="setMindmapView('radial')" id="viewRadial" class="px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium transition-colors">
                        <i class="fas fa-circle-notch mr-2"></i>Radial View
                    </button>
                    <button onclick="setMindmapView('tree')" id="viewTree" class="px-4 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-slate-300 text-sm font-medium transition-colors">
                        <i class="fas fa-sitemap mr-2"></i>Tree View
                    </button>
                </div>
                <div class="flex-1"></div>
                <div class="flex gap-2">
                    <select id="mindmapDepthFilter" onchange="filterMindmapDepth()" class="px-4 py-2.5 rounded-lg bg-slate-700 border border-slate-600 text-slate-200 text-sm focus:outline-none focus:border-blue-500">
                        <option value="all">All Depths</option>
                        <option value="1">Depth 0-1</option>
                        <option value="2">Depth 0-2</option>
                        <option value="3">Depth 0-3</option>
                        <option value="4">Depth 0-4</option>
                    </select>
                    <button onclick="resetMindmapView()" class="px-4 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-slate-300 text-sm transition-colors">
                        <i class="fas fa-sync-alt mr-2"></i>Reset
                    </button>
                    <button onclick="exportMindmapPNG()" class="px-4 py-2 rounded-lg bg-green-600 hover:bg-green-700 text-white text-sm transition-colors">
                        <i class="fas fa-download mr-2"></i>Export PNG
                    </button>
                </div>
            </div>
            
            <!-- Mind Map Visualization -->
            <div class="grid grid-cols-1 lg:grid-cols-4 gap-6">
                <!-- Main Mind Map -->
                <div class="lg:col-span-3">
                    <div class="rounded-xl border border-slate-700 bg-slate-800 p-6">
                        <div class="flex items-center justify-between mb-4">
                            <h3 class="text-lg font-semibold text-slate-50 flex items-center gap-2">
                                <i class="fas fa-sitemap text-purple-400"></i>
                                Information Architecture Mind Map
                            </h3>
                            <div class="text-sm text-slate-400">
                                <span id="mindmapNodeCount">{{ stats.total_pages }}</span> pages visualized
                            </div>
                        </div>
                        <div class="rounded-lg bg-slate-900 overflow-hidden" style="height: 600px;">
                            <div id="mindmapGraph" style="width: 100%; height: 100%;"></div>
                        </div>
                        
                        <!-- Legend -->
                        <div class="flex flex-wrap gap-4 mt-4 p-4 rounded-lg bg-slate-700/30">
                            <div class="flex items-center gap-2">
                                <span class="w-4 h-4 rounded-full bg-blue-500"></span>
                                <span class="text-sm text-slate-300">🏠 Homepage</span>
                            </div>
                            <div class="flex items-center gap-2">
                                <span class="w-4 h-4 rounded-full bg-green-500"></span>
                                <span class="text-sm text-slate-300">📁 Main Sections</span>
                            </div>
                            <div class="flex items-center gap-2">
                                <span class="w-4 h-4 rounded-full bg-amber-500"></span>
                                <span class="text-sm text-slate-300">📄 Subsections</span>
                            </div>
                            <div class="flex items-center gap-2">
                                <span class="w-4 h-4 rounded-full bg-orange-500"></span>
                                <span class="text-sm text-slate-300">📝 Detail Pages</span>
                            </div>
                            <div class="flex items-center gap-2">
                                <span class="w-4 h-4 rounded-full bg-red-500"></span>
                                <span class="text-sm text-slate-300">📎 Deep Pages</span>
                            </div>
                            <div class="flex items-center gap-2 ml-auto text-slate-400 text-sm">
                                <i class="fas fa-info-circle"></i>
                                Node size = number of child links
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Side Panel -->
                <div class="lg:col-span-1 space-y-4">
                    <!-- Structure Summary -->
                    <div class="rounded-xl border border-slate-700 bg-slate-800 p-5">
                        <h3 class="text-base font-semibold text-slate-50 mb-4 flex items-center gap-2">
                            <i class="fas fa-layer-group text-blue-400"></i>
                            Structure Summary
                        </h3>
                        <div class="space-y-3">
                            {% for depth, count in stats.pages_by_depth.items() %}
                            <div class="flex justify-between items-center py-2 border-b border-slate-700/50">
                                <span class="text-sm text-slate-400 flex items-center gap-2">
                                    <span class="w-3 h-3 rounded-full" style="background-color: {{ ['#3B82F6', '#10B981', '#F59E0B', '#FB923C', '#EF4444'][depth|int if depth|int < 5 else 4] }}"></span>
                                    Depth {{ depth }}
                                </span>
                                <span class="text-sm font-semibold text-slate-200">{{ count }} pages</span>
                            </div>
                            {% endfor %}
                        </div>
                    </div>
                    
                    <!-- Treemap -->
                    <div class="rounded-xl border border-slate-700 bg-slate-800 p-5">
                        <h3 class="text-base font-semibold text-slate-50 mb-4 flex items-center gap-2">
                            <i class="fas fa-th-large text-amber-400"></i>
                            Content Treemap
                        </h3>
                        <div id="treemapChart" style="height: 250px;"></div>
                    </div>
                    
                    <!-- Quick Stats -->
                    <div class="rounded-xl border border-slate-700 bg-slate-800 p-5">
                        <h3 class="text-base font-semibold text-slate-50 mb-4 flex items-center gap-2">
                            <i class="fas fa-chart-pie text-green-400"></i>
                            Quick Stats
                        </h3>
                        <div class="space-y-3">
                            <div class="flex justify-between items-center">
                                <span class="text-sm text-slate-400">Total Pages</span>
                                <span class="text-lg font-bold text-blue-400">{{ stats.total_pages }}</span>
                            </div>
                            <div class="flex justify-between items-center">
                                <span class="text-sm text-slate-400">Max Depth</span>
                                <span class="text-lg font-bold text-amber-400">{{ stats.max_depth }}</span>
                            </div>
                            <div class="flex justify-between items-center">
                                <span class="text-sm text-slate-400">Avg Links/Page</span>
                                <span class="text-lg font-bold text-green-400">{{ stats.avg_links }}</span>
                            </div>
                            <div class="flex justify-between items-center">
                                <span class="text-sm text-slate-400">IA Score</span>
                                <span class="text-lg font-bold {{ 'text-green-400' if ia_score.final_score >= 75 else 'text-amber-400' if ia_score.final_score >= 50 else 'text-red-400' }}">{{ ia_score.final_score }}/100</span>
                            </div>
                        </div>
                    </div>
                    
                    <!-- External Links -->
                    <div class="rounded-xl border border-slate-700 bg-slate-800 p-5">
                        <h3 class="text-base font-semibold text-slate-50 mb-4 flex items-center gap-2">
                            <i class="fas fa-external-link-alt text-purple-400"></i>
                            View Full Visualizations
                        </h3>
                        <div class="space-y-2">
                            <a href="/visualizations/mindmap" target="_blank" class="flex items-center gap-2 p-3 rounded-lg bg-slate-700/50 hover:bg-slate-700 text-slate-300 text-sm transition-colors">
                                <i class="fas fa-project-diagram text-blue-400"></i>
                                <span>Full Mind Map</span>
                                <i class="fas fa-arrow-right ml-auto text-slate-500"></i>
                            </a>
                            <a href="/visualizations/radial" target="_blank" class="flex items-center gap-2 p-3 rounded-lg bg-slate-700/50 hover:bg-slate-700 text-slate-300 text-sm transition-colors">
                                <i class="fas fa-circle-notch text-purple-400"></i>
                                <span>Radial View</span>
                                <i class="fas fa-arrow-right ml-auto text-slate-500"></i>
                            </a>
                            <a href="/visualizations/tree" target="_blank" class="flex items-center gap-2 p-3 rounded-lg bg-slate-700/50 hover:bg-slate-700 text-slate-300 text-sm transition-colors">
                                <i class="fas fa-sitemap text-green-400"></i>
                                <span>Tree Hierarchy</span>
                                <i class="fas fa-arrow-right ml-auto text-slate-500"></i>
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </main>
    
    <!-- Footer -->
    <footer class="border-t border-slate-700 mt-8 py-6 text-center text-sm text-slate-400">
        <p>TSM Website Structure Dashboard • Built with Flask, Plotly & Tailwind CSS</p>
        <p class="mt-1">
            <a href="/api/statistics" class="text-blue-400 hover:text-blue-300">API</a>
            <span class="mx-2">•</span>
            <a href="#" class="text-blue-400 hover:text-blue-300">Documentation</a>
        </p>
    </footer>
    
    <!-- JavaScript -->
    <script>
        // Chart data from server
        const networkData = {{ network_graph_json | safe }};
        const depthChartData = {{ depth_chart_json | safe }};
        const sectionChartData = {{ section_chart_json | safe }};
        const mindmapData = {{ mindmap_json | safe }};
        const treemapData = {{ treemap_json | safe }};
        
        // Initialize on page load
        document.addEventListener('DOMContentLoaded', function() {
            initCharts();
            initTabs();
        });
        
        function initCharts() {
            // Overview network graph
            if (networkData && Object.keys(networkData).length > 0) {
                Plotly.newPlot('networkGraphOverview', networkData.data, networkData.layout, {
                    responsive: true,
                    displayModeBar: false
                });
            }
            
            // Depth chart
            if (depthChartData && Object.keys(depthChartData).length > 0) {
                Plotly.newPlot('depthChart', depthChartData.data, depthChartData.layout, {
                    responsive: true,
                    displayModeBar: false
                });
            }
            
            // Section chart
            if (sectionChartData && Object.keys(sectionChartData).length > 0) {
                Plotly.newPlot('sectionChart', sectionChartData.data, sectionChartData.layout, {
                    responsive: true,
                    displayModeBar: false
                });
            }
        }
        
        function initTabs() {
            document.querySelectorAll('.tab-btn').forEach(btn => {
                btn.addEventListener('click', function() {
                    // Update tab buttons
                    document.querySelectorAll('.tab-btn').forEach(b => {
                        b.classList.remove('border-blue-500', 'text-blue-400');
                        b.classList.add('border-transparent', 'text-slate-400');
                        b.setAttribute('aria-selected', 'false');
                    });
                    this.classList.remove('border-transparent', 'text-slate-400');
                    this.classList.add('border-blue-500', 'text-blue-400');
                    this.setAttribute('aria-selected', 'true');
                    
                    // Update tab content
                    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                    document.getElementById('tab-' + this.dataset.tab).classList.add('active');
                    
                    // Initialize full network graph when network tab is selected
                    if (this.dataset.tab === 'network' && networkData) {
                        setTimeout(() => {
                            Plotly.newPlot('networkGraphFull', networkData.data, {
                                ...networkData.layout,
                                height: 580
                            }, {responsive: true});
                        }, 100);
                    }
                    
                    // Initialize mindmap when mindmap tab is selected
                    if (this.dataset.tab === 'mindmap') {
                        setTimeout(() => {
                            initMindmapCharts();
                        }, 100);
                    }
                });
            });
        }
        
        // Mind Map Functions
        let mindmapInitialized = false;
        
        function initMindmapCharts() {
            if (mindmapInitialized) return;
            
            // Mind map graph
            if (mindmapData && Object.keys(mindmapData).length > 0) {
                Plotly.newPlot('mindmapGraph', mindmapData.data, {
                    ...mindmapData.layout,
                    height: 580
                }, {responsive: true});
            }
            
            // Treemap chart
            if (treemapData && Object.keys(treemapData).length > 0) {
                Plotly.newPlot('treemapChart', treemapData.data, {
                    ...treemapData.layout,
                    height: 230
                }, {responsive: true});
            }
            
            mindmapInitialized = true;
        }
        
        function setMindmapView(view) {
            // Update button styles
            document.getElementById('viewRadial').className = view === 'radial' 
                ? 'px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium transition-colors'
                : 'px-4 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-slate-300 text-sm font-medium transition-colors';
            document.getElementById('viewTree').className = view === 'tree'
                ? 'px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium transition-colors'
                : 'px-4 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-slate-300 text-sm font-medium transition-colors';
            
            // For now, both views use the same Plotly visualization
            // In a full implementation, this would switch between different visualization types
            console.log('Switched to ' + view + ' view');
        }
        
        function filterMindmapDepth() {
            const depthValue = document.getElementById('mindmapDepthFilter').value;
            console.log('Filtering to depth: ' + depthValue);
            // In a full implementation, this would filter the visualization by depth
        }
        
        function resetMindmapView() {
            if (document.getElementById('mindmapGraph')) {
                Plotly.relayout('mindmapGraph', {
                    'xaxis.autorange': true,
                    'yaxis.autorange': true
                });
            }
        }
        
        function exportMindmapPNG() {
            Plotly.downloadImage('mindmapGraph', {
                format: 'png',
                width: 1400,
                height: 800,
                filename: 'tsm_mindmap'
            });
        }
        
        function toggleTheme() {
            document.documentElement.classList.toggle('dark');
            const btn = document.getElementById('themeBtn');
            const isDark = document.documentElement.classList.contains('dark');
            btn.innerHTML = isDark ? '<i class="fas fa-moon"></i>' : '<i class="fas fa-sun"></i>';
        }
        
        function toggleSection(btn) {
            const content = btn.nextElementSibling;
            const icon = btn.querySelector('.section-icon');
            content.classList.toggle('hidden');
            icon.style.transform = content.classList.contains('hidden') ? 'rotate(0deg)' : 'rotate(180deg)';
        }
        
        function refreshData() {
            window.location.href = '/?refresh=1';
        }
        
        function resetNetworkView() {
            const chartId = document.getElementById('networkGraphFull') ? 'networkGraphFull' : 'networkGraphOverview';
            Plotly.relayout(chartId, {
                'xaxis.autorange': true,
                'yaxis.autorange': true
            });
        }
        
        function zoomIn() {
            // Simplified zoom
            console.log('Zoom in');
        }
        
        function zoomOut() {
            // Simplified zoom
            console.log('Zoom out');
        }
        
        function exportNetworkPNG() {
            Plotly.downloadImage('networkGraphFull', {
                format: 'png',
                width: 1200,
                height: 800,
                filename: 'tsm_network_graph'
            });
        }
        
        function filterTable() {
            const search = document.getElementById('tableSearch').value.toLowerCase();
            const depthFilter = document.getElementById('depthFilter').value;
            const statusFilter = document.getElementById('statusFilter').value;
            
            const rows = document.querySelectorAll('#dataTableBody tr');
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
            
            document.getElementById('visibleCount').textContent = visibleCount;
        }
        
        let sortDirection = {};
        function sortTable(columnIndex) {
            const tbody = document.getElementById('dataTableBody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            
            sortDirection[columnIndex] = !sortDirection[columnIndex];
            const dir = sortDirection[columnIndex] ? 1 : -1;
            
            rows.sort((a, b) => {
                let aVal = a.cells[columnIndex].textContent.trim();
                let bVal = b.cells[columnIndex].textContent.trim();
                
                if (!isNaN(aVal) && !isNaN(bVal)) {
                    return (parseFloat(aVal) - parseFloat(bVal)) * dir;
                }
                return aVal.localeCompare(bVal) * dir;
            });
            
            rows.forEach(row => tbody.appendChild(row));
        }
    </script>
</body>
</html>
'''


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.route("/")
def dashboard_home():
    """Main dashboard route."""
    if request.args.get("refresh"):
        refresh_dashboard_data()

    data = get_dashboard_data()
    df = data["df_crawl"]
    audit_data = data["audit_data"]
    stats = data["stats"]

    ia_score = audit_data.get("ia_score", {
        "final_score": 0, "health_status": "Unknown", "interpretation": "",
        "breakdown": {"depth_score": 0, "balance_score": 0, "connectivity_score": 0}
    })
    orphan_pages = audit_data.get("orphan_pages", [])
    dead_ends = audit_data.get("dead_ends", [])
    bottlenecks = audit_data.get("bottlenecks", [])
    top_pages = audit_data.get("top_pages", [])
    recommendations = audit_data.get("recommendations", {"critical": [], "important": [], "nice_to_have": []})

    network_graph_json = create_network_graph_plotly(df, max_nodes=80)
    depth_chart_json = create_depth_bar_chart(stats)
    section_chart_json = create_section_pie_chart(audit_data)
    mindmap_json = create_mindmap_plotly(df, max_nodes=100)
    treemap_json = create_treemap_chart(df)

    table_data = df.to_dict("records") if not df.empty else []

    return render_template_string(
        SHADCN_DASHBOARD_HTML,
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
        mindmap_json=mindmap_json,
        treemap_json=treemap_json,
        table_data=table_data[:100],
    )


@app.route("/api/statistics")
def api_statistics():
    """API endpoint for statistics."""
    data = get_dashboard_data()
    stats = data["stats"]
    audit_data = data["audit_data"]

    return jsonify({
        "total_pages": stats.get("total_pages", 0),
        "avg_depth": stats.get("avg_depth", 0),
        "max_depth": stats.get("max_depth", 0),
        "pages_by_depth": stats.get("pages_by_depth", {}),
        "ia_score": audit_data.get("ia_score", {}),
    })


@app.route("/download-report")
def download_report():
    """Download audit report."""
    if not REPORT_OUTPUT_PATH.exists():
        try:
            auditor = AuditReportGenerator(str(CSV_FILE_PATH))
            auditor.generate_full_report(str(REPORT_OUTPUT_PATH))
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return jsonify({"error": "Failed to generate report"}), 500

    return send_file(
        REPORT_OUTPUT_PATH,
        mimetype="text/plain",
        as_attachment=True,
        download_name="TSM_Website_Audit_Report.txt",
    )


@app.route("/download-data")
def download_data():
    """Download crawl data as CSV."""
    if not CSV_FILE_PATH.exists():
        return jsonify({"error": "Data file not found"}), 404

    return send_file(
        CSV_FILE_PATH,
        mimetype="text/csv",
        as_attachment=True,
        download_name="tsm_crawl_data.csv",
    )


@app.route("/visualizations/mindmap")
def visualizations_mindmap():
    """Serve the full mindmap visualization."""
    from src.mindmap import create_plotly_mindmap
    
    output_file = Path(__file__).parent.parent / "visualizations" / "mindmap.html"
    
    # Generate if not exists
    if not output_file.exists():
        try:
            create_plotly_mindmap(str(CSV_FILE_PATH), str(output_file))
        except Exception as e:
            logger.error(f"Error generating mindmap: {e}")
            return jsonify({"error": "Failed to generate mindmap"}), 500
    
    return send_file(output_file, mimetype="text/html")


@app.route("/visualizations/radial")
def visualizations_radial():
    """Serve the radial mindmap visualization."""
    from src.mindmap import create_radial_mindmap
    
    output_file = Path(__file__).parent.parent / "visualizations" / "radial_mindmap.html"
    
    # Generate if not exists
    if not output_file.exists():
        try:
            create_radial_mindmap(str(CSV_FILE_PATH), str(output_file))
        except Exception as e:
            logger.error(f"Error generating radial mindmap: {e}")
            return jsonify({"error": "Failed to generate radial mindmap"}), 500
    
    return send_file(output_file, mimetype="text/html")


@app.route("/visualizations/tree")
def visualizations_tree():
    """Serve the tree hierarchy visualization."""
    from src.mindmap import create_tree_hierarchy_view
    
    output_file = Path(__file__).parent.parent / "visualizations" / "tree_hierarchy.html"
    
    # Generate if not exists
    if not output_file.exists():
        try:
            create_tree_hierarchy_view(str(CSV_FILE_PATH), str(output_file))
        except Exception as e:
            logger.error(f"Error generating tree hierarchy: {e}")
            return jsonify({"error": "Failed to generate tree hierarchy"}), 500
    
    return send_file(output_file, mimetype="text/html")


# ---------------------------------------------------------------------------
# Main Execution
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("  TSM Website Structure Dashboard (shadcn/ui Edition)")
    print("=" * 60)
    print()
    print("  🌐 Dashboard: http://localhost:5000")
    print()
    print("  Features:")
    print("    • Modern dark theme with shadcn/ui components")
    print("    • Interactive network visualization")
    print("    • Comprehensive statistics & charts")
    print("    • Detailed audit report")
    print("    • Sortable/filterable data table")
    print()
    print("=" * 60)
    print("  Press Ctrl+C to stop the server")
    print()
    
    app.run(debug=True, host="0.0.0.0", port=5000)

