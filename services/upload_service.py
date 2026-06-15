import os
import uuid
from werkzeug.utils import secure_filename
from flask import currentapp

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'csv', 'xlsx', 'xls'}
UPLOAD_FOLDER = 'uploads'

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file, folder=None):
    """Save an uploaded file and return the filename"""
    if folder is None:
        folder = UPLOAD_FOLDER

    # Create upload folder if it doesn't exist
    if not os.path.exists(folder):
        os.makedirs(folder)

    if file and allowed_file(file.filename):
        # Generate a unique filename to avoid conflicts
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(folder, unique_filename)
        file.save(file_path)
        return file_path
    else:
        raise ValueError("Invalid file type")