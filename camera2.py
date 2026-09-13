import cv2
import os
import json
import threading
from google import genai
from google.genai import types
import time
import API

# ---- shared camera state ----------------------------------------------
cap = None
latest_frame = None
frame_lock = threading.Lock()
worker_started = False
current_device = None
cap_lock = threading.Lock()

def start_camera_worker(device_num):
    global cap, worker_started, current_device
    if worker_started and current_device == device_num:
        return
    with cap_lock:
        if cap is not None:
            cap.release()
        cap = cv2.VideoCapture(device_num, cv2.CAP_DSHOW)
        if not cap.isOpened():
            raise RuntimeError(f"Camera {device_num} could not be opened")
        current_device = device_num
    if not worker_started:
        threading.Thread(target=reader, args=(device_num,), daemon=True).start()
        worker_started = True

def reader(device_num):
    global latest_frame, cap
    fail_count = 0
    while True:
        try:
            with cap_lock:
                ret, frame = cap.read()
        except cv2.error:
            ret = False
        if ret:
            fail_count = 0
            with frame_lock:
                latest_frame = frame
        else:
            fail_count += 1
            time.sleep(0.05)
            if fail_count > 30:
                with cap_lock:
                    cap.release()
                    cap = cv2.VideoCapture(current_device, cv2.CAP_DSHOW)
                fail_count = 0
                
def get_latest_frame():
    with frame_lock:
        return None if latest_frame is None else latest_frame.copy()

def generate_mjpeg():
    """For the live-feed endpoint (left half of the autobook div)."""
    while True:
        frame = get_latest_frame()
        if frame is None:
            continue
        ok, buf = cv2.imencode('.jpg', frame)
        if ok:
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n'
                   + buf.tobytes() + b'\r\n')

def get_latest_frame_jpeg():
    """For the capture button — no extra device access needed."""
    frame = get_latest_frame()
    if frame is None:
        return None
    ok, buf = cv2.imencode('.jpg', frame)
    return buf.tobytes() if ok else None

def stop_camera():
    print("stop cameraaa")

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