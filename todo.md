erors:

[INFO] Database initialized successfully
[ WARN:0@1.318] global cap.cpp:477 cv::VideoCapture::open VIDEOIO(DSHOW): backend is generally available but can't be used to capture by index
\app.py", line 672, in <module>
    camera2.start_camera_worker(cameranum)   # once, at startup — guard against Flask's
    camera2.py", line 23, in start_camera_worker
    raise RuntimeError(f"Camera {device_num} could not be opened")

I use a usb cam but the thing is it sometimes uses my computers internal cam and sometimes the usb cam even when the code is same
secondly the website doesnt open


do not overcomplicate things but just fix the code. After reviewing code and undertanding how to solve this problem. ell me where to change and what to change specifically 
how this would be implemented to current system , which parts should be changed which parts should be added and where.
You may only write which parts of the code I should change and where changes should be made to save time instead of writing the whole script again.