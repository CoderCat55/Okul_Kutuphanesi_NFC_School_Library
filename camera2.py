import cv2
import os
import json
import threading
import base64
import re
from openai import OpenAI
import time
import numpy as np
import API

# ---- shared camera state ----------------------------------------------
cap = None
#latest_frame = None
#frame_lock = threading.Lock()
#worker_started = False
current_device = None
cap_lock = threading.Lock()

def start_camera_worker(device_num):
    global cap, current_device
    with cap_lock:                          # <-- add
        if cap is not None:
            cap.release()
        cap = cv2.VideoCapture(device_num, cv2.CAP_DSHOW)
        if not cap.isOpened():
            raise RuntimeError(f"Camera {device_num} could not be opened")
        current_device = device_num

def get_frame_jpeg():
    with cap_lock:                          # <-- add
        if cap is None:
            return None
        ret, frame = cap.read()
    # ---- lock released here ----
    if not ret:
        return None
    ok, buf = cv2.imencode('.jpg', frame)
    return buf.tobytes() if ok else None

def stop_camera():
    global cap
    with cap_lock:                          # <-- add
        if cap is not None:
            cap.release()
            cap = None

client = OpenAI(base_url=API.freellm_url, api_key=API.freellm_key, timeout=200)

_PROMPT = (
    'Book cover. Reply ONLY with JSON: '
    '{"title":"...","author":"...","language":"TR|EN|DE"}. '
    'Language = the one visible on the cover, not the original. '
    'If unsure: "TR".'
)

def _parse_json(text):
    # some free models wrap JSON in ```json fences or add extra text
    text = re.sub(r"```(?:json)?", "", text).strip()
    m = re.search(r"\{.*\}", text, re.DOTALL)
    return json.loads(m.group(0) if m else text)

def analyze_book_cover(image_bytes):
    img = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
    h, w = img.shape[:2]
    s = 640 / max(h, w)  #changed from 1024 for faster results
    if s < 1:
        img = cv2.resize(img, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)
    image_bytes = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 75])[1].tobytes() #used to be 85
    #shringked image 
    
    b64 = base64.b64encode(image_bytes).decode()
    try:
        resp = client.chat.completions.create(
            model=API.MODEL,   # your vision profile name; "auto" also works but may pick a text-only model
            temperature=0,
            max_tokens=120, 
            extra_body={"keep_alive": "24h"}, 
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": _PROMPT},
                    {"type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                ],
            }],
        )
    except Exception as e:
        raise RuntimeError(
            f"Ollama'ya bağlanılamadı ({API.freellm_url}). "
            f"'ollama serve' çalışıyor mu? Model '{API.MODEL}' yüklü mü? "
            f"Orijinal hata: {e}"
        ) from e
    return _parse_json(resp.choices[0].message.content)