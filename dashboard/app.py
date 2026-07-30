import threading
import time
import cv2
from flask import Flask, Response, render_template, jsonify

app = Flask(__name__)

# Global state to hold callbacks
_get_frame_cb = None
_get_telemetry_cb = None


@app.route("/")
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
def video_feed():
    return Response(gen_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/api/telemetry")
def telemetry():
    if _get_telemetry_cb:
        data = _get_telemetry_cb()
        return jsonify(data)
    return jsonify({"status": "waiting"})


def run_server():
    # Use Waitress for production-grade serving
    import logging

    logging.getLogger("waitress.queue").setLevel(logging.ERROR)

    print("[Dashboard] Starting web dashboard at http://127.0.0.1:5000 (Waitress WSGI)")
    from waitress import serve

    serve(app, host="0.0.0.0", port=5000, threads=4)


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
