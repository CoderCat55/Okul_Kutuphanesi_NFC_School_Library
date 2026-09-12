import cv2
import os
import json
import threading
from google import genai
from google.genai import types

# ---- shared camera state ----------------------------------------------
_cap = None
_latest_frame = None
_frame_lock = threading.Lock()
_worker_started = False

def start_camera_worker(device_num=0):
    """Call once at server startup. One thread owns the device; the
    stream and the capture endpoint both just read the latest frame."""
    global _cap, _worker_started
    if _worker_started:
        return
    _cap = cv2.VideoCapture(device_num)
    if not _cap.isOpened():
        raise RuntimeError(f"Camera {device_num} could not be opened")

    def _reader():
        global _latest_frame
        while True:
            ret, frame = _cap.read()
            if ret:
                with _frame_lock:
                    _latest_frame = frame

    threading.Thread(target=_reader, daemon=True).start()
    _worker_started = True

def _get_latest_frame():
    with _frame_lock:
        return None if _latest_frame is None else _latest_frame.copy()

def generate_mjpeg():
    """For the live-feed endpoint (left half of the autobook div)."""
    while True:
        frame = _get_latest_frame()
        if frame is None:
            continue
        ok, buf = cv2.imencode('.jpg', frame)
        if ok:
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n'
                   + buf.tobytes() + b'\r\n')

def get_latest_frame_jpeg():
    """For the capture button — no extra device access needed."""
    frame = _get_latest_frame()
    if frame is None:
        return None
    ok, buf = cv2.imencode('.jpg', frame)
    return buf.tobytes() if ok else None

# ---- Gemini -------------------------------------------------------------
# Set this in your shell / systemd unit / .env — never in source:
#   export GEMINI_API_KEY="your-new-key"
#client = genai.Client()  # reads GEMINI_API_KEY from the environment
import API 
client = genai.Client(api_key=API.apikey)

_PROMPT = (
    'Bu görsel bir kitap kapağı. Sadece şu JSON ile cevap ver, başka hiçbir '
    'şey yazma: {"title": "...", "author": "...", "language": "TR|EN|DE"}'
)

def analyze_book_cover(image_bytes):
    response = client.models.generate_content(
        model="gemini-3.7-flash",  # double-check current name at ai.google.dev/gemini-api/docs/models
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
            _PROMPT,
        ],
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )
    return json.loads(response.text)