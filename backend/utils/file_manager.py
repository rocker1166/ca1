import os
import time
import threading

TMP_DIR = os.path.join(os.path.dirname(__file__), '..', 'tmp')
os.makedirs(TMP_DIR, exist_ok=True)

# Delete a file after a delay (seconds)
def cleanup_file(path: str, delay: int = 600):
    def _delete():
        time.sleep(delay)
        try:
            os.remove(path)
        except Exception:
            pass
    threading.Thread(target=_delete, daemon=True).start()

def get_download_path(filename: str) -> str:
    return os.path.join(TMP_DIR, filename)
