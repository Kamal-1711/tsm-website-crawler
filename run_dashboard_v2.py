"""
Run TSM Website Structure Dashboard v2
======================================

Simple entry point to run the comprehensive dashboard.
"""

from src.dashboard_v2 import app

if __name__ == "__main__":
    print("=" * 60)
    print("TSM Website Structure Dashboard v2")
    print("=" * 60)
    print()
    print("🌐 Dashboard: http://localhost:5000")
    print()
    print("📊 Features:")
    print("   - Interactive Network Visualization")
    print("   - Depth Distribution Charts")
    print("   - Content Analysis Pie Charts")
    print("   - Comprehensive Audit Report")
    print("   - Filterable Data Table")
    print("   - Dark/Light Mode Toggle")
    print()
    print("📡 API Endpoints:")
    print("   - /api/network-data")
    print("   - /api/statistics")
    print("   - /api/audit-summary")
    print("   - /download-report")
    print("   - /download-data")
    print()
    print("=" * 60)
    print("Press Ctrl+C to stop the server")
    print()
    
    app.run(debug=True, host="0.0.0.0", port=5000)

