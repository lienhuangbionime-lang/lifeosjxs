import asyncio
import os
import sys

# Mocking parts of the app for Standalone testing
class MockLogger:
    def info(self, msg): print(f"INFO: {msg}")
    def error(self, msg): print(f"ERROR: {msg}")

logger = MockLogger()

# Add project root to sys.path
sys.path.append(os.getcwd())

async def test_cron():
    from app.core.cron import cron_watcher
    print("Running cron_watcher test... (Press Ctrl+C if it hangs)")
    
    # We will just run the loop for a few seconds
    try:
        await asyncio.wait_for(cron_watcher(), timeout=15)
    except asyncio.TimeoutError:
        print("\nTest timed out (desired behavior - loop is running)")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_cron())
