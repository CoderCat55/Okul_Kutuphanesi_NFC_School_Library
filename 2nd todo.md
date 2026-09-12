Fix 3 — stop relying on a fixed index for the USB cam

File: camera2.py, inside start_camera_worker, replace the single hardcoded cv2.VideoCapture(device_num, cv2.CAP_DSHOW) open with a small loop that tries a couple of indices and keeps the first one that actually opens and isn't your laptop's built-in cam:

def _open_camera(preferred_index=0, tries=(0, 1, 2)):
    for idx in tries:
        cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
        if cap.isOpened():
            return cap, idx
        cap.release()
    return None, None

Then in start_camera_worker, call _cap, opened_idx = _open_camera(device_num) instead of the direct cv2.VideoCapture(...) line, and use opened_idx in the reopen logic inside _reader() too.

This won't guarantee which physical camera is "first" (that's a Windows driver-order issue outside your code's control), but it stops hard failures when index 0 briefly belongs to the wrong device — it'll walk to the next index instead of just dying. If you need it to always pick the correct one regardless of order, the reliable route is enumerating devices by name with pygrabber (pip install pygrabber) and matching a substring of your USB cam's product name — let me know if you want that added, it's a few more lines in the same function.