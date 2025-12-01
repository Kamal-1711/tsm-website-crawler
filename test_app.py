"""Quick test to verify app can be created"""
from src.dashboard import create_flask_app

print("Testing Flask app creation...")
try:
    app = create_flask_app()
    print("✓ App created successfully!")
    print(f"✓ Template folder: {app.template_folder}")
    print(f"✓ Routes: {len(list(app.url_map.iter_rules()))}")
    print("\n✓ Ready to run! Use: python run_dashboard.py")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

