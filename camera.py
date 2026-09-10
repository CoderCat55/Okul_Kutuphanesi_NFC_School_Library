#https://note.nkmk.me/en/python-opencv-camera-to-still-image/
#https://note.nkmk.me/en/python-opencv-video-to-still-image/
#https://note.nkmk.me/en/python-opencv-videocapture-file-camera/
#https://note.nkmk.me/en/python-opencv-camera-to-still-image/ 

import cv2
import os

def livefeed(device_num,delay=1, window_name='frame'):
  cap = cv2.VideoCapture(device_num)

  if not cap.isOpened():
    return
  
  while True:
    ret, frame = cap.read()
    cv2.imshow(window_name, frame)
    key = cv2.waitKey(delay) & 0xFF
    if key == ord('q'):
      break
  cv2.destroyWindow(window_name)
        
    
def save_frame_camera_key(device_num, dir_path, basename, ext='jpg', delay=1, window_name='frame'):
    cap = cv2.VideoCapture(device_num)

    if not cap.isOpened():
      return

    os.makedirs(dir_path, exist_ok=True)
    base_path = os.path.join(dir_path, basename)
    n = 0
    ret, frame = cap.read()
    cv2.imwrite('{}_{}.{}'.format(base_path, n, ext), frame)



#livefeed(0)

from google import genai

client = genai.Client(api_key="AQ.Ab8RN6LQZcmdhC_Dh0e3XQSq5wjUGg3boH6dTHwrBhwtgVTtPA")

from google import genai

client = genai.Client(api_key="AQ.Ab8RN6LQZcmdhC_Dh0e3XQSq5wjUGg3boH6dTHwrBhwtgVTtPA")

interaction = client.models.generate_content(
  model="models/gemini-3.8-flash",
  contents= " what do you see in this photo"
)
print(interaction)



"""
AQ.Ab8RN6LQZcmdhC_Dh0e3XQSq5wjUGg3boH6dTHwrBhwtgVTtPA

curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent" \
  -H 'Content-Type: application/json' \
  -H 'X-goog-api-key: AQ.Ab8RN6LQZcmdhC_Dh0e3XQSq5wjUGg3boH6dTHwrBhwtgVTtPA' \
  -X POST \
  -d '{
    "contents": [
      {
        "parts": [
          {
            "text": "Explain how AI works in a few words"
          }
        ]
      }
    ]
  }'
"""