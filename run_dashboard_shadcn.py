"""
Run TSM Dashboard with shadcn/ui Components
============================================

Entry point for the modern shadcn/ui-styled dashboard.
"""

from src.dashboard_shadcn import app

if __name__ == "__main__":
    print("=" * 60)
    print("  TSM Website Structure Dashboard")
    print("  Modern Edition with shadcn/ui Components")
    print("=" * 60)
    print()
    print("  🌐 Dashboard: http://localhost:5000")
    print()
    print("  ✨ Features:")
    print("     • Dark theme with Tailwind CSS")
    print("     • shadcn/ui-inspired components")
    print("     • Interactive Plotly visualizations")
    print("     • Real-time data filtering")
    print("     • Export capabilities")
    print()
    print("=" * 60)
    print("  Press Ctrl+C to stop")
    print()
    
    app.run(debug=True, host="0.0.0.0", port=5000)

