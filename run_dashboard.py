"""
Simple dashboard runner with clear output
"""
print("=" * 60)
print("TSM Website Crawler - Starting Dashboard")
print("=" * 60)

try:
    from src.dashboard import create_flask_app
    
    print("\n✓ Importing dashboard module...")
    app = create_flask_app()
    print("✓ Flask app created")
    print(f"✓ Template folder: {app.template_folder}")
    print(f"✓ Routes registered: {len(list(app.url_map.iter_rules()))}")
    
    print("\n" + "=" * 60)
    print("🚀 Starting Flask development server...")
    print("=" * 60)
    print("\n📍 Dashboard URL: http://localhost:5000")
    print("📍 Alternative: http://127.0.0.1:5000")
    print("\n⚠️  Press Ctrl+C to stop the server")
    print("=" * 60 + "\n")
    
    app.run(debug=True, host='127.0.0.1', port=5000, use_reloader=False)
    
except KeyboardInterrupt:
    print("\n\n✓ Server stopped by user")
except Exception as e:
    print(f"\n✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
    input("\nPress Enter to exit...")

