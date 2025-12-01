"""
Comprehensive Visualization Module for Web Crawler Data
Creates network graphs, charts, and statistics reports from crawled data.
"""

import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from collections import Counter
import numpy as np


# Setup logger
logger = logging.getLogger("TSMVisualizer")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def create_network_graph(csv_file: str) -> nx.DiGraph:
    """
    Create a directed graph from crawled CSV data.
    
    Reads CSV file, creates NetworkX DiGraph, adds nodes with attributes
    (title, depth, url), and adds edges from parent_url to url.
    
    Args:
        csv_file: Path to CSV file containing crawl data
        
    Returns:
        NetworkX DiGraph object with nodes and edges
    """
    try:
        logger.info(f"Reading crawl data from {csv_file}")
        
        # Read CSV using pandas
        df = pd.read_csv(csv_file)
        
        if df.empty:
            logger.warning("CSV file is empty")
            return nx.DiGraph()
        
        logger.info(f"Loaded {len(df)} pages from CSV")
        
        # Create NetworkX DiGraph
        graph = nx.DiGraph()
        
        # Add nodes with attributes
        for _, row in df.iterrows():
            url = row["url"]
            title = row.get("title", "") or "No Title"
            depth = int(row.get("depth", 0))
            child_count = int(row.get("child_count", 0))
            
            # Add node with attributes
            graph.add_node(
                url,
                title=title,
                depth=depth,
                url=url,
                child_count=child_count
            )
        
        # Add edges from parent_url to url
        edges_added = 0
        for _, row in df.iterrows():
            url = row["url"]
            parent_url = row.get("parent_url")
            
            # Only add edge if parent exists and is not None/NaN
            if pd.notna(parent_url) and parent_url in graph:
                graph.add_edge(parent_url, url)
                edges_added += 1
        
        logger.info(f"Created graph with {graph.number_of_nodes()} nodes and {graph.number_of_edges()} edges")
        
        return graph
    
    except FileNotFoundError:
        logger.error(f"CSV file not found: {csv_file}")
        raise
    except Exception as e:
        logger.error(f"Error creating network graph: {e}")
        raise


def visualize_hierarchy(
    graph: nx.DiGraph,
    output_path: str = "visualizations/tsm_hierarchy.png",
    figure_size: tuple = (20, 12),
    dpi: int = 300,
    base_node_size: int = 300,
    colormap: str = "Blues"
) -> None:
    """
    Visualize site hierarchy with tree-like layout.
    
    Creates a network visualization showing the website structure with nodes
    colored by depth and sized by number of children.
    
    Args:
        graph: NetworkX DiGraph object
        output_path: Path to save the visualization
        figure_size: Figure size tuple (width, height) in inches
        dpi: Resolution in dots per inch
        base_node_size: Base size for nodes
        colormap: Matplotlib colormap name
    """
    try:
        if graph.number_of_nodes() == 0:
            logger.warning("Graph is empty, cannot create visualization")
            return
        
        logger.info(f"Creating hierarchy visualization with {graph.number_of_nodes()} nodes")
        
        # Get graph layout using spring_layout
        # k=0.5 (repulsion strength), iterations=50, seed=42 (for reproducibility)
        pos = nx.spring_layout(graph, k=0.5, iterations=50, seed=42)
        
        # Create figure with size (20, 12)
        fig, ax = plt.subplots(figsize=figure_size)
        
        # Get node colors by depth
        # Use cmap=plt.cm.Blues, normalize depth values to 0-1 range
        depths = [graph.nodes[node].get("depth", 0) for node in graph.nodes()]
        
        if depths:
            min_depth = min(depths)
            max_depth = max(depths)
            
            # Normalize depths to 0-1 range
            if max_depth > min_depth:
                normalized_depths = [(d - min_depth) / (max_depth - min_depth) for d in depths]
            else:
                normalized_depths = [0.5] * len(depths)
        else:
            normalized_depths = [0.5] * len(graph.nodes())
        
        # Get colormap
        try:
            cmap = plt.cm.get_cmap(colormap)
        except (AttributeError, ValueError):
            # Fallback to Blues if specified colormap not found
            cmap = plt.cm.get_cmap("Blues")
        node_colors = [cmap(d) for d in normalized_depths]
        
        # Get node sizes (scale by number of children)
        # Base size: 300, multiply by (1 + child_count/10)
        node_sizes = []
        for node in graph.nodes():
            child_count = graph.nodes[node].get("child_count", 0)
            size = base_node_size * (1 + child_count / 10)
            node_sizes.append(size)
        
        # Draw network
        nx.draw_networkx(
            graph,
            pos,
            ax=ax,
            node_color=node_colors,
            node_size=node_sizes,
            edge_color="gray",
            alpha=0.5,
            with_labels=False,
            arrows=True,
            arrowsize=20,
            arrowstyle="->",
            linewidths=0.5
        )
        
        # Add colorbar showing depth levels
        sm = plt.cm.ScalarMappable(
            cmap=cmap,
            norm=plt.Normalize(vmin=min_depth if depths else 0, vmax=max_depth if depths else 1)
        )
        sm.set_array([])
        cbar = plt.colorbar(sm, ax=ax, label="Crawl Depth")
        
        # Set title
        ax.set_title(
            "TSM Madurai Website Structure - Crawl Hierarchy",
            fontsize=16,
            fontweight="bold",
            pad=20
        )
        
        # Add legend explaining colors and sizes
        from matplotlib.patches import Circle, Rectangle
        
        legend_elements = [
            plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=cmap(0.2), 
                      markersize=10, label="Shallow pages (low depth)"),
            plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=cmap(0.8), 
                      markersize=10, label="Deep pages (high depth)"),
            Circle((0, 0), 0.1, color="gray", alpha=0.3, label="Node size ∝ number of children")
        ]
        
        ax.legend(handles=legend_elements, loc="upper left", fontsize=9)
        
        # Remove axes
        ax.axis("off")
        
        # Save figure
        output_file = Path(output_path)
        output_file.parent.mkdir(exist_ok=True)
        plt.savefig(output_file, dpi=dpi, bbox_inches="tight")
        plt.close()
        
        logger.info(f"Hierarchy visualization saved to {output_path}")
    
    except Exception as e:
        logger.error(f"Error creating hierarchy visualization: {e}")
        raise


def visualize_depth_distribution(
    csv_file: str,
    output_path: str = "visualizations/depth_distribution.png"
) -> None:
    """
    Create bar chart showing pages per depth level.
    
    Reads CSV, counts pages by depth, and creates a bar chart visualization.
    
    Args:
        csv_file: Path to CSV file containing crawl data
        output_path: Path to save the visualization
    """
    try:
        logger.info(f"Creating depth distribution chart from {csv_file}")
        
        # Read CSV
        df = pd.read_csv(csv_file)
        
        if df.empty:
            logger.warning("CSV file is empty, cannot create depth distribution")
            return
        
        # Count pages by depth
        depth_counts = df["depth"].value_counts().sort_index()
        
        # Create figure with size (12, 6)
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Create bar chart
        # X-axis: Depth level, Y-axis: Number of pages
        bars = ax.bar(
            depth_counts.index,
            depth_counts.values,
            color=plt.cm.Blues(np.linspace(0.4, 0.8, len(depth_counts))),
            edgecolor="black",
            linewidth=1.2
        )
        
        # Add value labels on top of bars
        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.,
                height,
                f"{int(height)}",
                ha="center",
                va="bottom",
                fontsize=10,
                fontweight="bold"
            )
        
        # Set title
        ax.set_title(
            "Website Pages Distribution by Depth",
            fontsize=14,
            fontweight="bold",
            pad=15
        )
        
        # Set labels
        ax.set_xlabel("Crawl Depth", fontsize=12, fontweight="bold")
        ax.set_ylabel("Number of Pages", fontsize=12, fontweight="bold")
        
        # Set x-axis to show integer values
        ax.set_xticks(depth_counts.index)
        
        # Add grid for better readability
        ax.grid(axis="y", alpha=0.3, linestyle="--")
        
        # Save to output_path with dpi=300
        output_file = Path(output_path)
        output_file.parent.mkdir(exist_ok=True)
        plt.savefig(output_file, dpi=300, bbox_inches="tight")
        plt.close()
        
        logger.info(f"Depth distribution chart saved to {output_path}")
    
    except FileNotFoundError:
        logger.error(f"CSV file not found: {csv_file}")
        raise
    except Exception as e:
        logger.error(f"Error creating depth distribution: {e}")
        raise


def create_statistics_report(
    csv_file: str,
    json_file: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate comprehensive text report of crawl statistics.
    
    Calculates various statistics from crawled data including total pages,
    depth information, link statistics, and page relationships.
    
    Args:
        csv_file: Path to CSV file containing crawl data
        json_file: Optional path to JSON file (for additional analysis)
        
    Returns:
        Dictionary containing:
        - total_pages_crawled
        - max_depth_reached
        - average_links_per_page
        - most_linked_pages (top 5)
        - orphan_pages (pages with no children)
        - homepage_link_count
    """
    try:
        logger.info(f"Generating statistics report from {csv_file}")
        
        # Read CSV
        df = pd.read_csv(csv_file)
        
        if df.empty:
            logger.warning("CSV file is empty")
            return {
                "total_pages_crawled": 0,
                "max_depth_reached": 0,
                "average_links_per_page": 0.0,
                "most_linked_pages": [],
                "orphan_pages": 0,
                "homepage_link_count": 0
            }
        
        # Total pages crawled
        total_pages = len(df)
        
        # Max depth reached
        max_depth = int(df["depth"].max()) if "depth" in df.columns else 0
        
        # Average links per page (child_count)
        if "child_count" in df.columns:
            avg_links = float(df["child_count"].mean())
        else:
            avg_links = 0.0
        
        # Most linked pages (top 5 by child_count)
        if "child_count" in df.columns and "url" in df.columns:
            most_linked = df.nlargest(5, "child_count")[["url", "title", "child_count"]].to_dict("records")
        else:
            most_linked = []
        
        # Orphan pages (pages with no children)
        if "child_count" in df.columns:
            orphan_count = int((df["child_count"] == 0).sum())
        else:
            orphan_count = 0
        
        # Homepage link count (assuming first row or depth 0 is homepage)
        homepage_link_count = 0
        if "child_count" in df.columns:
            homepage_rows = df[df["depth"] == 0]
            if not homepage_rows.empty:
                homepage_link_count = int(homepage_rows.iloc[0]["child_count"])
        
        # Build statistics dictionary
        statistics = {
            "total_pages_crawled": total_pages,
            "max_depth_reached": max_depth,
            "average_links_per_page": round(avg_links, 2),
            "most_linked_pages": most_linked,
            "orphan_pages": orphan_count,
            "homepage_link_count": homepage_link_count
        }
        
        logger.info("Statistics report generated successfully")
        return statistics
    
    except FileNotFoundError:
        logger.error(f"CSV file not found: {csv_file}")
        raise
    except Exception as e:
        logger.error(f"Error generating statistics report: {e}")
        raise


def main() -> None:
    """
    Execute all visualizations and generate reports.
    
    Orchestrates the complete visualization pipeline:
    1. Checks if CSV file exists
    2. Creates network graph
    3. Generates hierarchy visualization
    4. Creates depth distribution chart
    5. Generates statistics report
    6. Prints all statistics
    """
    try:
        # Default paths from config
        csv_file = "output/tsm_crawl_data.csv"
        json_file = "output/tsm_crawl_data.json"
        hierarchy_output = "visualizations/tsm_hierarchy.png"
        depth_output = "visualizations/depth_distribution.png"
        
        # Check if output/tsm_crawl_data.csv exists
        csv_path = Path(csv_file)
        if not csv_path.exists():
            logger.error(f"CSV file not found: {csv_file}")
            logger.error("Please run the crawler first to generate crawl data.")
            return
        
        logger.info("Starting visualization pipeline...")
        
        # Load CSV
        logger.info(f"Loading data from {csv_file}")
        df = pd.read_csv(csv_file)
        logger.info(f"Loaded {len(df)} pages")
        
        # Create graph
        logger.info("Creating network graph...")
        graph = create_network_graph(csv_file)
        
        if graph.number_of_nodes() == 0:
            logger.warning("Graph is empty, skipping visualizations")
            return
        
        # Call visualize_hierarchy()
        logger.info("Generating hierarchy visualization...")
        visualize_hierarchy(graph, hierarchy_output)
        
        # Call visualize_depth_distribution()
        logger.info("Generating depth distribution chart...")
        visualize_depth_distribution(csv_file, depth_output)
        
        # Call create_statistics_report()
        logger.info("Generating statistics report...")
        stats = create_statistics_report(csv_file, json_file)
        
        # Print all statistics
        print("\n" + "="*60)
        print("CRAWL STATISTICS REPORT")
        print("="*60)
        print(f"Total Pages Crawled: {stats['total_pages_crawled']}")
        print(f"Max Depth Reached: {stats['max_depth_reached']}")
        print(f"Average Links per Page: {stats['average_links_per_page']}")
        print(f"Orphan Pages (no children): {stats['orphan_pages']}")
        print(f"Homepage Link Count: {stats['homepage_link_count']}")
        
        if stats['most_linked_pages']:
            print("\nTop 5 Most Linked Pages:")
            for i, page in enumerate(stats['most_linked_pages'], 1):
                title = page.get('title', 'No Title')
                url = page.get('url', 'N/A')
                count = page.get('child_count', 0)
                print(f"  {i}. {title} ({count} links)")
                print(f"     URL: {url}")
        
        print("="*60)
        print("\nVisualization Files Generated:")
        print(f"  - Hierarchy: {hierarchy_output}")
        print(f"  - Depth Distribution: {depth_output}")
        print("="*60)
        
        logger.info("All visualizations completed successfully")
    
    except Exception as e:
        logger.error(f"Error in visualization pipeline: {e}")
        raise


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Visualization interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise
