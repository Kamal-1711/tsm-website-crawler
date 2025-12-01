"""
Interactive Web Dashboard for TSM Website Crawler
Flask application with Plotly visualizations
"""

from flask import Flask, render_template, jsonify
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import json
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse
from collections import defaultdict
import numpy as np

# Global data cache (will be initialized per app instance)
crawl_data = None
data_loaded_time = None


def load_crawl_data():
    """Load and cache crawl data from CSV."""
    global crawl_data, data_loaded_time
    import os
    # Get project root directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_path = Path(project_root) / "output" / "tsm_crawl_data.csv"
    
    if not csv_path.exists():
        return None
    
    try:
        crawl_data = pd.read_csv(csv_path)
        data_loaded_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Convert numpy types to native Python types
        for col in crawl_data.columns:
            if crawl_data[col].dtype == 'float64':
                crawl_data[col] = crawl_data[col].fillna(0).astype('Int64')
        
        return crawl_data
    except Exception as e:
        print(f"Error loading data: {e}")
        return None


def calculate_metrics(df):
    """Calculate dashboard metrics."""
    if df is None or df.empty:
        return {}
    
    return {
        "total_pages": len(df),
        "max_depth": int(df['depth'].max()) if 'depth' in df.columns else 0,
        "average_links": round(df['child_count'].mean(), 2) if 'child_count' in df.columns else 0,
        "success_rate": round((df['status_code'] == 200).sum() / len(df) * 100, 1) if 'status_code' in df.columns else 0,
        "unique_domains": len(df['url'].apply(lambda x: urlparse(x).netloc).unique()) if 'url' in df.columns else 0,
        "orphan_pages": int((df['child_count'] == 0).sum()) if 'child_count' in df.columns else 0
    }


def create_network_graph(df):
    """Create interactive network graph using Plotly."""
    if df is None or df.empty:
        return None
    
    # Create node positions using a simple layout
    nodes = []
    edges = []
    
    # Group nodes by depth for better layout
    depth_groups = defaultdict(list)
    for idx, row in df.iterrows():
        # Handle depth
        depth_val = row['depth'] if 'depth' in row else 0
        depth = int(depth_val) if pd.notna(depth_val) else 0
        
        # Handle title - convert to string and handle NaN
        try:
            title_val = row['title'] if 'title' in row.index else None
            if title_val is None or (isinstance(title_val, float) and pd.isna(title_val)):
                title = 'No Title'
            else:
                title = str(title_val)[:50]
        except (KeyError, TypeError, AttributeError):
            title = 'No Title'
        
        # Handle URL
        url_val = row['url'] if 'url' in row else ''
        url = str(url_val) if pd.notna(url_val) else ''
        
        # Handle child_count
        child_count_val = row['child_count'] if 'child_count' in row else 0
        child_count = int(child_count_val) if pd.notna(child_count_val) else 0
        
        # Handle status_code
        status_code_val = row['status_code'] if 'status_code' in row else 0
        status_code = int(status_code_val) if pd.notna(status_code_val) else 0
        
        depth_groups[depth].append({
            'id': idx,
            'url': url,
            'title': title,
            'depth': depth,
            'child_count': child_count,
            'status_code': status_code
        })
    
    # Calculate positions
    node_positions = {}
    y_spacing = 2.0
    x_spacing = 1.5
    
    for depth, nodes_in_depth in sorted(depth_groups.items()):
        y = -depth * y_spacing
        for i, node in enumerate(nodes_in_depth):
            x = (i - len(nodes_in_depth) / 2) * x_spacing
            node_positions[node['id']] = (x, y)
    
    # Create edge traces
    edge_x = []
    edge_y = []
    edge_info = []
    
    for idx, row in df.iterrows():
        parent_url = row.get('parent_url')
        if pd.notna(parent_url) and str(parent_url) in df['url'].astype(str).values:
            parent_matches = df[df['url'].astype(str) == str(parent_url)]
            if not parent_matches.empty:
                parent_idx = parent_matches.index[0]
                if parent_idx in node_positions and idx in node_positions:
                    x0, y0 = node_positions[parent_idx]
                    x1, y1 = node_positions[idx]
                    edge_x.extend([x0, x1, None])
                    edge_y.extend([y0, y1, None])
                    edge_info.append(f"{parent_url} → {row['url']}")
    
    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.5, color='#888'),
        hoverinfo='none',
        mode='lines',
        name='Links'
    )
    
    # Create node traces grouped by depth
    node_traces = []
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    
    for depth, nodes_in_depth in sorted(depth_groups.items()):
        node_x = [node_positions[n['id']][0] for n in nodes_in_depth]
        node_y = [node_positions[n['id']][1] for n in nodes_in_depth]
        node_text = [f"{n['title']}<br>{n['url']}" for n in nodes_in_depth]
        node_size = [max(10, min(30, 10 + n['child_count'] / 5)) for n in nodes_in_depth]
        
        # Ensure title is string for text display
        node_titles = [str(n['title'])[:20] if n['title'] else 'No Title' for n in nodes_in_depth]
        
        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            name=f'Depth {depth}',
            text=node_titles,
            textposition="middle center",
            textfont=dict(size=8),
            hovertext=node_text,
            hoverinfo='text',
            marker=dict(
                size=node_size,
                color=colors[depth % len(colors)],
                line=dict(width=2, color='white')
            )
        )
        node_traces.append(node_trace)
    
    fig = go.Figure(data=[edge_trace] + node_traces,
                    layout=go.Layout(
                        title=dict(text='Website Structure Network Graph', font=dict(size=16)),
                        showlegend=True,
                        hovermode='closest',
                        margin=dict(b=20, l=5, r=5, t=40),
                        annotations=[dict(
                            text="Interactive Network Graph - Hover for details, click to explore",
                            showarrow=False,
                            xref="paper", yref="paper",
                            x=0.005, y=-0.002,
                            xanchor="left", yanchor="bottom",
                            font=dict(color="#888", size=12)
                        )],
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        plot_bgcolor='white',
                        paper_bgcolor='white',
                        height=600
                    ))
    
    return fig.to_json()


def create_depth_bar_chart(df):
    """Create bar chart showing pages per depth."""
    if df is None or df.empty:
        return None
    
    # Handle NaN values in depth column
    df_clean = df.copy()
    df_clean['depth'] = df_clean['depth'].fillna(0).astype(int)
    depth_counts = df_clean['depth'].value_counts().sort_index()
    
    fig = go.Figure(data=[
        go.Bar(
            x=[f"Depth {d}" for d in depth_counts.index],
            y=depth_counts.values,
            marker_color='#3498db',
            text=depth_counts.values,
            textposition='outside',
            name='Pages'
        )
    ])
    
    fig.update_layout(
        title='Pages Distribution by Depth Level',
        xaxis_title='Depth Level',
        yaxis_title='Number of Pages',
        height=400,
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    return fig.to_json()


def create_section_pie_chart(df):
    """Create pie chart showing distribution by section."""
    if df is None or df.empty:
        return None
    
    def extract_section(url):
        try:
            parsed = urlparse(url)
            path_parts = [p for p in parsed.path.split('/') if p]
            return path_parts[0] if path_parts else 'home'
        except:
            return 'other'
    
    df['section'] = df['url'].apply(extract_section)
    section_counts = df['section'].value_counts().head(10)
    
    fig = go.Figure(data=[
        go.Pie(
            labels=section_counts.index,
            values=section_counts.values,
            hole=0.4,
            textinfo='label+percent',
            marker=dict(colors=px.colors.qualitative.Set3)
        )
    ])
    
    fig.update_layout(
        title='Content Distribution by Section (Top 10)',
        height=400,
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    return fig.to_json()


def create_treemap(df):
    """Create treemap showing content hierarchy."""
    if df is None or df.empty:
        return None
    
    def extract_section(url):
        try:
            parsed = urlparse(url)
            path_parts = [p for p in parsed.path.split('/') if p]
            return path_parts[0] if path_parts else 'home'
        except:
            return 'other'
    
    df['section'] = df['url'].apply(extract_section)
    section_data = df.groupby('section').agg({
        'url': 'count',
        'child_count': 'sum'
    }).reset_index()
    section_data.columns = ['section', 'page_count', 'total_links']
    
    fig = go.Figure(go.Treemap(
        labels=section_data['section'],
        values=section_data['page_count'],
        parents=[''] * len(section_data),
        textinfo="label+value",
        marker=dict(
            colors=section_data['total_links'],
            colorscale='Blues',
            showscale=True
        ),
        hovertemplate='<b>%{label}</b><br>Pages: %{value}<br>Total Links: %{color}<extra></extra>'
    ))
    
    fig.update_layout(
        title='Content Hierarchy Treemap',
        height=400,
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    return fig.to_json()


def create_flask_app():
    """Create and configure Flask application."""
    import os
    # Get the project root directory (parent of src/)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_dir = os.path.join(project_root, 'templates')
    
    app = Flask(__name__, template_folder=template_dir)
    
    # Load data on app creation
    load_crawl_data()
    
    @app.route('/')
    def index():
        """Main dashboard route."""
        global crawl_data, data_loaded_time
        
        if crawl_data is None:
            crawl_data = load_crawl_data()
        
        if crawl_data is None:
            return render_template('error.html', message="No crawl data found. Please run the crawler first.")
        
        metrics = calculate_metrics(crawl_data)
        metrics['crawl_date'] = data_loaded_time
        
        # Prepare data for table
        table_data = crawl_data[['url', 'title', 'depth', 'child_count', 'status_code']].to_dict('records')
        
        # Convert to JSON-serializable format
        for record in table_data:
            record['depth'] = int(record['depth']) if pd.notna(record['depth']) else 0
            record['child_count'] = int(record['child_count']) if pd.notna(record['child_count']) else 0
            record['status_code'] = int(record['status_code']) if pd.notna(record['status_code']) else 0
            record['title'] = str(record.get('title', 'No Title'))[:100]
            record['url'] = str(record['url'])
        
        return render_template('dashboard.html', 
                             metrics=metrics,
                             table_data=table_data,
                             total_pages=len(crawl_data))


    @app.route('/data')
    def data():
        """JSON endpoint for crawl data."""
        global crawl_data
        
        if crawl_data is None:
            crawl_data = load_crawl_data()
        
        if crawl_data is None:
            return jsonify({"error": "No data available"}), 404
        
        # Return data as JSON
        data_dict = crawl_data.to_dict('records')
        
        # Convert numpy types
        for record in data_dict:
            for key, value in record.items():
                if pd.isna(value):
                    record[key] = None
                elif isinstance(value, (np.integer, np.int64)):
                    record[key] = int(value)
                elif isinstance(value, (np.floating, np.float64)):
                    record[key] = float(value) if not pd.isna(value) else None
                else:
                    record[key] = str(value) if value is not None else None
        
        return jsonify({
            "data": data_dict,
            "metrics": calculate_metrics(crawl_data),
            "timestamp": data_loaded_time
        })


    @app.route('/about')
    def about():
        """About page route."""
        return render_template('about.html')


    @app.route('/api/network-graph')
    def api_network_graph():
        """API endpoint for network graph."""
        global crawl_data
        if crawl_data is None:
            crawl_data = load_crawl_data()
        
        graph_json = create_network_graph(crawl_data)
        if graph_json:
            from flask import Response
            return Response(graph_json, mimetype='application/json')
        return jsonify({"error": "Could not generate graph"}), 500


    @app.route('/api/depth-chart')
    def api_depth_chart():
        """API endpoint for depth bar chart."""
        global crawl_data
        if crawl_data is None:
            crawl_data = load_crawl_data()
        
        chart_json = create_depth_bar_chart(crawl_data)
        if chart_json:
            from flask import Response
            return Response(chart_json, mimetype='application/json')
        return jsonify({"error": "Could not generate chart"}), 500


    @app.route('/api/section-chart')
    def api_section_chart():
        """API endpoint for section pie chart."""
        global crawl_data
        if crawl_data is None:
            crawl_data = load_crawl_data()
        
        chart_json = create_section_pie_chart(crawl_data)
        if chart_json:
            from flask import Response
            return Response(chart_json, mimetype='application/json')
        return jsonify({"error": "Could not generate chart"}), 500


    @app.route('/api/treemap')
    def api_treemap():
        """API endpoint for treemap."""
        global crawl_data
        if crawl_data is None:
            crawl_data = load_crawl_data()
        
        treemap_json = create_treemap(crawl_data)
        if treemap_json:
            from flask import Response
            return Response(treemap_json, mimetype='application/json')
        return jsonify({"error": "Could not generate treemap"}), 500


    @app.route('/api/refresh')
    def api_refresh():
        """Refresh data endpoint."""
        global crawl_data, data_loaded_time
        crawl_data = load_crawl_data()
        
        if crawl_data is None:
            return jsonify({"error": "Could not refresh data"}), 500
        
        return jsonify({
            "success": True,
            "timestamp": data_loaded_time,
            "metrics": calculate_metrics(crawl_data)
        })


    return app


if __name__ == '__main__':
    # For direct execution
    app = create_flask_app()
    app.run(debug=True, host='0.0.0.0', port=5000)

