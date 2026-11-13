"""Launch the same Flask application in a native desktop window using PyWebView."""
import os
import socket
import threading
import time
import webview
from app import app

HOST = "127.0.0.1"
PORT = int(os.environ.get("PORT", "5055"))

def run_server():
    app.run(host=HOST, port=PORT, debug=False, use_reloader=False, threaded=True)

def wait_for_server():
    for _ in range(60):
        try:
            with socket.create_connection((HOST, PORT), timeout=0.2):
                return
        except OSError:
            time.sleep(0.2)
    raise RuntimeError("The local game server did not start.")

if __name__ == "__main__":
    threading.Thread(target=run_server, daemon=True).start()
    wait_for_server()
    webview.create_window(
        "Math Sequence Guessing Game",
        f"http://{HOST}:{PORT}",
        width=1180,
        height=820,
        min_size=(760, 600),
        background_color="#0b1220"
    )
    webview.start()
