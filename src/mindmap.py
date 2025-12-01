"""
Mind Map Visualization Module for Website Structure
====================================================

Generates mind map visualizations showing hierarchical information architecture
in an intuitive, interactive format.

Author: TSM Web Crawler Project
"""

from __future__ import annotations

import json
import logging
import math
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import networkx as nx
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# ---------------------------------------------------------------------------
# Logging Setup
# ---------------------------------------------------------------------------

logger = logging.getLogger("MindMapVisualization")
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
# Color Scheme
# ---------------------------------------------------------------------------

DEPTH_COLORS = {
    0: "#3B82F6",  # Blue - Homepage
    1: "#10B981",  # Green - Main sections
    2: "#F59E0B",  # Amber - Subsections
    3: "#FB923C",  # Orange - Detail pages
    4: "#EF4444",  # Red - Deep pages
}

SECTION_ICONS = {
    "academics": "📚",
    "admissions": "📝",
    "about": "👥",
    "contact": "📞",
    "events": "📅",
    "news": "📰",
    "faculty": "👨‍🏫",
    "research": "🔬",
    "programmes": "🎓",
    "placements": "💼",
    "library": "📖",
    "sports": "⚽",
    "hostel": "🏠",
    "alumni": "🎓",
    "careers": "💼",
    "login": "🔐",
    "home": "🏠",
    "homepage": "🌐",
    "default": "📄",
}


def get_section_icon(section_name: str) -> str:
    """Get appropriate icon for a section."""
    section_lower = section_name.lower()
    for key, icon in SECTION_ICONS.items():
        if key in section_lower:
            return icon
    return SECTION_ICONS["default"]


def get_depth_color(depth: int) -> str:
    """Get color for a given depth level."""
    if depth in DEPTH_COLORS:
        return DEPTH_COLORS[depth]
    return DEPTH_COLORS[4]  # Default to red for deep pages


# ---------------------------------------------------------------------------
# Data Structure Generation
# ---------------------------------------------------------------------------


def extract_section_name(url: str) -> str:
    """Extract section name from URL path."""
    try:
        parsed = urlparse(url)
        parts = [p for p in parsed.path.split("/") if p]
        if parts:
            # Clean up the section name
            name = parts[-1].replace("-", " ").replace("_", " ").title()
            return name[:30]  # Limit length
        return "Homepage"
    except Exception:
        return "Page"


def generate_mindmap_data(csv_file: str) -> Dict[str, Any]:
    """
    Transform crawled data into mind map structure.
    
    Args:
        csv_file: Path to the crawl data CSV file.
        
    Returns:
        Hierarchical dictionary structure for mind map visualization.
    """
    csv_path = Path(csv_file)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    df = pd.read_csv(csv_path)

    # Normalize columns
    for col in ("depth", "child_count", "status_code"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    for col in ("url", "parent_url", "title"):
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str)

    # Build parent-child relationships
    children_map: Dict[str, List[Dict]] = defaultdict(list)
    url_data: Dict[str, Dict] = {}

    for _, row in df.iterrows():
        url = row["url"]
        parent = row.get("parent_url", "") or ""
        
        url_data[url] = {
            "url": url,
            "name": row.get("title", "") or extract_section_name(url),
            "depth": int(row.get("depth", 0)),
            "child_count": int(row.get("child_count", 0)),
            "status_code": int(row.get("status_code", 200)),
            "icon": get_section_icon(extract_section_name(url)),
        }
        
        if parent:
            children_map[parent].append(url)

    # Find root (depth 0)
    root_url = None
    for url, data in url_data.items():
        if data["depth"] == 0:
            root_url = url
            break

    if not root_url:
        # Use first URL as root
        root_url = df.iloc[0]["url"] if len(df) > 0 else ""

    # Build tree recursively
    def build_tree(url: str, visited: set) -> Optional[Dict]:
        if url in visited or url not in url_data:
            return None
        
        visited.add(url)
        node = url_data[url].copy()
        
        children = []
        for child_url in children_map.get(url, []):
            child_node = build_tree(child_url, visited)
            if child_node:
                children.append(child_node)
        
        # Sort children by child_count descending
        children.sort(key=lambda x: x.get("child_count", 0), reverse=True)
        node["children"] = children
        
        return node

    root_node = build_tree(root_url, set())
    
    if not root_node:
        root_node = {
            "name": "TSM Website",
            "url": "/",
            "depth": 0,
            "child_count": len(df),
            "icon": "🌐",
            "children": [],
        }

    return {"root": root_node}


# ---------------------------------------------------------------------------
# Plotly Mind Map Visualization
# ---------------------------------------------------------------------------


def calculate_radial_positions(
    root: Dict[str, Any],
    center: Tuple[float, float] = (0, 0),
    start_angle: float = 0,
    end_angle: float = 360,
    radius: float = 1.0,
    level_radius_step: float = 1.5,
) -> Dict[str, Tuple[float, float]]:
    """
    Calculate radial positions for mind map nodes.
    
    Args:
        root: Root node of the tree.
        center: Center position (x, y).
        start_angle: Starting angle in degrees.
        end_angle: Ending angle in degrees.
        radius: Current radius from center.
        level_radius_step: How much to increase radius per level.
        
    Returns:
        Dictionary mapping URLs to (x, y) positions.
    """
    positions = {}
    
    def calculate_positions(
        node: Dict,
        cx: float,
        cy: float,
        start: float,
        end: float,
        r: float,
    ):
        url = node.get("url", "")
        positions[url] = (cx, cy)
        
        children = node.get("children", [])
        if not children:
            return
        
        # Calculate angle span for each child
        angle_span = end - start
        angle_per_child = angle_span / len(children)
        
        for i, child in enumerate(children):
            child_angle = start + (i + 0.5) * angle_per_child
            child_rad = math.radians(child_angle)
            
            child_x = cx + r * math.cos(child_rad)
            child_y = cy + r * math.sin(child_rad)
            
            # Recurse with smaller angle span
            child_start = start + i * angle_per_child
            child_end = child_start + angle_per_child
            
            calculate_positions(
                child,
                child_x,
                child_y,
                child_start,
                child_end,
                r * 0.6,  # Reduce radius for nested levels
            )
    
    # Start from root at center
    positions[root.get("url", "")] = center
    
    children = root.get("children", [])
    if children:
        angle_per_child = 360 / len(children)
        for i, child in enumerate(children):
            child_angle = i * angle_per_child
            child_rad = math.radians(child_angle)
            
            child_x = center[0] + radius * math.cos(child_rad)
            child_y = center[1] + radius * math.sin(child_rad)
            
            child_start = child_angle - angle_per_child / 2
            child_end = child_angle + angle_per_child / 2
            
            calculate_positions(
                child,
                child_x,
                child_y,
                child_start,
                child_end,
                radius * level_radius_step,
            )
    
    return positions


def create_plotly_mindmap(
    csv_file: str,
    output_file: str = "visualizations/mindmap.html",
) -> str:
    """
    Create interactive Plotly-based mind map visualization.
    
    Args:
        csv_file: Path to the crawl data CSV file.
        output_file: Path to save the HTML output.
        
    Returns:
        Path to the generated HTML file.
    """
    logger.info(f"Creating mind map from {csv_file}")
    
    # Load data
    df = pd.read_csv(csv_file)
    
    # Normalize columns
    for col in ("depth", "child_count", "status_code"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    for col in ("url", "parent_url", "title"):
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str)

    # Build graph
    G = nx.DiGraph()
    
    for _, row in df.iterrows():
        url = row["url"]
        parent = row.get("parent_url", "") or ""
        
        G.add_node(url, **{
            "title": row.get("title", "") or extract_section_name(url),
            "depth": int(row.get("depth", 0)),
            "child_count": int(row.get("child_count", 0)),
            "status_code": int(row.get("status_code", 200)),
        })
        
        if parent and parent in [r["url"] for _, r in df.iterrows()]:
            G.add_edge(parent, url)

    # Find root
    root_nodes = [n for n in G.nodes() if G.in_degree(n) == 0]
    root = root_nodes[0] if root_nodes else list(G.nodes())[0]

    # Calculate positions using radial layout
    try:
        # Use spring layout with root at center
        pos = nx.spring_layout(G, k=2, iterations=100, seed=42, center=(0, 0))
        
        # Adjust root to center
        if root in pos:
            root_pos = pos[root]
            for node in pos:
                pos[node] = (pos[node][0] - root_pos[0], pos[node][1] - root_pos[1])
    except Exception:
        # Fallback to simple layout
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
        line=dict(width=1, color="#475569"),
        hoverinfo="none",
        mode="lines",
        name="Connections",
    )

    # Create node traces by depth
    node_traces = []
    
    for depth in range(5):
        nodes_at_depth = [n for n in G.nodes() if G.nodes[n].get("depth", 0) == depth]
        
        if not nodes_at_depth:
            continue
        
        node_x = []
        node_y = []
        node_text = []
        node_size = []
        
        for node in nodes_at_depth:
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            
            data = G.nodes[node]
            title = data.get("title", "")[:35]
            child_count = data.get("child_count", 0)
            status = data.get("status_code", 200)
            
            hover_text = (
                f"<b>{title}</b><br>"
                f"URL: {node[:50]}...<br>"
                f"Depth: {depth}<br>"
                f"Children: {child_count}<br>"
                f"Status: {status}"
            )
            node_text.append(hover_text)
            
            # Size based on child count
            size = 20 + min(child_count * 2, 40)
            node_size.append(size)
        
        depth_name = {
            0: "Homepage",
            1: "Main Sections",
            2: "Subsections",
            3: "Detail Pages",
            4: "Deep Pages",
        }.get(depth, f"Depth {depth}")
        
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
            title=dict(
                text="TSM Website Information Architecture - Mind Map",
                font=dict(size=20, color="#E2E8F0"),
                x=0.5,
            ),
            showlegend=True,
            legend=dict(
                font=dict(color="#E2E8F0"),
                bgcolor="rgba(30, 41, 59, 0.8)",
                bordercolor="#475569",
            ),
            hovermode="closest",
            height=800,
            width=1400,
            paper_bgcolor="#0F172A",
            plot_bgcolor="#1E293B",
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
            margin=dict(l=20, r=20, t=60, b=20),
        ),
    )

    # Save to HTML
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fig.write_html(str(output_path), include_plotlyjs=True, full_html=True)
    
    logger.info(f"Mind map saved to {output_path}")
    
    return str(output_path)


# ---------------------------------------------------------------------------
# Radial Mind Map (Most Visually Striking)
# ---------------------------------------------------------------------------


def create_radial_mindmap(
    csv_file: str,
    output_file: str = "visualizations/radial_mindmap.html",
) -> str:
    """
    Create radial/circular mind map visualization.
    
    Args:
        csv_file: Path to the crawl data CSV file.
        output_file: Path to save the HTML output.
        
    Returns:
        Path to the generated HTML file.
    """
    logger.info(f"Creating radial mind map from {csv_file}")
    
    # Generate mind map data
    mindmap_data = generate_mindmap_data(csv_file)
    root = mindmap_data["root"]
    
    # Collect all nodes with positions
    nodes = []
    edges = []
    
    def collect_nodes(
        node: Dict,
        parent_id: Optional[int],
        cx: float,
        cy: float,
        angle_start: float,
        angle_end: float,
        radius: float,
        level: int,
    ):
        node_id = len(nodes)
        
        nodes.append({
            "id": node_id,
            "url": node.get("url", ""),
            "name": node.get("name", "")[:25],
            "depth": node.get("depth", level),
            "child_count": node.get("child_count", 0),
            "icon": node.get("icon", "📄"),
            "x": cx,
            "y": cy,
        })
        
        if parent_id is not None:
            edges.append((parent_id, node_id))
        
        children = node.get("children", [])
        if not children:
            return
        
        angle_span = angle_end - angle_start
        angle_per_child = angle_span / len(children)
        
        for i, child in enumerate(children):
            child_angle = angle_start + (i + 0.5) * angle_per_child
            child_rad = math.radians(child_angle)
            
            child_x = cx + radius * math.cos(child_rad)
            child_y = cy + radius * math.sin(child_rad)
            
            child_start = angle_start + i * angle_per_child
            child_end = child_start + angle_per_child
            
            collect_nodes(
                child,
                node_id,
                child_x,
                child_y,
                child_start,
                child_end,
                radius * 0.7,
                level + 1,
            )
    
    # Start collection from root
    children = root.get("children", [])
    nodes.append({
        "id": 0,
        "url": root.get("url", ""),
        "name": root.get("name", "Homepage")[:25],
        "depth": 0,
        "child_count": root.get("child_count", 0),
        "icon": "🌐",
        "x": 0,
        "y": 0,
    })
    
    if children:
        angle_per_child = 360 / len(children)
        for i, child in enumerate(children):
            child_angle = i * angle_per_child
            child_rad = math.radians(child_angle)
            
            child_x = 2 * math.cos(child_rad)
            child_y = 2 * math.sin(child_rad)
            
            child_start = child_angle - angle_per_child / 2
            child_end = child_angle + angle_per_child / 2
            
            collect_nodes(
                child,
                0,
                child_x,
                child_y,
                child_start,
                child_end,
                1.5,
                1,
            )

    # Create edge traces
    edge_x = []
    edge_y = []
    
    for parent_id, child_id in edges:
        parent = nodes[parent_id]
        child = nodes[child_id]
        edge_x.extend([parent["x"], child["x"], None])
        edge_y.extend([parent["y"], child["y"], None])

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        line=dict(width=1.5, color="#475569"),
        hoverinfo="none",
        mode="lines",
        name="Connections",
    )

    # Create node traces by depth
    node_traces = []
    max_depth = max(n["depth"] for n in nodes) if nodes else 0
    
    for depth in range(max_depth + 1):
        depth_nodes = [n for n in nodes if n["depth"] == depth]
        
        if not depth_nodes:
            continue
        
        node_x = [n["x"] for n in depth_nodes]
        node_y = [n["y"] for n in depth_nodes]
        node_text = [
            f"<b>{n['icon']} {n['name']}</b><br>"
            f"Depth: {n['depth']}<br>"
            f"Children: {n['child_count']}"
            for n in depth_nodes
        ]
        node_size = [25 + min(n["child_count"] * 3, 35) for n in depth_nodes]
        
        depth_name = {
            0: "🌐 Homepage",
            1: "📁 Main Sections",
            2: "📂 Subsections",
            3: "📄 Detail Pages",
        }.get(depth, f"📄 Depth {depth}")
        
        node_trace = go.Scatter(
            x=node_x,
            y=node_y,
            mode="markers+text",
            hoverinfo="text",
            text=[n["icon"] for n in depth_nodes],
            textposition="middle center",
            textfont=dict(size=12),
            hovertext=node_text,
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
            title=dict(
                text="🌐 TSM Website Structure - Radial Mind Map",
                font=dict(size=22, color="#E2E8F0"),
                x=0.5,
            ),
            showlegend=True,
            legend=dict(
                font=dict(color="#E2E8F0", size=12),
                bgcolor="rgba(30, 41, 59, 0.9)",
                bordercolor="#475569",
                borderwidth=1,
            ),
            hovermode="closest",
            height=800,
            width=1200,
            paper_bgcolor="#0F172A",
            plot_bgcolor="#0F172A",
            xaxis=dict(
                showgrid=False,
                zeroline=False,
                showticklabels=False,
                range=[-6, 6],
            ),
            yaxis=dict(
                showgrid=False,
                zeroline=False,
                showticklabels=False,
                range=[-6, 6],
                scaleanchor="x",
                scaleratio=1,
            ),
            margin=dict(l=20, r=20, t=80, b=20),
        ),
    )

    # Add annotations for section labels
    annotations = []
    for node in nodes[:min(15, len(nodes))]:  # Limit labels
        if node["depth"] <= 1:
            annotations.append(dict(
                x=node["x"],
                y=node["y"] - 0.3,
                text=node["name"][:15],
                showarrow=False,
                font=dict(size=9, color="#94A3B8"),
            ))
    
    fig.update_layout(annotations=annotations)

    # Save to HTML
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fig.write_html(str(output_path), include_plotlyjs=True, full_html=True)
    
    logger.info(f"Radial mind map saved to {output_path}")
    
    return str(output_path)


# ---------------------------------------------------------------------------
# Tree Hierarchy View
# ---------------------------------------------------------------------------


def create_tree_hierarchy_view(
    csv_file: str,
    output_file: str = "visualizations/tree_hierarchy.html",
) -> str:
    """
    Create traditional tree hierarchy view (like folder structure).
    
    Args:
        csv_file: Path to the crawl data CSV file.
        output_file: Path to save the HTML output.
        
    Returns:
        Path to the generated HTML file.
    """
    logger.info(f"Creating tree hierarchy from {csv_file}")
    
    # Generate mind map data
    mindmap_data = generate_mindmap_data(csv_file)
    root = mindmap_data["root"]
    
    # Generate HTML tree structure
    def generate_tree_html(node: Dict, level: int = 0) -> str:
        indent = "  " * level
        icon = node.get("icon", "📄")
        name = node.get("name", "Page")[:40]
        url = node.get("url", "")
        depth = node.get("depth", level)
        child_count = node.get("child_count", 0)
        children = node.get("children", [])
        
        color = get_depth_color(depth)
        
        html = f'''
{indent}<div class="tree-node" data-depth="{depth}" data-url="{url}">
{indent}  <div class="node-header" style="border-left: 3px solid {color};" onclick="toggleNode(this)">
{indent}    <span class="toggle-icon">{("▼" if children else "•")}</span>
{indent}    <span class="node-icon">{icon}</span>
{indent}    <span class="node-name">{name}</span>
{indent}    <span class="node-badge" style="background: {color}20; color: {color};">{child_count} pages</span>
{indent}  </div>
{indent}  <div class="node-children">'''
        
        for child in children[:20]:  # Limit children for performance
            html += generate_tree_html(child, level + 1)
        
        if len(children) > 20:
            html += f'''
{indent}    <div class="more-indicator">... and {len(children) - 20} more</div>'''
        
        html += f'''
{indent}  </div>
{indent}</div>'''
        
        return html

    tree_html = generate_tree_html(root)

    # Full HTML template
    html_template = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TSM Website - Tree Hierarchy View</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
            color: #E2E8F0;
            min-height: 100vh;
            padding: 24px;
        }}
        
        h1 {{
            text-align: center;
            margin-bottom: 24px;
            font-size: 24px;
            color: #F8FAFC;
        }}
        
        .controls {{
            display: flex;
            gap: 12px;
            justify-content: center;
            margin-bottom: 24px;
            flex-wrap: wrap;
        }}
        
        .btn {{
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
        }}
        
        .btn-primary {{
            background: #3B82F6;
            color: white;
        }}
        
        .btn-primary:hover {{
            background: #2563EB;
        }}
        
        .btn-secondary {{
            background: #334155;
            color: #E2E8F0;
        }}
        
        .btn-secondary:hover {{
            background: #475569;
        }}
        
        .tree-container {{
            max-width: 1200px;
            margin: 0 auto;
            background: #1E293B;
            border-radius: 12px;
            padding: 24px;
            border: 1px solid #334155;
        }}
        
        .tree-node {{
            margin-left: 20px;
        }}
        
        .tree-node[data-depth="0"] {{
            margin-left: 0;
        }}
        
        .node-header {{
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 10px 12px;
            margin: 4px 0;
            background: #0F172A;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s;
        }}
        
        .node-header:hover {{
            background: #1E3A5F;
        }}
        
        .toggle-icon {{
            width: 16px;
            font-size: 10px;
            color: #64748B;
            transition: transform 0.2s;
        }}
        
        .node-header.collapsed .toggle-icon {{
            transform: rotate(-90deg);
        }}
        
        .node-icon {{
            font-size: 16px;
        }}
        
        .node-name {{
            flex: 1;
            font-size: 14px;
            color: #E2E8F0;
        }}
        
        .node-badge {{
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 500;
        }}
        
        .node-children {{
            display: block;
        }}
        
        .node-header.collapsed + .node-children {{
            display: none;
        }}
        
        .more-indicator {{
            padding: 8px 12px;
            margin-left: 20px;
            color: #64748B;
            font-size: 12px;
            font-style: italic;
        }}
        
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }}
        
        .stat-card {{
            background: #1E293B;
            border: 1px solid #334155;
            border-radius: 8px;
            padding: 16px;
            text-align: center;
        }}
        
        .stat-value {{
            font-size: 28px;
            font-weight: 700;
            color: #3B82F6;
        }}
        
        .stat-label {{
            font-size: 12px;
            color: #94A3B8;
            margin-top: 4px;
        }}
    </style>
</head>
<body>
    <h1>🗂️ TSM Website - Tree Hierarchy View</h1>
    
    <div class="controls">
        <button class="btn btn-primary" onclick="expandAll()">
            ▼ Expand All
        </button>
        <button class="btn btn-secondary" onclick="collapseAll()">
            ▶ Collapse All
        </button>
        <button class="btn btn-secondary" onclick="collapseToDepth(1)">
            Depth 1 Only
        </button>
        <button class="btn btn-secondary" onclick="collapseToDepth(2)">
            Depth 2 Only
        </button>
    </div>
    
    <div class="tree-container">
        {tree_html}
    </div>
    
    <script>
        function toggleNode(header) {{
            header.classList.toggle('collapsed');
        }}
        
        function expandAll() {{
            document.querySelectorAll('.node-header').forEach(h => {{
                h.classList.remove('collapsed');
            }});
        }}
        
        function collapseAll() {{
            document.querySelectorAll('.node-header').forEach(h => {{
                h.classList.add('collapsed');
            }});
        }}
        
        function collapseToDepth(maxDepth) {{
            document.querySelectorAll('.tree-node').forEach(node => {{
                const depth = parseInt(node.dataset.depth);
                const header = node.querySelector(':scope > .node-header');
                if (header) {{
                    if (depth >= maxDepth) {{
                        header.classList.add('collapsed');
                    }} else {{
                        header.classList.remove('collapsed');
                    }}
                }}
            }});
        }}
        
        // Initialize with depth 1 expanded
        collapseToDepth(2);
    </script>
</body>
</html>'''

    # Save to file
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_template)
    
    logger.info(f"Tree hierarchy saved to {output_path}")
    
    return str(output_path)


# ---------------------------------------------------------------------------
# Interactive HTML Mind Map with JavaScript
# ---------------------------------------------------------------------------


def create_interactive_mindmap_html(
    csv_file: str,
    output_file: str = "visualizations/interactive_mindmap.html",
) -> str:
    """
    Create fully interactive HTML-based mind map with JavaScript.
    
    Args:
        csv_file: Path to the crawl data CSV file.
        output_file: Path to save the HTML output.
        
    Returns:
        Path to the generated HTML file.
    """
    logger.info(f"Creating interactive mind map from {csv_file}")
    
    # Generate mind map data
    mindmap_data = generate_mindmap_data(csv_file)
    
    # Convert to JSON for JavaScript
    mindmap_json = json.dumps(mindmap_data, indent=2)
    
    # Full HTML template with embedded JavaScript
    html_template = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TSM Website - Interactive Mind Map</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: #0F172A;
            color: #E2E8F0;
            min-height: 100vh;
        }}
        
        .header {{
            background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
            border-bottom: 1px solid #334155;
            padding: 16px 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .header h1 {{
            font-size: 20px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        
        .header h1 i {{
            color: #3B82F6;
        }}
        
        .controls {{
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
        }}
        
        .btn {{
            padding: 8px 16px;
            border: none;
            border-radius: 6px;
            font-size: 13px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        
        .btn-primary {{
            background: #3B82F6;
            color: white;
        }}
        
        .btn-primary:hover {{
            background: #2563EB;
        }}
        
        .btn-secondary {{
            background: #334155;
            color: #E2E8F0;
        }}
        
        .btn-secondary:hover {{
            background: #475569;
        }}
        
        .main-container {{
            display: flex;
            height: calc(100vh - 65px);
        }}
        
        .sidebar {{
            width: 300px;
            background: #1E293B;
            border-right: 1px solid #334155;
            overflow-y: auto;
            padding: 16px;
        }}
        
        .sidebar h3 {{
            font-size: 14px;
            font-weight: 600;
            color: #94A3B8;
            margin-bottom: 12px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        
        .view-toggle {{
            display: flex;
            gap: 4px;
            margin-bottom: 16px;
        }}
        
        .view-btn {{
            flex: 1;
            padding: 8px;
            border: 1px solid #334155;
            background: transparent;
            color: #94A3B8;
            border-radius: 6px;
            font-size: 12px;
            cursor: pointer;
            transition: all 0.2s;
        }}
        
        .view-btn.active {{
            background: #3B82F6;
            border-color: #3B82F6;
            color: white;
        }}
        
        .view-btn:hover:not(.active) {{
            background: #334155;
        }}
        
        .search-box {{
            width: 100%;
            padding: 10px 12px;
            border: 1px solid #334155;
            border-radius: 6px;
            background: #0F172A;
            color: #E2E8F0;
            font-size: 13px;
            margin-bottom: 16px;
        }}
        
        .search-box:focus {{
            outline: none;
            border-color: #3B82F6;
        }}
        
        .depth-filter {{
            margin-bottom: 16px;
        }}
        
        .depth-filter label {{
            display: block;
            font-size: 12px;
            color: #94A3B8;
            margin-bottom: 6px;
        }}
        
        .depth-slider {{
            width: 100%;
            accent-color: #3B82F6;
        }}
        
        .legend {{
            margin-top: 16px;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 6px 0;
            font-size: 12px;
            color: #94A3B8;
        }}
        
        .legend-dot {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
        }}
        
        .visualization-area {{
            flex: 1;
            position: relative;
        }}
        
        #mindmapChart {{
            width: 100%;
            height: 100%;
        }}
        
        .node-details {{
            position: absolute;
            bottom: 20px;
            right: 20px;
            width: 280px;
            background: #1E293B;
            border: 1px solid #334155;
            border-radius: 8px;
            padding: 16px;
            display: none;
        }}
        
        .node-details.visible {{
            display: block;
        }}
        
        .node-details h4 {{
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 12px;
            color: #F8FAFC;
        }}
        
        .detail-row {{
            display: flex;
            justify-content: space-between;
            padding: 6px 0;
            border-bottom: 1px solid #334155;
            font-size: 12px;
        }}
        
        .detail-row:last-child {{
            border-bottom: none;
        }}
        
        .detail-label {{
            color: #94A3B8;
        }}
        
        .detail-value {{
            color: #E2E8F0;
            font-weight: 500;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 8px;
            margin-bottom: 16px;
        }}
        
        .stat-mini {{
            background: #0F172A;
            border-radius: 6px;
            padding: 10px;
            text-align: center;
        }}
        
        .stat-mini-value {{
            font-size: 18px;
            font-weight: 700;
            color: #3B82F6;
        }}
        
        .stat-mini-label {{
            font-size: 10px;
            color: #64748B;
            margin-top: 2px;
        }}
    </style>
</head>
<body>
    <header class="header">
        <h1>
            <i class="fas fa-sitemap"></i>
            TSM Website - Interactive Mind Map
        </h1>
        <div class="controls">
            <button class="btn btn-secondary" onclick="resetView()">
                <i class="fas fa-sync-alt"></i> Reset
            </button>
            <button class="btn btn-secondary" onclick="exportImage()">
                <i class="fas fa-download"></i> Export PNG
            </button>
            <button class="btn btn-primary" onclick="window.open('tree_hierarchy.html')">
                <i class="fas fa-folder-tree"></i> Tree View
            </button>
        </div>
    </header>
    
    <div class="main-container">
        <aside class="sidebar">
            <h3>View Type</h3>
            <div class="view-toggle">
                <button class="view-btn active" data-view="radial" onclick="setView('radial')">Radial</button>
                <button class="view-btn" data-view="force" onclick="setView('force')">Force</button>
            </div>
            
            <h3>Search</h3>
            <input type="text" class="search-box" placeholder="Search pages..." id="searchInput" oninput="searchNodes(this.value)">
            
            <h3>Filter by Depth</h3>
            <div class="depth-filter">
                <label>Max Depth: <span id="depthValue">5</span></label>
                <input type="range" class="depth-slider" min="0" max="5" value="5" id="depthSlider" oninput="filterByDepth(this.value)">
            </div>
            
            <h3>Statistics</h3>
            <div class="stats-grid">
                <div class="stat-mini">
                    <div class="stat-mini-value" id="totalNodes">0</div>
                    <div class="stat-mini-label">Total Pages</div>
                </div>
                <div class="stat-mini">
                    <div class="stat-mini-value" id="maxDepth">0</div>
                    <div class="stat-mini-label">Max Depth</div>
                </div>
                <div class="stat-mini">
                    <div class="stat-mini-value" id="totalSections">0</div>
                    <div class="stat-mini-label">Sections</div>
                </div>
                <div class="stat-mini">
                    <div class="stat-mini-value" id="avgChildren">0</div>
                    <div class="stat-mini-label">Avg Children</div>
                </div>
            </div>
            
            <h3>Legend</h3>
            <div class="legend">
                <div class="legend-item">
                    <div class="legend-dot" style="background: #3B82F6;"></div>
                    <span>Homepage (Depth 0)</span>
                </div>
                <div class="legend-item">
                    <div class="legend-dot" style="background: #10B981;"></div>
                    <span>Main Sections (Depth 1)</span>
                </div>
                <div class="legend-item">
                    <div class="legend-dot" style="background: #F59E0B;"></div>
                    <span>Subsections (Depth 2)</span>
                </div>
                <div class="legend-item">
                    <div class="legend-dot" style="background: #FB923C;"></div>
                    <span>Detail Pages (Depth 3)</span>
                </div>
                <div class="legend-item">
                    <div class="legend-dot" style="background: #EF4444;"></div>
                    <span>Deep Pages (Depth 4+)</span>
                </div>
            </div>
        </aside>
        
        <main class="visualization-area">
            <div id="mindmapChart"></div>
            
            <div class="node-details" id="nodeDetails">
                <h4 id="nodeTitle">Node Details</h4>
                <div class="detail-row">
                    <span class="detail-label">URL</span>
                    <span class="detail-value" id="nodeUrl">-</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Depth</span>
                    <span class="detail-value" id="nodeDepth">-</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Children</span>
                    <span class="detail-value" id="nodeChildren">-</span>
                </div>
            </div>
        </main>
    </div>
    
    <script>
        // Mind map data
        const mindmapData = {mindmap_json};
        
        // Depth colors
        const depthColors = {{
            0: '#3B82F6',
            1: '#10B981',
            2: '#F59E0B',
            3: '#FB923C',
            4: '#EF4444'
        }};
        
        // Current view type
        let currentView = 'radial';
        let currentMaxDepth = 5;
        
        // Collect all nodes
        let allNodes = [];
        let allEdges = [];
        
        function collectNodes(node, parentId = null, depth = 0) {{
            const nodeId = allNodes.length;
            
            allNodes.push({{
                id: nodeId,
                name: node.name || 'Page',
                url: node.url || '',
                depth: node.depth !== undefined ? node.depth : depth,
                childCount: node.child_count || 0,
                icon: node.icon || '📄'
            }});
            
            if (parentId !== null) {{
                allEdges.push([parentId, nodeId]);
            }}
            
            if (node.children) {{
                node.children.forEach(child => {{
                    collectNodes(child, nodeId, depth + 1);
                }});
            }}
        }}
        
        // Initialize data
        collectNodes(mindmapData.root);
        
        // Update statistics
        document.getElementById('totalNodes').textContent = allNodes.length;
        document.getElementById('maxDepth').textContent = Math.max(...allNodes.map(n => n.depth));
        document.getElementById('totalSections').textContent = allNodes.filter(n => n.depth === 1).length;
        document.getElementById('avgChildren').textContent = (allNodes.reduce((a, b) => a + b.childCount, 0) / allNodes.length).toFixed(1);
        
        // Calculate positions
        function calculateRadialPositions() {{
            const positions = {{}};
            const anglePerNode = {{}};
            
            // Group by depth
            const nodesByDepth = {{}};
            allNodes.forEach(node => {{
                if (!nodesByDepth[node.depth]) nodesByDepth[node.depth] = [];
                nodesByDepth[node.depth].push(node);
            }});
            
            // Position nodes
            Object.keys(nodesByDepth).forEach(depth => {{
                const nodes = nodesByDepth[depth];
                const radius = parseInt(depth) * 2 + 0.5;
                const angleStep = (2 * Math.PI) / nodes.length;
                
                nodes.forEach((node, i) => {{
                    const angle = i * angleStep;
                    positions[node.id] = {{
                        x: radius * Math.cos(angle),
                        y: radius * Math.sin(angle)
                    }};
                }});
            }});
            
            // Root at center
            if (allNodes.length > 0) {{
                positions[0] = {{ x: 0, y: 0 }};
            }}
            
            return positions;
        }}
        
        function renderMindmap(maxDepth = 5) {{
            const positions = calculateRadialPositions();
            
            // Filter nodes by depth
            const visibleNodes = allNodes.filter(n => n.depth <= maxDepth);
            const visibleIds = new Set(visibleNodes.map(n => n.id));
            const visibleEdges = allEdges.filter(e => visibleIds.has(e[0]) && visibleIds.has(e[1]));
            
            // Create edge trace
            const edgeX = [];
            const edgeY = [];
            
            visibleEdges.forEach(([from, to]) => {{
                if (positions[from] && positions[to]) {{
                    edgeX.push(positions[from].x, positions[to].x, null);
                    edgeY.push(positions[from].y, positions[to].y, null);
                }}
            }});
            
            const edgeTrace = {{
                x: edgeX,
                y: edgeY,
                mode: 'lines',
                line: {{ width: 1, color: '#475569' }},
                hoverinfo: 'none',
                name: 'Connections'
            }};
            
            // Create node traces by depth
            const nodeTraces = [];
            
            for (let d = 0; d <= maxDepth; d++) {{
                const depthNodes = visibleNodes.filter(n => n.depth === d);
                if (depthNodes.length === 0) continue;
                
                const nodeX = depthNodes.map(n => positions[n.id]?.x || 0);
                const nodeY = depthNodes.map(n => positions[n.id]?.y || 0);
                const nodeText = depthNodes.map(n => 
                    `<b>${{n.icon}} ${{n.name}}</b><br>` +
                    `Depth: ${{n.depth}}<br>` +
                    `Children: ${{n.childCount}}`
                );
                const nodeSize = depthNodes.map(n => 20 + Math.min(n.childCount * 2, 30));
                
                const depthName = ['🌐 Homepage', '📁 Sections', '📂 Subsections', '📄 Details', '📄 Deep'][d] || `Depth ${{d}}`;
                
                nodeTraces.push({{
                    x: nodeX,
                    y: nodeY,
                    mode: 'markers+text',
                    text: depthNodes.map(n => n.icon),
                    textposition: 'middle center',
                    textfont: {{ size: 10 }},
                    hovertext: nodeText,
                    hoverinfo: 'text',
                    name: depthName,
                    marker: {{
                        color: depthColors[d] || '#EF4444',
                        size: nodeSize,
                        line: {{ width: 2, color: '#0F172A' }},
                        opacity: 0.9
                    }}
                }});
            }}
            
            // Layout
            const layout = {{
                showlegend: true,
                legend: {{
                    font: {{ color: '#E2E8F0' }},
                    bgcolor: 'rgba(30, 41, 59, 0.9)',
                    bordercolor: '#475569'
                }},
                hovermode: 'closest',
                paper_bgcolor: '#0F172A',
                plot_bgcolor: '#0F172A',
                xaxis: {{
                    showgrid: false,
                    zeroline: false,
                    showticklabels: false,
                    range: [-8, 8]
                }},
                yaxis: {{
                    showgrid: false,
                    zeroline: false,
                    showticklabels: false,
                    range: [-8, 8],
                    scaleanchor: 'x',
                    scaleratio: 1
                }},
                margin: {{ l: 20, r: 20, t: 20, b: 20 }}
            }};
            
            Plotly.newPlot('mindmapChart', [edgeTrace, ...nodeTraces], layout, {{
                responsive: true,
                displayModeBar: false
            }});
            
            // Click handler
            document.getElementById('mindmapChart').on('plotly_click', function(data) {{
                if (data.points && data.points[0]) {{
                    const pointIndex = data.points[0].pointIndex;
                    const traceIndex = data.points[0].curveNumber - 1; // -1 for edge trace
                    
                    if (traceIndex >= 0) {{
                        const depth = traceIndex;
                        const depthNodes = visibleNodes.filter(n => n.depth === depth);
                        const node = depthNodes[pointIndex];
                        
                        if (node) {{
                            showNodeDetails(node);
                        }}
                    }}
                }}
            }});
        }}
        
        function showNodeDetails(node) {{
            document.getElementById('nodeTitle').textContent = node.icon + ' ' + node.name;
            document.getElementById('nodeUrl').textContent = node.url.substring(0, 30) + '...';
            document.getElementById('nodeDepth').textContent = node.depth;
            document.getElementById('nodeChildren').textContent = node.childCount;
            document.getElementById('nodeDetails').classList.add('visible');
        }}
        
        function setView(view) {{
            currentView = view;
            document.querySelectorAll('.view-btn').forEach(btn => {{
                btn.classList.toggle('active', btn.dataset.view === view);
            }});
            renderMindmap(currentMaxDepth);
        }}
        
        function filterByDepth(depth) {{
            currentMaxDepth = parseInt(depth);
            document.getElementById('depthValue').textContent = depth;
            renderMindmap(currentMaxDepth);
        }}
        
        function searchNodes(query) {{
            if (!query) {{
                renderMindmap(currentMaxDepth);
                return;
            }}
            
            const lowerQuery = query.toLowerCase();
            const matchingNodes = allNodes.filter(n => 
                n.name.toLowerCase().includes(lowerQuery) || 
                n.url.toLowerCase().includes(lowerQuery)
            );
            
            // Highlight matching nodes (simplified - re-render with filter)
            console.log('Found', matchingNodes.length, 'matching nodes');
        }}
        
        function resetView() {{
            currentMaxDepth = 5;
            document.getElementById('depthSlider').value = 5;
            document.getElementById('depthValue').textContent = '5';
            document.getElementById('searchInput').value = '';
            document.getElementById('nodeDetails').classList.remove('visible');
            renderMindmap(currentMaxDepth);
        }}
        
        function exportImage() {{
            Plotly.downloadImage('mindmapChart', {{
                format: 'png',
                width: 1600,
                height: 1200,
                filename: 'tsm_mindmap'
            }});
        }}
        
        // Initial render
        renderMindmap();
    </script>
</body>
</html>'''

    # Save to file
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_template)
    
    logger.info(f"Interactive mind map saved to {output_path}")
    
    return str(output_path)


# ---------------------------------------------------------------------------
# Generate All Mind Map Visualizations
# ---------------------------------------------------------------------------


def generate_all_mindmaps(csv_file: str, output_dir: str = "visualizations") -> Dict[str, str]:
    """
    Generate all mind map visualization types.
    
    Args:
        csv_file: Path to the crawl data CSV file.
        output_dir: Directory to save visualizations.
        
    Returns:
        Dictionary mapping visualization type to output file path.
    """
    logger.info(f"Generating all mind map visualizations from {csv_file}")
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    results = {}
    
    # Generate each type
    try:
        results["plotly_mindmap"] = create_plotly_mindmap(
            csv_file, str(output_path / "mindmap.html")
        )
    except Exception as e:
        logger.error(f"Error creating Plotly mind map: {e}")
    
    try:
        results["radial_mindmap"] = create_radial_mindmap(
            csv_file, str(output_path / "radial_mindmap.html")
        )
    except Exception as e:
        logger.error(f"Error creating radial mind map: {e}")
    
    try:
        results["tree_hierarchy"] = create_tree_hierarchy_view(
            csv_file, str(output_path / "tree_hierarchy.html")
        )
    except Exception as e:
        logger.error(f"Error creating tree hierarchy: {e}")
    
    try:
        results["interactive_mindmap"] = create_interactive_mindmap_html(
            csv_file, str(output_path / "interactive_mindmap.html")
        )
    except Exception as e:
        logger.error(f"Error creating interactive mind map: {e}")
    
    logger.info(f"Generated {len(results)} mind map visualizations")
    
    return results


# ---------------------------------------------------------------------------
# Main Execution
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    
    csv_file = sys.argv[1] if len(sys.argv) > 1 else "output/tsm_crawl_data.csv"
    
    print("=" * 60)
    print("  Mind Map Visualization Generator")
    print("=" * 60)
    print()
    
    results = generate_all_mindmaps(csv_file)
    
    print("\nGenerated visualizations:")
    for name, path in results.items():
        print(f"  • {name}: {path}")
    
    print()
    print("Open the HTML files in a browser to view the mind maps.")

