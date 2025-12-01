"""
Flask Application Entry Point
Run the interactive web dashboard for TSM Website Crawler
"""

from src.dashboard import create_flask_app

# Create Flask application
app = create_flask_app()

if __name__ == '__main__':
    # Run: python app.py
    # Visit: http://localhost:5000
    print("=" * 60)
    print("TSM Website Crawler Dashboard")
    print("=" * 60)
    print("\n✓ Starting Flask server...")
    print("📍 Dashboard URL: http://localhost:5000")
    print("📍 Alternative: http://127.0.0.1:5000")
    print("\n⚠️  Press Ctrl+C to stop the server")
    print("=" * 60 + "\n")
    app.run(debug=True, host='127.0.0.1', port=5000, use_reloader=False)

