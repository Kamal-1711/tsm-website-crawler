"""
HTML Templates Module for TSM Dashboard
=======================================

Generates HTML templates for the Flask dashboard with embedded CSS and JavaScript.
Uses Jinja2-compatible template strings for dynamic content rendering.

Author: TSM Web Crawler Project
"""

from __future__ import annotations

from typing import Dict, Any


# ---------------------------------------------------------------------------
# Base HTML Template
# ---------------------------------------------------------------------------


def get_base_html_template() -> str:
    """
    Get the base HTML structure for all pages.
    
    Returns:
        Complete HTML template string with embedded CSS and JavaScript.
    """
    return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TSM Website Structure Dashboard</title>
    
    <!-- External CSS Libraries -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.datatables.net/1.13.6/css/jquery.dataTables.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    
    <!-- External JS Libraries -->
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <script src="https://code.jquery.com/jquery-3.7.0.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    
    <style>
        /* ================================================================
           CSS Variables - Design System
           ================================================================ */
        :root {
            --primary-color: #3B82F6;
            --primary-hover: #2563EB;
            --primary-light: #DBEAFE;
            --secondary-color: #1F2937;
            --success-color: #10B981;
            --success-light: #D1FAE5;
            --warning-color: #F59E0B;
            --warning-light: #FEF3C7;
            --danger-color: #EF4444;
            --danger-light: #FEE2E2;
            --light-bg: #F9FAFB;
            --dark-bg: #111827;
            --card-bg: #FFFFFF;
            --border-color: #E5E7EB;
            --text-primary: #111827;
            --text-secondary: #6B7280;
            --text-muted: #9CA3AF;
            --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
            --shadow: 0 1px 3px rgba(0,0,0,0.1), 0 1px 2px rgba(0,0,0,0.06);
            --shadow-md: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06);
            --shadow-lg: 0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05);
            --radius-sm: 4px;
            --radius: 8px;
            --radius-lg: 12px;
            --radius-xl: 16px;
            --transition: all 0.3s ease;
        }
        
        /* Dark Mode Variables */
        .dark-mode {
            --light-bg: #111827;
            --dark-bg: #000000;
            --card-bg: #1F2937;
            --border-color: #374151;
            --text-primary: #F9FAFB;
            --text-secondary: #D1D5DB;
            --text-muted: #9CA3AF;
        }
        
        /* ================================================================
           Base Styles
           ================================================================ */
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        html {
            scroll-behavior: smooth;
        }
        
        body {
            font-family: 'Inter', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, var(--light-bg) 0%, #EFF6FF 100%);
            color: var(--text-primary);
            line-height: 1.6;
            min-height: 100vh;
            transition: var(--transition);
        }
        
        .dark-mode body {
            background: linear-gradient(135deg, var(--dark-bg) 0%, #1F2937 100%);
        }
        
        /* ================================================================
           Header Styles
           ================================================================ */
        .dashboard-header {
            position: sticky;
            top: 0;
            z-index: 1000;
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-hover) 100%);
            padding: 16px 24px;
            box-shadow: var(--shadow-lg);
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 16px;
        }
        
        .header-brand {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .header-logo {
            width: 40px;
            height: 40px;
            background: rgba(255,255,255,0.2);
            border-radius: var(--radius);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
        }
        
        .header-title {
            color: white;
        }
        
        .header-title h1 {
            font-size: 1.5rem;
            font-weight: 700;
            margin: 0;
            letter-spacing: -0.025em;
        }
        
        .header-title p {
            font-size: 0.875rem;
            opacity: 0.9;
            margin: 0;
        }
        
        .header-controls {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .header-timestamp {
            color: rgba(255,255,255,0.8);
            font-size: 0.75rem;
        }
        
        /* ================================================================
           Button Styles
           ================================================================ */
        .btn-custom {
            padding: 10px 16px;
            border-radius: var(--radius);
            font-size: 0.875rem;
            font-weight: 500;
            cursor: pointer;
            transition: var(--transition);
            border: none;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            min-height: 44px;
            min-width: 44px;
        }
        
        .btn-primary-custom {
            background: white;
            color: var(--primary-color);
        }
        
        .btn-primary-custom:hover {
            background: var(--light-bg);
            transform: translateY(-1px);
        }
        
        .btn-secondary-custom {
            background: rgba(255,255,255,0.2);
            color: white;
            backdrop-filter: blur(10px);
        }
        
        .btn-secondary-custom:hover {
            background: rgba(255,255,255,0.3);
        }
        
        .btn-outline-custom {
            background: transparent;
            color: var(--primary-color);
            border: 1px solid var(--primary-color);
        }
        
        .btn-outline-custom:hover {
            background: var(--primary-light);
        }
        
        .btn-icon {
            width: 44px;
            height: 44px;
            padding: 0;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        /* ================================================================
           Navigation Tabs
           ================================================================ */
        .nav-tabs-custom {
            background: var(--card-bg);
            border-bottom: 1px solid var(--border-color);
            padding: 0 24px;
            display: flex;
            gap: 0;
            overflow-x: auto;
            scrollbar-width: none;
        }
        
        .nav-tabs-custom::-webkit-scrollbar {
            display: none;
        }
        
        .nav-tab-item {
            padding: 16px 24px;
            font-size: 0.875rem;
            font-weight: 500;
            color: var(--text-secondary);
            cursor: pointer;
            border-bottom: 3px solid transparent;
            transition: var(--transition);
            white-space: nowrap;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .nav-tab-item:hover {
            color: var(--primary-color);
            background: var(--primary-light);
        }
        
        .nav-tab-item.active {
            color: var(--primary-color);
            border-bottom-color: var(--primary-color);
            background: transparent;
        }
        
        .nav-tab-item i {
            font-size: 1rem;
        }
        
        /* ================================================================
           Main Content Area
           ================================================================ */
        .main-content {
            padding: 24px;
            max-width: 1600px;
            margin: 0 auto;
        }
        
        /* ================================================================
           Card Styles
           ================================================================ */
        .card-custom {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow);
            transition: var(--transition);
            padding: 20px;
            margin-bottom: 16px;
        }
        
        .card-custom:hover {
            box-shadow: var(--shadow-lg);
            transform: translateY(-2px);
        }
        
        .card-header-custom {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 1px solid var(--border-color);
        }
        
        .card-title {
            font-size: 1rem;
            font-weight: 600;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .card-title i {
            color: var(--primary-color);
        }
        
        /* ================================================================
           Summary Cards (Statistics)
           ================================================================ */
        .summary-cards-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            margin-bottom: 24px;
        }
        
        @media (max-width: 1200px) {
            .summary-cards-grid {
                grid-template-columns: repeat(2, 1fr);
            }
        }
        
        @media (max-width: 576px) {
            .summary-cards-grid {
                grid-template-columns: 1fr;
            }
        }
        
        .summary-card {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-lg);
            padding: 20px;
            transition: var(--transition);
            position: relative;
            overflow: hidden;
        }
        
        .summary-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 4px;
            height: 100%;
            background: var(--primary-color);
        }
        
        .summary-card.success::before { background: var(--success-color); }
        .summary-card.warning::before { background: var(--warning-color); }
        .summary-card.danger::before { background: var(--danger-color); }
        
        .summary-card:hover {
            box-shadow: var(--shadow-lg);
            transform: translateY(-2px);
        }
        
        .summary-card-label {
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-secondary);
            margin-bottom: 8px;
        }
        
        .summary-card-value {
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--text-primary);
            line-height: 1;
            margin-bottom: 4px;
        }
        
        .summary-card-value.success { color: var(--success-color); }
        .summary-card-value.warning { color: var(--warning-color); }
        .summary-card-value.danger { color: var(--danger-color); }
        
        .summary-card-subtext {
            font-size: 0.75rem;
            color: var(--text-muted);
        }
        
        /* ================================================================
           Chart Containers
           ================================================================ */
        .chart-container {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow);
            padding: 16px;
            height: 400px;
            width: 100%;
            overflow: hidden;
        }
        
        .chart-container.large {
            height: 600px;
        }
        
        .chart-container .chart-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }
        
        .chart-container .chart-title {
            font-size: 0.875rem;
            font-weight: 600;
            color: var(--text-primary);
        }
        
        .chart-container .chart-controls {
            display: flex;
            gap: 8px;
        }
        
        .chart-container .plotly-chart {
            width: 100%;
            height: calc(100% - 40px);
        }
        
        /* ================================================================
           Grid Layouts
           ================================================================ */
        .grid-2 {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 24px;
        }
        
        .grid-3 {
            display: grid;
            grid-template-columns: 30% 40% 30%;
            gap: 24px;
        }
        
        .grid-4 {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
        }
        
        @media (max-width: 1200px) {
            .grid-2, .grid-3 {
                grid-template-columns: 1fr;
            }
            .grid-4 {
                grid-template-columns: repeat(2, 1fr);
            }
        }
        
        @media (max-width: 576px) {
            .grid-4 {
                grid-template-columns: 1fr;
            }
        }
        
        /* ================================================================
           Data Table Styles
           ================================================================ */
        .data-table-container {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow);
            overflow: hidden;
        }
        
        .table-controls {
            padding: 16px 20px;
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
            align-items: center;
            border-bottom: 1px solid var(--border-color);
            background: var(--light-bg);
        }
        
        .search-input {
            flex: 1;
            min-width: 200px;
            padding: 10px 16px;
            border: 1px solid var(--border-color);
            border-radius: var(--radius);
            font-size: 0.875rem;
            background: var(--card-bg);
            color: var(--text-primary);
            transition: var(--transition);
        }
        
        .search-input:focus {
            outline: none;
            border-color: var(--primary-color);
            box-shadow: 0 0 0 3px var(--primary-light);
        }
        
        .filter-select {
            padding: 10px 16px;
            border: 1px solid var(--border-color);
            border-radius: var(--radius);
            font-size: 0.875rem;
            background: var(--card-bg);
            color: var(--text-primary);
            cursor: pointer;
            min-width: 120px;
        }
        
        .data-table {
            width: 100%;
            border-collapse: collapse;
        }
        
        .data-table th {
            background: var(--primary-color);
            color: white;
            padding: 14px 16px;
            text-align: left;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            cursor: pointer;
            user-select: none;
            position: sticky;
            top: 0;
        }
        
        .data-table th:hover {
            background: var(--primary-hover);
        }
        
        .data-table th i {
            margin-left: 8px;
            opacity: 0.7;
        }
        
        .data-table td {
            padding: 12px 16px;
            border-bottom: 1px solid var(--border-color);
            font-size: 0.875rem;
            color: var(--text-primary);
        }
        
        .data-table tbody tr:nth-child(even) {
            background: var(--light-bg);
        }
        
        .data-table tbody tr:hover {
            background: var(--primary-light);
        }
        
        .data-table .url-cell {
            max-width: 300px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            font-family: monospace;
            font-size: 0.8rem;
        }
        
        .table-pagination {
            padding: 16px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-top: 1px solid var(--border-color);
            background: var(--light-bg);
        }
        
        .pagination-info {
            font-size: 0.875rem;
            color: var(--text-secondary);
        }
        
        .pagination-controls {
            display: flex;
            gap: 8px;
        }
        
        .page-btn {
            padding: 8px 12px;
            border: 1px solid var(--border-color);
            border-radius: var(--radius-sm);
            background: var(--card-bg);
            color: var(--text-primary);
            cursor: pointer;
            font-size: 0.875rem;
            transition: var(--transition);
            min-width: 40px;
            text-align: center;
        }
        
        .page-btn:hover:not(:disabled) {
            background: var(--primary-light);
            border-color: var(--primary-color);
        }
        
        .page-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .page-btn.active {
            background: var(--primary-color);
            color: white;
            border-color: var(--primary-color);
        }
        
        /* ================================================================
           Status Badges
           ================================================================ */
        .status-badge {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            padding: 4px 10px;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 500;
        }
        
        .status-success {
            background: var(--success-light);
            color: var(--success-color);
        }
        
        .status-warning {
            background: var(--warning-light);
            color: var(--warning-color);
        }
        
        .status-danger {
            background: var(--danger-light);
            color: var(--danger-color);
        }
        
        .status-info {
            background: var(--primary-light);
            color: var(--primary-color);
        }
        
        /* ================================================================
           Audit Report Styles
           ================================================================ */
        .report-section {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-lg);
            margin-bottom: 16px;
            overflow: hidden;
            transition: var(--transition);
        }
        
        .report-section:hover {
            box-shadow: var(--shadow-md);
        }
        
        .report-header {
            padding: 16px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            cursor: pointer;
            background: var(--light-bg);
            border-bottom: 1px solid transparent;
            transition: var(--transition);
        }
        
        .report-header:hover {
            background: var(--primary-light);
        }
        
        .report-section.expanded .report-header {
            border-bottom-color: var(--border-color);
        }
        
        .report-header h3 {
            font-size: 1rem;
            font-weight: 600;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            gap: 10px;
            margin: 0;
        }
        
        .report-header h3 i {
            color: var(--primary-color);
        }
        
        .expand-icon {
            color: var(--text-secondary);
            transition: transform 0.3s ease;
        }
        
        .report-section.expanded .expand-icon {
            transform: rotate(180deg);
        }
        
        .report-content {
            padding: 20px;
            display: none;
        }
        
        .report-section.expanded .report-content {
            display: block;
        }
        
        /* ================================================================
           Issue List Styles
           ================================================================ */
        .issue-list {
            list-style: none;
            padding: 0;
            margin: 0;
        }
        
        .issue-item {
            padding: 12px 16px;
            border-left: 4px solid var(--warning-color);
            background: var(--warning-light);
            margin-bottom: 8px;
            border-radius: 0 var(--radius) var(--radius) 0;
            font-size: 0.875rem;
        }
        
        .issue-item.critical {
            border-left-color: var(--danger-color);
            background: var(--danger-light);
        }
        
        .issue-item.success {
            border-left-color: var(--success-color);
            background: var(--success-light);
        }
        
        .issue-item strong {
            display: block;
            margin-bottom: 4px;
        }
        
        /* ================================================================
           Recommendation List
           ================================================================ */
        .recommendation-list {
            list-style: none;
            padding: 0;
            margin: 0;
        }
        
        .recommendation-item {
            padding: 16px;
            background: var(--light-bg);
            border: 1px solid var(--border-color);
            border-radius: var(--radius);
            margin-bottom: 12px;
        }
        
        .recommendation-priority {
            display: inline-block;
            padding: 4px 10px;
            border-radius: var(--radius-sm);
            font-size: 0.7rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 8px;
        }
        
        .priority-critical {
            background: var(--danger-color);
            color: white;
        }
        
        .priority-important {
            background: var(--warning-color);
            color: white;
        }
        
        .priority-nice {
            background: var(--success-color);
            color: white;
        }
        
        /* ================================================================
           Metrics Grid
           ================================================================ */
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 16px;
        }
        
        .metric-item {
            text-align: center;
            padding: 16px;
            background: var(--light-bg);
            border-radius: var(--radius);
        }
        
        .metric-value {
            font-size: 1.75rem;
            font-weight: 700;
            color: var(--primary-color);
            line-height: 1;
        }
        
        .metric-label {
            font-size: 0.75rem;
            color: var(--text-secondary);
            margin-top: 8px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        /* ================================================================
           Network Graph Legend
           ================================================================ */
        .graph-legend {
            display: flex;
            gap: 24px;
            flex-wrap: wrap;
            padding: 16px;
            background: var(--light-bg);
            border-radius: var(--radius);
            font-size: 0.875rem;
        }
        
        .legend-item {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .legend-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
        }
        
        .legend-dot.depth-0 { background: #1E40AF; }
        .legend-dot.depth-1 { background: #3B82F6; }
        .legend-dot.depth-2 { background: #60A5FA; }
        .legend-dot.depth-3 { background: #93C5FD; }
        .legend-dot.depth-4 { background: #BFDBFE; }
        
        /* ================================================================
           Node Details Panel
           ================================================================ */
        .node-details-panel {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-lg);
            padding: 20px;
            margin-top: 16px;
        }
        
        .node-details-panel h4 {
            font-size: 1rem;
            font-weight: 600;
            margin-bottom: 16px;
            color: var(--text-primary);
        }
        
        .node-detail-row {
            display: flex;
            padding: 8px 0;
            border-bottom: 1px solid var(--border-color);
        }
        
        .node-detail-row:last-child {
            border-bottom: none;
        }
        
        .node-detail-label {
            width: 120px;
            font-weight: 500;
            color: var(--text-secondary);
            font-size: 0.875rem;
        }
        
        .node-detail-value {
            flex: 1;
            color: var(--text-primary);
            font-size: 0.875rem;
            word-break: break-all;
        }
        
        /* ================================================================
           Tab Content
           ================================================================ */
        .tab-content {
            display: none;
            animation: fadeIn 0.3s ease;
        }
        
        .tab-content.active {
            display: block;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        /* ================================================================
           Footer
           ================================================================ */
        .dashboard-footer {
            padding: 24px;
            text-align: center;
            color: var(--text-secondary);
            font-size: 0.875rem;
            border-top: 1px solid var(--border-color);
            margin-top: 32px;
            background: var(--card-bg);
        }
        
        .dashboard-footer a {
            color: var(--primary-color);
            text-decoration: none;
        }
        
        .dashboard-footer a:hover {
            text-decoration: underline;
        }
        
        /* ================================================================
           Utilities
           ================================================================ */
        .text-success { color: var(--success-color) !important; }
        .text-warning { color: var(--warning-color) !important; }
        .text-danger { color: var(--danger-color) !important; }
        .text-primary { color: var(--primary-color) !important; }
        .text-muted { color: var(--text-muted) !important; }
        
        .bg-success-light { background: var(--success-light) !important; }
        .bg-warning-light { background: var(--warning-light) !important; }
        .bg-danger-light { background: var(--danger-light) !important; }
        
        .mb-0 { margin-bottom: 0 !important; }
        .mb-1 { margin-bottom: 8px !important; }
        .mb-2 { margin-bottom: 16px !important; }
        .mb-3 { margin-bottom: 24px !important; }
        
        .mt-0 { margin-top: 0 !important; }
        .mt-1 { margin-top: 8px !important; }
        .mt-2 { margin-top: 16px !important; }
        .mt-3 { margin-top: 24px !important; }
        
        /* ================================================================
           Loading Spinner
           ================================================================ */
        .loading-spinner {
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 48px;
        }
        
        .spinner {
            width: 48px;
            height: 48px;
            border: 4px solid var(--border-color);
            border-top-color: var(--primary-color);
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        /* ================================================================
           Scrollbar Styles
           ================================================================ */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: var(--light-bg);
        }
        
        ::-webkit-scrollbar-thumb {
            background: var(--text-muted);
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: var(--text-secondary);
        }
        
        /* ================================================================
           Print Styles
           ================================================================ */
        @media print {
            .dashboard-header,
            .nav-tabs-custom,
            .btn-custom,
            .table-controls,
            .table-pagination {
                display: none !important;
            }
            
            .card-custom,
            .chart-container,
            .data-table-container {
                box-shadow: none !important;
                border: 1px solid #ddd !important;
            }
            
            body {
                background: white !important;
            }
        }
    </style>
</head>
<body>
    {% block content %}{% endblock %}
    
    {% block scripts %}{% endblock %}
</body>
</html>'''


# ---------------------------------------------------------------------------
# Dashboard Tab HTML
# ---------------------------------------------------------------------------


def get_dashboard_tab_html() -> str:
    """
    Get HTML for the Overview tab.
    
    Returns:
        HTML template string for the overview/dashboard tab.
    """
    return '''
<!-- Overview Tab Content -->
<div class="tab-content active" id="tab-overview">
    <!-- Three Column Layout -->
    <div class="grid-3">
        <!-- Left Column: Key Metrics + Important Pages -->
        <div>
            <!-- Key Metrics Card -->
            <div class="card-custom">
                <div class="card-header-custom">
                    <h3 class="card-title">
                        <i class="fas fa-chart-bar"></i>
                        Key Metrics
                    </h3>
                </div>
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
            
            <!-- Top Pages Card -->
            <div class="card-custom">
                <div class="card-header-custom">
                    <h3 class="card-title">
                        <i class="fas fa-trophy"></i>
                        Top Pages
                    </h3>
                </div>
                <ul class="issue-list">
                    {% for page in top_pages[:5] %}
                    <li class="issue-item success">
                        <strong>{{ page.title[:35] }}{% if page.title|length > 35 %}...{% endif %}</strong>
                        <span class="text-muted">{{ page.child_count }} links</span>
                    </li>
                    {% endfor %}
                </ul>
            </div>
        </div>
        
        <!-- Center Column: Network Graph -->
        <div class="chart-container large">
            <div class="chart-header">
                <span class="chart-title">
                    <i class="fas fa-project-diagram"></i>
                    Website Structure Network
                </span>
                <div class="chart-controls">
                    <button class="btn-custom btn-outline-custom btn-icon" onclick="resetNetworkView()" title="Reset View">
                        <i class="fas fa-sync-alt"></i>
                    </button>
                </div>
            </div>
            <div id="network-chart-overview" class="plotly-chart"></div>
        </div>
        
        <!-- Right Column: Issues and Recommendations -->
        <div>
            <!-- Issues Card -->
            <div class="card-custom">
                <div class="card-header-custom">
                    <h3 class="card-title">
                        <i class="fas fa-exclamation-triangle"></i>
                        Issues Found
                    </h3>
                </div>
                <ul class="issue-list">
                    {% if orphan_count > 0 %}
                    <li class="issue-item critical">
                        <strong>{{ orphan_count }} orphan pages</strong>
                        Need internal links for SEO
                    </li>
                    {% endif %}
                    {% if dead_end_count > 0 %}
                    <li class="issue-item">
                        <strong>{{ dead_end_count }} dead-end pages</strong>
                        Need navigation elements
                    </li>
                    {% endif %}
                    {% if bottleneck_count > 0 %}
                    <li class="issue-item">
                        <strong>{{ bottleneck_count }} bottlenecks</strong>
                        Hard to reach pages
                    </li>
                    {% endif %}
                    {% if orphan_count == 0 and dead_end_count == 0 and bottleneck_count == 0 %}
                    <li class="issue-item success">
                        <strong>No critical issues!</strong>
                        Website structure is well-organized
                    </li>
                    {% endif %}
                </ul>
            </div>
            
            <!-- Quick Wins Card -->
            <div class="card-custom">
                <div class="card-header-custom">
                    <h3 class="card-title">
                        <i class="fas fa-lightbulb"></i>
                        Quick Wins
                    </h3>
                </div>
                <ul class="recommendation-list">
                    {% for rec in recommendations.critical[:2] %}
                    <li class="recommendation-item">
                        <span class="recommendation-priority priority-critical">Critical</span>
                        <p class="mb-0">{{ rec.action }}</p>
                    </li>
                    {% endfor %}
                    {% for rec in recommendations.important[:2] %}
                    <li class="recommendation-item">
                        <span class="recommendation-priority priority-important">Important</span>
                        <p class="mb-0">{{ rec.action }}</p>
                    </li>
                    {% endfor %}
                    {% if not recommendations.critical and not recommendations.important %}
                    <li class="recommendation-item">
                        <span class="recommendation-priority priority-nice">Great</span>
                        <p class="mb-0">No urgent actions needed. Consider long-term improvements.</p>
                    </li>
                    {% endif %}
                </ul>
            </div>
        </div>
    </div>
</div>
'''


# ---------------------------------------------------------------------------
# Network Tab HTML
# ---------------------------------------------------------------------------


def get_network_tab_html() -> str:
    """
    Get HTML for the Network Visualization tab.
    
    Returns:
        HTML template string for the network visualization tab.
    """
    return '''
<!-- Network Visualization Tab Content -->
<div class="tab-content" id="tab-network">
    <!-- Large Network Graph Container -->
    <div class="chart-container large">
        <div class="chart-header">
            <span class="chart-title">
                <i class="fas fa-project-diagram"></i>
                Interactive Network Visualization
            </span>
            <div class="chart-controls">
                <button class="btn-custom btn-outline-custom" onclick="zoomIn()">
                    <i class="fas fa-search-plus"></i> Zoom In
                </button>
                <button class="btn-custom btn-outline-custom" onclick="zoomOut()">
                    <i class="fas fa-search-minus"></i> Zoom Out
                </button>
                <button class="btn-custom btn-outline-custom" onclick="resetNetworkView()">
                    <i class="fas fa-sync-alt"></i> Reset
                </button>
                <button class="btn-custom btn-primary-custom" onclick="exportNetworkPNG()">
                    <i class="fas fa-download"></i> Export PNG
                </button>
            </div>
        </div>
        <div id="network-chart-full" class="plotly-chart" style="height: calc(100% - 50px);"></div>
    </div>
    
    <!-- Legend -->
    <div class="card-custom mt-2">
        <div class="graph-legend">
            <div class="legend-item">
                <span class="legend-dot depth-0"></span>
                <span>Depth 0 (Homepage)</span>
            </div>
            <div class="legend-item">
                <span class="legend-dot depth-1"></span>
                <span>Depth 1 (Main Sections)</span>
            </div>
            <div class="legend-item">
                <span class="legend-dot depth-2"></span>
                <span>Depth 2 (Sub-pages)</span>
            </div>
            <div class="legend-item">
                <span class="legend-dot depth-3"></span>
                <span>Depth 3 (Detail Pages)</span>
            </div>
            <div class="legend-item">
                <span class="legend-dot depth-4"></span>
                <span>Depth 4+ (Deep Pages)</span>
            </div>
            <div class="legend-item">
                <i class="fas fa-circle text-muted" style="font-size: 0.5rem;"></i>
                <span class="text-muted">Node size = Link count</span>
            </div>
        </div>
    </div>
    
    <!-- Node Details Panel -->
    <div class="node-details-panel" id="node-details">
        <h4><i class="fas fa-info-circle text-primary"></i> Node Details</h4>
        <p class="text-muted">Click on a node in the graph to see its details here.</p>
        <div id="node-details-content" style="display: none;">
            <div class="node-detail-row">
                <span class="node-detail-label">URL:</span>
                <span class="node-detail-value" id="detail-url">-</span>
            </div>
            <div class="node-detail-row">
                <span class="node-detail-label">Title:</span>
                <span class="node-detail-value" id="detail-title">-</span>
            </div>
            <div class="node-detail-row">
                <span class="node-detail-label">Depth:</span>
                <span class="node-detail-value" id="detail-depth">-</span>
            </div>
            <div class="node-detail-row">
                <span class="node-detail-label">Child Count:</span>
                <span class="node-detail-value" id="detail-children">-</span>
            </div>
            <div class="node-detail-row">
                <span class="node-detail-label">Parent URL:</span>
                <span class="node-detail-value" id="detail-parent">-</span>
            </div>
        </div>
    </div>
</div>
'''


# ---------------------------------------------------------------------------
# Statistics Tab HTML
# ---------------------------------------------------------------------------


def get_statistics_tab_html() -> str:
    """
    Get HTML for the Statistics tab.
    
    Returns:
        HTML template string for the statistics tab.
    """
    return '''
<!-- Statistics Tab Content -->
<div class="tab-content" id="tab-statistics">
    <!-- Row 1: Charts -->
    <div class="grid-2 mb-3">
        <!-- Bar Chart: Pages Per Depth -->
        <div class="chart-container">
            <div class="chart-header">
                <span class="chart-title">
                    <i class="fas fa-chart-bar"></i>
                    Pages by Depth Level
                </span>
            </div>
            <div id="depth-chart" class="plotly-chart"></div>
        </div>
        
        <!-- Pie Chart: Content Distribution -->
        <div class="chart-container">
            <div class="chart-header">
                <span class="chart-title">
                    <i class="fas fa-chart-pie"></i>
                    Content Distribution by Section
                </span>
            </div>
            <div id="section-chart" class="plotly-chart"></div>
        </div>
    </div>
    
    <!-- Row 2: Metrics Cards -->
    <div class="grid-4 mb-3">
        <div class="summary-card">
            <div class="summary-card-label">Breadth</div>
            <div class="summary-card-value text-primary">
                {{ (stats.total_pages / (stats.max_depth + 1)) | round(1) }}
            </div>
            <div class="summary-card-subtext">Avg pages per depth</div>
        </div>
        <div class="summary-card">
            <div class="summary-card-label">Depth Range</div>
            <div class="summary-card-value text-primary">
                0 - {{ stats.max_depth }}
            </div>
            <div class="summary-card-subtext">Min to max depth</div>
        </div>
        <div class="summary-card">
            <div class="summary-card-label">Link Density</div>
            <div class="summary-card-value text-primary">
                {{ stats.avg_links }}
            </div>
            <div class="summary-card-subtext">Avg links per page</div>
        </div>
        <div class="summary-card success">
            <div class="summary-card-label">Connectivity</div>
            <div class="summary-card-value success">
                {{ ia_score.breakdown.connectivity_score }}%
            </div>
            <div class="summary-card-subtext">Pages reachable from home</div>
        </div>
    </div>
    
    <!-- Row 3: Detailed Metrics Table -->
    <div class="card-custom">
        <div class="card-header-custom">
            <h3 class="card-title">
                <i class="fas fa-table"></i>
                Detailed Metrics Comparison
            </h3>
        </div>
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
                        <td><strong>Max Depth</strong></td>
                        <td>{{ stats.max_depth }}</td>
                        <td>≤ 4 clicks</td>
                        <td>
                            {% if stats.max_depth <= 4 %}
                            <span class="status-badge status-success"><i class="fas fa-check"></i> Good</span>
                            {% else %}
                            <span class="status-badge status-warning"><i class="fas fa-exclamation"></i> Review</span>
                            {% endif %}
                        </td>
                        <td>{{ 'Optimal depth structure' if stats.max_depth <= 4 else 'Consider restructuring deep pages' }}</td>
                    </tr>
                    <tr>
                        <td><strong>Average Depth</strong></td>
                        <td>{{ stats.avg_depth }}</td>
                        <td>≤ 3.0 clicks</td>
                        <td>
                            {% if stats.avg_depth <= 3 %}
                            <span class="status-badge status-success"><i class="fas fa-check"></i> Good</span>
                            {% else %}
                            <span class="status-badge status-warning"><i class="fas fa-exclamation"></i> Review</span>
                            {% endif %}
                        </td>
                        <td>{{ 'Content easily accessible' if stats.avg_depth <= 3 else 'Move important content higher' }}</td>
                    </tr>
                    <tr>
                        <td><strong>IA Score</strong></td>
                        <td>{{ ia_score.final_score }}/100</td>
                        <td>≥ 75</td>
                        <td>
                            {% if ia_score.final_score >= 75 %}
                            <span class="status-badge status-success"><i class="fas fa-check"></i> {{ ia_score.health_status }}</span>
                            {% elif ia_score.final_score >= 50 %}
                            <span class="status-badge status-warning"><i class="fas fa-exclamation"></i> {{ ia_score.health_status }}</span>
                            {% else %}
                            <span class="status-badge status-danger"><i class="fas fa-times"></i> {{ ia_score.health_status }}</span>
                            {% endif %}
                        </td>
                        <td>{{ ia_score.interpretation }}</td>
                    </tr>
                    <tr>
                        <td><strong>Orphan Pages</strong></td>
                        <td>{{ orphan_count }}</td>
                        <td>0</td>
                        <td>
                            {% if orphan_count == 0 %}
                            <span class="status-badge status-success"><i class="fas fa-check"></i> Good</span>
                            {% else %}
                            <span class="status-badge status-danger"><i class="fas fa-times"></i> Fix Required</span>
                            {% endif %}
                        </td>
                        <td>{{ 'No orphan pages detected' if orphan_count == 0 else 'Add internal links to orphan pages' }}</td>
                    </tr>
                    <tr>
                        <td><strong>Dead Ends</strong></td>
                        <td>{{ dead_end_count }}</td>
                        <td>< 10% of pages</td>
                        <td>
                            {% if dead_end_count < stats.total_pages * 0.1 %}
                            <span class="status-badge status-success"><i class="fas fa-check"></i> Good</span>
                            {% else %}
                            <span class="status-badge status-warning"><i class="fas fa-exclamation"></i> Review</span>
                            {% endif %}
                        </td>
                        <td>{{ 'Acceptable dead end rate' if dead_end_count < stats.total_pages * 0.1 else 'Add navigation to dead-end pages' }}</td>
                    </tr>
                    <tr>
                        <td><strong>Link Density</strong></td>
                        <td>{{ stats.avg_links }} links/page</td>
                        <td>10-50 links</td>
                        <td>
                            {% if 10 <= stats.avg_links <= 50 %}
                            <span class="status-badge status-success"><i class="fas fa-check"></i> Good</span>
                            {% elif stats.avg_links < 10 %}
                            <span class="status-badge status-warning"><i class="fas fa-exclamation"></i> Low</span>
                            {% else %}
                            <span class="status-badge status-warning"><i class="fas fa-exclamation"></i> High</span>
                            {% endif %}
                        </td>
                        <td>{{ 'Healthy internal linking' if 10 <= stats.avg_links <= 50 else 'Adjust internal linking strategy' }}</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
</div>
'''


# ---------------------------------------------------------------------------
# Audit Tab HTML
# ---------------------------------------------------------------------------


def get_audit_tab_html() -> str:
    """
    Get HTML for the Audit Report tab.
    
    Returns:
        HTML template string for the audit report tab.
    """
    return '''
<!-- Audit Report Tab Content -->
<div class="tab-content" id="tab-audit">
    <!-- Export Controls -->
    <div style="display: flex; justify-content: flex-end; gap: 8px; margin-bottom: 16px;">
        <button class="btn-custom btn-outline-custom" onclick="window.open('/download-report?format=txt')">
            <i class="fas fa-file-alt"></i> Export TXT
        </button>
        <button class="btn-custom btn-primary-custom" onclick="window.print()">
            <i class="fas fa-print"></i> Print Report
        </button>
    </div>
    
    <!-- Executive Summary Section -->
    <div class="report-section expanded">
        <div class="report-header" onclick="toggleReportSection(this)">
            <h3><i class="fas fa-clipboard-list"></i> Executive Summary</h3>
            <i class="fas fa-chevron-down expand-icon"></i>
        </div>
        <div class="report-content">
            <div class="metrics-grid mb-2">
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
                    <div class="metric-value {% if ia_score.health_status == 'Excellent' or ia_score.health_status == 'Good' %}text-success{% elif ia_score.health_status == 'Needs Improvement' %}text-warning{% else %}text-danger{% endif %}">
                        {{ ia_score.health_status }}
                    </div>
                    <div class="metric-label">Status</div>
                </div>
            </div>
            <p class="text-muted">{{ ia_score.interpretation }}</p>
        </div>
    </div>
    
    <!-- Critical Issues Section -->
    <div class="report-section">
        <div class="report-header" onclick="toggleReportSection(this)">
            <h3><i class="fas fa-exclamation-circle text-danger"></i> Critical Issues ({{ orphan_count + dead_end_count + bottleneck_count }})</h3>
            <i class="fas fa-chevron-down expand-icon"></i>
        </div>
        <div class="report-content">
            <ul class="issue-list">
                {% if orphan_count > 0 %}
                <li class="issue-item critical">
                    <strong><i class="fas fa-unlink"></i> Orphan Pages: {{ orphan_count }}</strong>
                    Pages with no inbound links. Add internal links to improve SEO and discoverability.
                </li>
                {% endif %}
                {% if dead_end_count > 0 %}
                <li class="issue-item">
                    <strong><i class="fas fa-sign-out-alt"></i> Dead-End Pages: {{ dead_end_count }}</strong>
                    Pages with no outbound navigation. Add related links or call-to-actions.
                </li>
                {% endif %}
                {% if bottleneck_count > 0 %}
                <li class="issue-item">
                    <strong><i class="fas fa-hourglass-half"></i> Navigation Bottlenecks: {{ bottleneck_count }}</strong>
                    Pages requiring more than 3 clicks to reach. Consider restructuring.
                </li>
                {% endif %}
                {% if orphan_count == 0 and dead_end_count == 0 and bottleneck_count == 0 %}
                <li class="issue-item success">
                    <strong><i class="fas fa-check-circle"></i> No Critical Issues Found!</strong>
                    Your website structure is well-organized.
                </li>
                {% endif %}
            </ul>
        </div>
    </div>
    
    <!-- Recommendations Section -->
    <div class="report-section">
        <div class="report-header" onclick="toggleReportSection(this)">
            <h3><i class="fas fa-lightbulb text-warning"></i> Recommendations</h3>
            <i class="fas fa-chevron-down expand-icon"></i>
        </div>
        <div class="report-content">
            {% if recommendations.critical %}
            <h5 class="text-danger mb-1"><i class="fas fa-fire"></i> Critical (Do This Week)</h5>
            <ul class="recommendation-list mb-2">
                {% for rec in recommendations.critical %}
                <li class="recommendation-item">
                    <span class="recommendation-priority priority-critical">Critical</span>
                    <p><strong>{{ rec.action }}</strong></p>
                    <p class="text-muted mb-0" style="font-size: 0.875rem;">
                        <i class="fas fa-clock"></i> Effort: {{ rec.effort_estimate }} | 
                        <i class="fas fa-bolt"></i> Impact: {{ rec.expected_impact }}
                    </p>
                </li>
                {% endfor %}
            </ul>
            {% endif %}
            
            {% if recommendations.important %}
            <h5 class="text-warning mb-1"><i class="fas fa-exclamation-triangle"></i> Important (Do This Month)</h5>
            <ul class="recommendation-list mb-2">
                {% for rec in recommendations.important %}
                <li class="recommendation-item">
                    <span class="recommendation-priority priority-important">Important</span>
                    <p><strong>{{ rec.action }}</strong></p>
                    <p class="text-muted mb-0" style="font-size: 0.875rem;">
                        <i class="fas fa-clock"></i> Effort: {{ rec.effort_estimate }} | 
                        <i class="fas fa-signal"></i> Difficulty: {{ rec.difficulty }}
                    </p>
                </li>
                {% endfor %}
            </ul>
            {% endif %}
            
            {% if recommendations.nice_to_have %}
            <h5 class="text-success mb-1"><i class="fas fa-star"></i> Nice to Have (Long Term)</h5>
            <ul class="recommendation-list">
                {% for rec in recommendations.nice_to_have %}
                <li class="recommendation-item">
                    <span class="recommendation-priority priority-nice">Enhancement</span>
                    <p><strong>{{ rec.action }}</strong></p>
                    <p class="text-muted mb-0" style="font-size: 0.875rem;">
                        <i class="fas fa-gem"></i> Strategic Value: {{ rec.expected_impact }}
                    </p>
                </li>
                {% endfor %}
            </ul>
            {% endif %}
        </div>
    </div>
    
    <!-- Implementation Roadmap Section -->
    <div class="report-section">
        <div class="report-header" onclick="toggleReportSection(this)">
            <h3><i class="fas fa-road text-primary"></i> Implementation Roadmap</h3>
            <i class="fas fa-chevron-down expand-icon"></i>
        </div>
        <div class="report-content">
            <div style="padding: 16px; background: var(--light-bg); border-radius: var(--radius); font-family: monospace; font-size: 0.875rem; line-height: 1.8;">
                <strong class="text-primary">PHASE 1 (Week 1-2): Quick Wins</strong><br>
                ├─ <i class="fas fa-link text-success"></i> Fix orphan pages with internal links<br>
                ├─ <i class="fas fa-compass text-success"></i> Add navigation to dead ends<br>
                └─ <i class="fas fa-tags text-success"></i> Update meta descriptions<br><br>
                
                <strong class="text-warning">PHASE 2 (Month 1): Major Improvements</strong><br>
                ├─ <i class="fas fa-sitemap text-warning"></i> Reorganize deep content<br>
                ├─ <i class="fas fa-layer-group text-warning"></i> Create section landing pages<br>
                └─ <i class="fas fa-th-large text-warning"></i> Implement related content widgets<br><br>
                
                <strong class="text-danger">PHASE 3 (Quarter 1): Strategic Changes</strong><br>
                ├─ <i class="fas fa-bread-slice text-danger"></i> Implement breadcrumb navigation<br>
                ├─ <i class="fas fa-search text-danger"></i> Add site search functionality<br>
                └─ <i class="fas fa-map text-danger"></i> Create comprehensive sitemap
            </div>
        </div>
    </div>
    
    <!-- Score Breakdown Section -->
    <div class="report-section">
        <div class="report-header" onclick="toggleReportSection(this)">
            <h3><i class="fas fa-chart-line text-success"></i> IA Score Breakdown</h3>
            <i class="fas fa-chevron-down expand-icon"></i>
        </div>
        <div class="report-content">
            <div class="grid-3" style="grid-template-columns: repeat(3, 1fr);">
                <div class="metric-item">
                    <div class="metric-value">{{ ia_score.breakdown.depth_score }}/100</div>
                    <div class="metric-label">Depth Score</div>
                </div>
                <div class="metric-item">
                    <div class="metric-value">{{ ia_score.breakdown.balance_score }}/100</div>
                    <div class="metric-label">Balance Score</div>
                </div>
                <div class="metric-item">
                    <div class="metric-value">{{ ia_score.breakdown.connectivity_score }}/100</div>
                    <div class="metric-label">Connectivity Score</div>
                </div>
            </div>
        </div>
    </div>
</div>
'''


# ---------------------------------------------------------------------------
# Data Table Tab HTML
# ---------------------------------------------------------------------------


def get_data_table_tab_html() -> str:
    """
    Get HTML for the Data Table tab.
    
    Returns:
        HTML template string for the data table tab.
    """
    return '''
<!-- Data Table Tab Content -->
<div class="tab-content" id="tab-data">
    <div class="data-table-container">
        <!-- Table Controls -->
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
            <select class="filter-select" id="rowsPerPage" onchange="changeRowsPerPage()">
                <option value="10">10 rows</option>
                <option value="25" selected>25 rows</option>
                <option value="50">50 rows</option>
                <option value="100">100 rows</option>
            </select>
            <button class="btn-custom btn-primary-custom" onclick="window.open('/download-data')">
                <i class="fas fa-download"></i> Export CSV
            </button>
        </div>
        
        <!-- Data Table -->
        <div style="overflow-x: auto; max-height: 600px;">
            <table class="data-table" id="dataTable">
                <thead>
                    <tr>
                        <th onclick="sortTable(0)">
                            URL <i class="fas fa-sort"></i>
                        </th>
                        <th onclick="sortTable(1)">
                            Title <i class="fas fa-sort"></i>
                        </th>
                        <th onclick="sortTable(2)">
                            Depth <i class="fas fa-sort"></i>
                        </th>
                        <th onclick="sortTable(3)">
                            Links <i class="fas fa-sort"></i>
                        </th>
                        <th onclick="sortTable(4)">
                            Status <i class="fas fa-sort"></i>
                        </th>
                    </tr>
                </thead>
                <tbody>
                    {% for row in table_data %}
                    <tr data-depth="{{ row.depth }}" data-status="{{ row.status_code }}">
                        <td class="url-cell" title="{{ row.url }}">
                            <a href="{{ row.url }}" target="_blank" style="color: var(--primary-color); text-decoration: none;">
                                {{ row.url[:60] }}{% if row.url|length > 60 %}...{% endif %}
                            </a>
                        </td>
                        <td>{{ row.title[:45] }}{% if row.title|length > 45 %}...{% endif %}</td>
                        <td>
                            <span class="status-badge status-info">{{ row.depth }}</span>
                        </td>
                        <td>{{ row.child_count }}</td>
                        <td>
                            {% if row.status_code == 200 %}
                            <span class="status-badge status-success">
                                <i class="fas fa-check"></i> {{ row.status_code }}
                            </span>
                            {% elif row.status_code < 400 %}
                            <span class="status-badge status-warning">
                                <i class="fas fa-exclamation"></i> {{ row.status_code }}
                            </span>
                            {% else %}
                            <span class="status-badge status-danger">
                                <i class="fas fa-times"></i> {{ row.status_code }}
                            </span>
                            {% endif %}
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        
        <!-- Pagination -->
        <div class="table-pagination">
            <div class="pagination-info">
                Showing <span id="showingStart">1</span>-<span id="showingEnd">{{ table_data|length }}</span> 
                of <span id="totalRows">{{ stats.total_pages }}</span> entries
            </div>
            <div class="pagination-controls">
                <button class="page-btn" onclick="changePage('first')" title="First">
                    <i class="fas fa-angle-double-left"></i>
                </button>
                <button class="page-btn" onclick="changePage('prev')" title="Previous">
                    <i class="fas fa-angle-left"></i>
                </button>
                <span id="pageNumbers"></span>
                <button class="page-btn" onclick="changePage('next')" title="Next">
                    <i class="fas fa-angle-right"></i>
                </button>
                <button class="page-btn" onclick="changePage('last')" title="Last">
                    <i class="fas fa-angle-double-right"></i>
                </button>
            </div>
        </div>
    </div>
</div>
'''


# ---------------------------------------------------------------------------
# JavaScript Functions
# ---------------------------------------------------------------------------


def get_dashboard_javascript() -> str:
    """
    Get JavaScript code for dashboard interactivity.
    
    Returns:
        JavaScript code string.
    """
    return '''
<script>
    // ================================================================
    // Chart Data (passed from server)
    // ================================================================
    const networkDataOverview = {{ network_graph_json | safe }};
    const networkDataFull = {{ network_graph_json | safe }};
    const depthChartData = {{ depth_chart_json | safe }};
    const sectionChartData = {{ section_chart_json | safe }};
    
    // ================================================================
    // Initialize Charts on Page Load
    // ================================================================
    document.addEventListener('DOMContentLoaded', function() {
        initializeCharts();
        initializeTabNavigation();
        initializeDataTable();
    });
    
    function initializeCharts() {
        // Overview network graph
        if (networkDataOverview && Object.keys(networkDataOverview).length > 0) {
            Plotly.newPlot('network-chart-overview', networkDataOverview.data, networkDataOverview.layout, {
                responsive: true,
                displayModeBar: false
            });
        }
        
        // Depth chart
        if (depthChartData && Object.keys(depthChartData).length > 0) {
            Plotly.newPlot('depth-chart', depthChartData.data, depthChartData.layout, {
                responsive: true,
                displayModeBar: false
            });
        }
        
        // Section chart
        if (sectionChartData && Object.keys(sectionChartData).length > 0) {
            Plotly.newPlot('section-chart', sectionChartData.data, sectionChartData.layout, {
                responsive: true,
                displayModeBar: false
            });
        }
    }
    
    // ================================================================
    // Tab Navigation
    // ================================================================
    function initializeTabNavigation() {
        document.querySelectorAll('.nav-tab-item').forEach(tab => {
            tab.addEventListener('click', function() {
                // Remove active from all tabs
                document.querySelectorAll('.nav-tab-item').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                
                // Add active to clicked tab
                this.classList.add('active');
                const tabId = 'tab-' + this.dataset.tab;
                document.getElementById(tabId).classList.add('active');
                
                // Initialize full network graph when network tab is selected
                if (this.dataset.tab === 'network' && networkDataFull) {
                    setTimeout(() => {
                        Plotly.newPlot('network-chart-full', networkDataFull.data, {
                            ...networkDataFull.layout,
                            height: 500
                        }, {responsive: true});
                    }, 100);
                }
            });
        });
    }
    
    // ================================================================
    // Theme Toggle
    // ================================================================
    function toggleTheme() {
        document.body.classList.toggle('dark-mode');
        const btn = document.querySelector('.theme-toggle-btn');
        const isDark = document.body.classList.contains('dark-mode');
        btn.innerHTML = isDark ? '<i class="fas fa-sun"></i>' : '<i class="fas fa-moon"></i>';
        
        // Update chart backgrounds
        const bgColor = isDark ? 'rgba(31, 41, 55, 0)' : 'rgba(0,0,0,0)';
        ['network-chart-overview', 'depth-chart', 'section-chart'].forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                Plotly.relayout(id, {'paper_bgcolor': bgColor, 'plot_bgcolor': bgColor});
            }
        });
        
        // Save preference
        localStorage.setItem('darkMode', isDark);
    }
    
    // Load saved theme preference
    if (localStorage.getItem('darkMode') === 'true') {
        document.body.classList.add('dark-mode');
    }
    
    // ================================================================
    // Report Section Toggle
    // ================================================================
    function toggleReportSection(header) {
        header.parentElement.classList.toggle('expanded');
    }
    
    // ================================================================
    // Network Graph Controls
    // ================================================================
    function resetNetworkView() {
        const chartId = document.getElementById('network-chart-full') ? 'network-chart-full' : 'network-chart-overview';
        Plotly.relayout(chartId, {
            'xaxis.autorange': true,
            'yaxis.autorange': true
        });
    }
    
    function zoomIn() {
        const chartId = 'network-chart-full';
        const el = document.getElementById(chartId);
        if (el && el.layout) {
            const xRange = el.layout.xaxis.range;
            const yRange = el.layout.yaxis.range;
            const xMid = (xRange[0] + xRange[1]) / 2;
            const yMid = (yRange[0] + yRange[1]) / 2;
            const xSpan = (xRange[1] - xRange[0]) * 0.4;
            const ySpan = (yRange[1] - yRange[0]) * 0.4;
            Plotly.relayout(chartId, {
                'xaxis.range': [xMid - xSpan, xMid + xSpan],
                'yaxis.range': [yMid - ySpan, yMid + ySpan]
            });
        }
    }
    
    function zoomOut() {
        const chartId = 'network-chart-full';
        const el = document.getElementById(chartId);
        if (el && el.layout) {
            const xRange = el.layout.xaxis.range;
            const yRange = el.layout.yaxis.range;
            const xMid = (xRange[0] + xRange[1]) / 2;
            const yMid = (yRange[0] + yRange[1]) / 2;
            const xSpan = (xRange[1] - xRange[0]) * 0.75;
            const ySpan = (yRange[1] - yRange[0]) * 0.75;
            Plotly.relayout(chartId, {
                'xaxis.range': [xMid - xSpan, xMid + xSpan],
                'yaxis.range': [yMid - ySpan, yMid + ySpan]
            });
        }
    }
    
    function exportNetworkPNG() {
        Plotly.downloadImage('network-chart-full', {
            format: 'png',
            width: 1200,
            height: 800,
            filename: 'tsm_network_graph'
        });
    }
    
    // ================================================================
    // Data Table Functions
    // ================================================================
    let currentPage = 1;
    let rowsPerPage = 25;
    let sortDirection = {};
    
    function initializeDataTable() {
        updatePagination();
    }
    
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
        
        document.getElementById('totalRows').textContent = visibleCount;
        currentPage = 1;
        updatePagination();
    }
    
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
        
        // Update sort icons
        const headers = table.querySelectorAll('th');
        headers.forEach((th, idx) => {
            const icon = th.querySelector('i');
            if (icon) {
                if (idx === columnIndex) {
                    icon.className = sortDirection[columnIndex] ? 'fas fa-sort-up' : 'fas fa-sort-down';
                } else {
                    icon.className = 'fas fa-sort';
                }
            }
        });
    }
    
    function changeRowsPerPage() {
        rowsPerPage = parseInt(document.getElementById('rowsPerPage').value);
        currentPage = 1;
        updatePagination();
    }
    
    function changePage(action) {
        const rows = document.querySelectorAll('#dataTable tbody tr:not([style*="display: none"])');
        const totalPages = Math.ceil(rows.length / rowsPerPage);
        
        switch(action) {
            case 'first': currentPage = 1; break;
            case 'prev': currentPage = Math.max(1, currentPage - 1); break;
            case 'next': currentPage = Math.min(totalPages, currentPage + 1); break;
            case 'last': currentPage = totalPages; break;
            default: currentPage = parseInt(action) || 1;
        }
        
        updatePagination();
    }
    
    function updatePagination() {
        const rows = document.querySelectorAll('#dataTable tbody tr');
        const visibleRows = Array.from(rows).filter(r => r.style.display !== 'none');
        const totalPages = Math.ceil(visibleRows.length / rowsPerPage);
        
        // Hide all rows first
        visibleRows.forEach((row, idx) => {
            const start = (currentPage - 1) * rowsPerPage;
            const end = start + rowsPerPage;
            row.style.display = (idx >= start && idx < end) ? '' : 'none';
        });
        
        // Update info
        const start = Math.min((currentPage - 1) * rowsPerPage + 1, visibleRows.length);
        const end = Math.min(currentPage * rowsPerPage, visibleRows.length);
        document.getElementById('showingStart').textContent = start;
        document.getElementById('showingEnd').textContent = end;
        
        // Update page numbers
        const pageNumbers = document.getElementById('pageNumbers');
        if (pageNumbers) {
            let html = '';
            for (let i = Math.max(1, currentPage - 2); i <= Math.min(totalPages, currentPage + 2); i++) {
                html += `<button class="page-btn ${i === currentPage ? 'active' : ''}" onclick="changePage(${i})">${i}</button>`;
            }
            pageNumbers.innerHTML = html;
        }
    }
    
    // ================================================================
    // Utility Functions
    // ================================================================
    function refreshData() {
        window.location.href = '/?refresh=1';
    }
    
    function exportReport() {
        window.open('/download-report?format=txt');
    }
</script>
'''


# ---------------------------------------------------------------------------
# Complete Dashboard Template
# ---------------------------------------------------------------------------


def get_complete_dashboard_template() -> str:
    """
    Get the complete dashboard HTML template with all components.
    
    Returns:
        Complete HTML template string ready for Flask render_template_string.
    """
    base = get_base_html_template()
    
    # Build the content block
    content = '''
{% block content %}
    <!-- Header -->
    <header class="dashboard-header">
        <div class="header-brand">
            <div class="header-logo">🌐</div>
            <div class="header-title">
                <h1>TSM Website Structure Dashboard</h1>
                <p>Comprehensive Website Audit & Insights</p>
            </div>
        </div>
        <div class="header-controls">
            <span class="header-timestamp">Last Updated: {{ timestamp }}</span>
            <button class="btn-custom btn-secondary-custom" onclick="refreshData()">
                <i class="fas fa-sync-alt"></i> Refresh
            </button>
            <button class="btn-custom btn-primary-custom" onclick="exportReport()">
                <i class="fas fa-download"></i> Export Report
            </button>
            <button class="btn-custom btn-secondary-custom btn-icon theme-toggle-btn" onclick="toggleTheme()" title="Toggle Theme">
                <i class="fas fa-moon"></i>
            </button>
        </div>
    </header>
    
    <!-- Navigation Tabs -->
    <nav class="nav-tabs-custom">
        <div class="nav-tab-item active" data-tab="overview">
            <i class="fas fa-th-large"></i> Overview
        </div>
        <div class="nav-tab-item" data-tab="network">
            <i class="fas fa-project-diagram"></i> Network
        </div>
        <div class="nav-tab-item" data-tab="statistics">
            <i class="fas fa-chart-bar"></i> Statistics
        </div>
        <div class="nav-tab-item" data-tab="audit">
            <i class="fas fa-clipboard-check"></i> Audit Report
        </div>
        <div class="nav-tab-item" data-tab="data">
            <i class="fas fa-table"></i> Data Table
        </div>
    </nav>
    
    <!-- Main Content -->
    <main class="main-content">
        <!-- Summary Cards -->
        <div class="summary-cards-grid">
            <div class="summary-card">
                <div class="summary-card-label">Total Pages</div>
                <div class="summary-card-value">{{ stats.total_pages }}</div>
                <div class="summary-card-subtext">Comprehensive crawl</div>
            </div>
            <div class="summary-card {{ 'success' if ia_score.final_score >= 75 else 'warning' if ia_score.final_score >= 50 else 'danger' }}">
                <div class="summary-card-label">Architecture Score</div>
                <div class="summary-card-value {{ 'success' if ia_score.final_score >= 75 else 'warning' if ia_score.final_score >= 50 else 'danger' }}">
                    {{ ia_score.final_score }}/100
                </div>
                <div class="summary-card-subtext">{{ ia_score.health_status }}</div>
            </div>
            <div class="summary-card {{ 'success' if stats.avg_depth <= 3 else 'warning' if stats.avg_depth <= 4 else 'danger' }}">
                <div class="summary-card-label">Average Depth</div>
                <div class="summary-card-value {{ 'success' if stats.avg_depth <= 3 else 'warning' if stats.avg_depth <= 4 else 'danger' }}">
                    {{ stats.avg_depth }}
                </div>
                <div class="summary-card-subtext">{{ 'Optimal' if stats.avg_depth <= 4 else 'Needs Optimization' }}</div>
            </div>
            <div class="summary-card {{ 'success' if ia_score.health_status in ['Excellent', 'Good'] else 'warning' if ia_score.health_status == 'Needs Improvement' else 'danger' }}">
                <div class="summary-card-label">Health Status</div>
                <div class="summary-card-value {{ 'success' if ia_score.health_status in ['Excellent', 'Good'] else 'warning' if ia_score.health_status == 'Needs Improvement' else 'danger' }}">
                    {{ ia_score.health_status }}
                </div>
                <div class="summary-card-subtext">Based on composite score</div>
            </div>
        </div>
        
        ''' + get_dashboard_tab_html() + '''
        ''' + get_network_tab_html() + '''
        ''' + get_statistics_tab_html() + '''
        ''' + get_audit_tab_html() + '''
        ''' + get_data_table_tab_html() + '''
    </main>
    
    <!-- Footer -->
    <footer class="dashboard-footer">
        <p>TSM Website Structure Dashboard | Data crawled: {{ timestamp }}</p>
        <p style="margin-top: 8px;">
            Built with Flask, Plotly, and NetworkX | 
            <a href="/api/statistics">API</a> | 
            <a href="#">Documentation</a>
        </p>
    </footer>
{% endblock %}

{% block scripts %}
''' + get_dashboard_javascript() + '''
{% endblock %}
'''
    
    # Insert content into base template
    return base.replace('{% block content %}{% endblock %}', content.split('{% block scripts %}')[0]).replace(
        '{% block scripts %}{% endblock %}',
        '{% block scripts %}' + content.split('{% block scripts %}')[1]
    )


# ---------------------------------------------------------------------------
# Template Dictionary for Easy Access
# ---------------------------------------------------------------------------


def get_all_templates() -> Dict[str, str]:
    """
    Get all templates as a dictionary.
    
    Returns:
        Dictionary mapping template names to template strings.
    """
    return {
        'base': get_base_html_template(),
        'dashboard': get_dashboard_tab_html(),
        'network': get_network_tab_html(),
        'statistics': get_statistics_tab_html(),
        'audit': get_audit_tab_html(),
        'data_table': get_data_table_tab_html(),
        'javascript': get_dashboard_javascript(),
        'complete': get_complete_dashboard_template(),
    }


# ---------------------------------------------------------------------------
# Main (for testing)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("TSM Dashboard Templates Module")
    print("=" * 50)
    print("Available templates:")
    for name in get_all_templates().keys():
        print(f"  - {name}")
    print()
    print("Use get_complete_dashboard_template() for the full dashboard.")

