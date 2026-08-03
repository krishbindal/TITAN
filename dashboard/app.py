import threading
import time
import cv2
import os
from functools import wraps
from flask import Flask, Response, render_template, jsonify, request

app = Flask(__name__)

# Global state to hold callbacks
_get_frame_cb = None
_get_telemetry_cb = None

# Simple Basic Auth
DASHBOARD_USER = os.environ.get("TITAN_DASHBOARD_USER")
DASHBOARD_PASS = os.environ.get("TITAN_DASHBOARD_PASS")

def check_auth(username, password):
    return username == DASHBOARD_USER and password == DASHBOARD_PASS

def authenticate():
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="TITAN Dashboard"'}
    )

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Skip auth if credentials are not configured
        if not DASHBOARD_USER or not DASHBOARD_PASS:
            return f(*args, **kwargs)
            
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

@app.route("/")
@requires_auth
def index():
    return render_template("index.html")


def gen_frames():
    """Generator for MJPEG streaming."""
    while True:
        if _get_frame_cb:
            frame = _get_frame_cb()
            if frame is not None:
                # Encode frame to JPEG
                ret, buffer = cv2.imencode(
                    ".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80]
                )
                if ret:
                    frame_bytes = buffer.tobytes()
                    yield (
                        b"--frame\r\n"
                        b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
                    )
            else:
                time.sleep(0.1)
        else:
            time.sleep(0.1)


@app.route("/video_feed")
@requires_auth
def video_feed():
    return Response(gen_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/api/telemetry")
@requires_auth
def telemetry():
    if _get_telemetry_cb:
        data = _get_telemetry_cb()
        return jsonify(data)
    return jsonify({"status": "waiting"})


def run_server():
    # Use Waitress for production-grade serving
    import logging

    logging.getLogger("waitress.queue").setLevel(logging.ERROR)
    
    host = os.environ.get("TITAN_DASHBOARD_HOST", "127.0.0.1")
    port = int(os.environ.get("TITAN_DASHBOARD_PORT", 5000))

    if host == "0.0.0.0" and (not DASHBOARD_USER or not DASHBOARD_PASS):
        print("[WARNING] Dashboard is exposed to 0.0.0.0 without authentication!")
        print("          Set TITAN_DASHBOARD_USER and TITAN_DASHBOARD_PASS to secure it.")

    print(f"[Dashboard] Starting web dashboard at http://{host}:{port} (Waitress WSGI)")
    from waitress import serve

    serve(app, host=host, port=port, threads=4)


def start_dashboard(frame_callback, telemetry_callback):
    """
    Start the Flask dashboard in a background thread.
    Pass in callbacks that the dashboard can call to get the latest frame and telemetry.
    """
    global _get_frame_cb, _get_telemetry_cb
    _get_frame_cb = frame_callback
    _get_telemetry_cb = telemetry_callback

    t = threading.Thread(target=run_server, daemon=True)
    t.start()
    return t
