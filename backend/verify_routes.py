import sys
from main import app

sys.stdout.write("App imported successfully!\n")
sys.stdout.write(f"Total routes: {len(app.routes)}\n")
sys.stdout.write("\nAll registered routes:\n")
for route in app.routes:
    if hasattr(route, 'path') and hasattr(route, 'methods'):
        methods = ', '.join(route.methods)
        sys.stdout.write(f"  {methods:10s} {route.path}\n")
sys.stdout.flush()
