import cv2
import os
import json
import threading
from google import genai
from google.genai import types
import time

# ---- shared camera state ----------------------------------------------
_cap = None
_latest_frame = None
_frame_lock = threading.Lock()
_worker_started = False
_current_index = 0

def start_camera_worker(device_num):
    """Call once at server startup. One thread owns the device; the
    stream and the capture endpoint both just read the latest frame."""
    global _cap, _worker_started
    if _worker_started:
        return
    _cap = cv2.VideoCapture(device_num, cv2.CAP_DSHOW)  # DSHOW backend avoids the MSMF "can't grab frame" bug on Windows
    _current_index = device_num
    #if not _cap.isOpened():
        #raise RuntimeError(f"Camera {device_num} could not be opened")
    if not _cap.isOpened():
        print(f"[camera] WARNING: camera {device_num} could not be opened — /api/camera routes will fail until it's available")
        return
    
    def _reader():
        global _latest_frame, _cap
        fail_count = 0
        while True:
            ret, frame = _cap.read()
            if ret:
                fail_count = 0
                with _frame_lock:
                    _latest_frame = frame
            else:
                fail_count += 1
                time.sleep(0.05)  # don't spin the CPU / hammer the driver while it's failing
                if fail_count > 30:  # ~1.5s of failures -> device likely dropped, reopen it
                    _cap.release()
                    _cap = cv2.VideoCapture(_current_index, cv2.CAP_DSHOW)
                    fail_count = 0
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
            time.sleep(0.05)
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

def list_cameras(max_check=6):
    """Probe indices 0..max_check and report which ones can actually be opened.
    Names come from pygrabber if installed (pip install pygrabber), else generic labels."""
    names = []
    try:
        from pygrabber.dshow_graph import FilterGraph
        names = FilterGraph().get_input_devices()
    except Exception:
        pass

    cameras = []
    for idx in range(max_check):
        if idx == _current_index:
            # already held open by the reader thread — report it without probing
            cameras.append({'index': idx, 'name': names[idx] if idx < len(names) else f'Kamera {idx}'})
            continue
        cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
        if cap.isOpened():
            cameras.append({'index': idx, 'name': names[idx] if idx < len(names) else f'Kamera {idx}'})
        cap.release()
    return cameras

def get_current_index():
    return _current_index

def switch_camera(new_index):
    global _cap, _current_index
    new_cap = cv2.VideoCapture(new_index, cv2.CAP_DSHOW)
    if not new_cap.isOpened():
        new_cap.release()
        return False
    global _latest_frame
    with _frame_lock:
        old_cap = _cap
        _cap = new_cap
        _current_index = new_index
        _latest_frame = None  # drop stale frame from the old device
    old_cap.release()
    return True

def start_or_switch_camera(index):
    if not _worker_started:
        start_camera_worker(index)
        return _cap is not None and _cap.isOpened()
    return switch_camera(index)