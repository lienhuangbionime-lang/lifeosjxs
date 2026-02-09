
import sys
import os

# Add current directory to sys.path to mimic uvicorn behavior
sys.path.insert(0, os.getcwd())

print("Attempting to import main app...")

try:
    from main import app
    print("SUCCESS: main.app imported successfully.")
except ImportError as e:
    print(f"ERROR: ImportError during startup: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"ERROR: Exception during startup: {e}")
    import traceback
    traceback.print_exc()
