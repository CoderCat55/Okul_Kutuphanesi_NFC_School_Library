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
from PIL import Image
import pytesseract
#teserract downloader for windows https://github.com/UB-Mannheim/tesseract/wiki
#https://pypi.org/project/pytesseract/

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)
# If you don't have tesseract executable in your PATH, include the following:
#pytesseract.pytesseract.tesseract_cmd = r'<full_path_to_your_tesseract_executable>'
# Example tesseract_cmd = r'C:\Program Files (x86)\Tesseract-OCR\tesseract'


# ---- shared camera state ----------------------------------------------
cap = None
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
    'You are extracting book-cover details from OCR text. '
    'Use only the supplied text. Do not invent missing information. '
    'Return only valid json like this exactly:'
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
    img = cv2.imdecode(
        np.frombuffer(image_bytes, np.uint8),
        cv2.IMREAD_COLOR,
    )
    if img is None:
        raise RuntimeError("Could not decode the camera image.")
    # Keep enough detail for OCR, while limiting very large camera frames.
    height, width = img.shape[:2]
    max_side = 1200
    scale = max_side / max(height, width)
    if scale < 1:
        img = cv2.resize(
            img,
            (int(width * scale), int(height * scale)),
            interpolation=cv2.INTER_AREA,
        )
    # Tesseract works on grayscale text; OpenCV is used here for preprocessing.
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    try:
        ocr_text = pytesseract.image_to_string(
            gray,
            lang="tur+eng+deu",
            config="--oem 3 --psm 11",
        ).strip()
        print("Tesseract OCR:", repr(ocr_text))
    except Exception as e:
        raise RuntimeError(
            "Tesseract OCR failed. Check that Tesseract and the tur, eng, "
            f"and deu language data are installed. Error: {e}"
        ) from e
    if not ocr_text:
        raise RuntimeError(
            "Tesseract could not read text from this cover. "
            "Try adjusting the camera or lighting."
        )
    try:
        response = client.chat.completions.create(
            model=API.MODEL,
            temperature=0,
            max_tokens=120,
            extra_body={"keep_alive": "24h"},
            messages=[
                {
                    "role": "user",
                    "content": f"{_PROMPT}\n\nOCR text:\n{ocr_text}",
                }
            ],
        )
    except Exception as e:
        raise RuntimeError(
            f"Could not reach the text model ({API.MODEL}). "
            f"Check the Ollama service and model. Original error: {e}"
        ) from e
    return _parse_json(response.choices[0].message.content or "")