"""Test script to diagnose dashboard issues"""
import sys
import traceback

print("Testing dashboard import and creation...")
print("=" * 50)

try:
    print("1. Importing create_flask_app...")
    from src.dashboard import create_flask_app
    print("   ✓ Import successful")
    
    print("2. Creating Flask app...")
    app = create_flask_app()
    print("   ✓ Flask app created")
    print(f"   Template folder: {app.template_folder}")
    
    print("3. Testing route registration...")
    routes = [str(rule) for rule in app.url_map.iter_rules()]
    print(f"   ✓ Found {len(routes)} routes:")
    for route in routes[:5]:
        print(f"     - {route}")
    
    print("4. Starting test server...")
    print("   Server should start on http://localhost:5000")
    print("   Press Ctrl+C to stop")
    print("=" * 50)
    
    app.run(debug=True, host='127.0.0.1', port=5000, use_reloader=False)
    
except Exception as e:
    print(f"\n✗ ERROR: {e}")
    print("\nFull traceback:")
    traceback.print_exc()
    sys.exit(1)

