from flask import Flask, request, jsonify, send_file, send_from_directory,Response
from database import get_db_connection, init_db
from models import Student, Resource, Transaction
import os
import time
import uuid
import csv
import io
import webbrowser
from threading import Timer
from dotenv import load_dotenv
from export_import_service import export_database, import_database
from upload_service import save_uploaded_file, allowed_file
from werkzeug.utils import secure_filename
import camera2

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)  # For session management if needed

# Initialize the database
with app.app_context():
    try:
        init_db()
        print("[INFO] Database initialized successfully")
    except Exception as e:
        print(f"[ERROR] Failed to initialize database: {e}")
        raise

# Admin login endpoint
@app.route('/api/login', methods=['POST'])
def admin_login():
    data = request.get_json()
    if not data or 'password' not in data:
        return jsonify({'success': False, 'message': 'Password is required'}), 400

    password = data['password']
    admin_password = os.environ.get('ADMIN_PASSWORD', 'yogurt')

    if password == admin_password:
        return jsonify({
            'success': True,
            'message': 'Admin login successful'
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Invalid password'
        }), 401

# Student validation endpoint
@app.route('/api/student/validate', methods=['POST'])
def validate_student():
    data = request.get_json()
    if not data or 'student_number' not in data:
        return jsonify({'success': False, 'message': 'Student number is required'}), 400

    student_number = data['student_number']
    student = Student.find_by_student_number(student_number)

    if student:
        return jsonify({
            'success': True,
            'student': {
                'id': student.id,
                'student_number': student.student_number,
                'name': student.name,
                'class': student.class_name
            }
        })
    else:
        return jsonify({'success': False, 'message': 'Student not found'}), 404

# Resource listing and search endpoints
@app.route('/api/resources', methods=['GET'])
def get_resources():
    # Optional filtering by resource_type
    resource_type = request.args.get('type')
    search_query = request.args.get('q', '').strip()

    with get_db_connection() as conn:
        cursor = conn.cursor()

        if search_query:
            # Search in title, author, or tags
            query = '''
                SELECT * FROM resources
                WHERE (title LIKE ? OR author LIKE ? OR tags LIKE ?)
                AND is_available = 1
            '''
            search_term = f'%{search_query}%'
            cursor.execute(query, (search_term, search_term, search_term))
        elif resource_type:
            cursor.execute('SELECT * FROM resources WHERE resource_type = ? AND is_available = 1', (resource_type,))
        else:
            cursor.execute('SELECT * FROM resources WHERE is_available = 1')

        rows = cursor.fetchall()
        resources = []
        for row in rows:
            resources.append({
                'id': row['id'],
                'uuid': row['uuid'],
                'title': row['title'],
                'author': row['author'],
                'language': row['language'],
                'shelf_location': row['shelf_location'],
                'resource_type': row['resource_type'],
                'tags': row['tags'],
                'file_path': row['file_path'],
                'nfc_tag': row['nfc_tag'],
                'created_at': row['created_at'],
                'is_available': bool(row['is_available'])
            })

        return jsonify({
            'success': True,
            'resources': resources,
            'count': len(resources)
        })

@app.route('/api/resources/<int:resource_id>/download', methods=['GET'])
def download_resource(resource_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM resources WHERE id = ?', (resource_id,))
        resource = cursor.fetchone()

    if not resource:
        return jsonify({'success': False, 'message': 'Resource not found'}), 404

    if resource['resource_type'] != 'digital' or not resource['file_path']:
        return jsonify({'success': False, 'message': 'This resource has no downloadable file'}), 400

    if not os.path.exists(resource['file_path']):
        return jsonify({'success': False, 'message': 'File not found on server'}), 404

    # Keep the original file extension, but use the resource's title as the
    # download name so what the user saves matches what they see in the catalog.
    _, ext = os.path.splitext(resource['file_path'])
    download_name = secure_filename(resource['title'] or 'dosya') + ext

    return send_file(resource['file_path'], as_attachment=True, download_name=download_name)

@app.route('/api/resources/physical', methods=['POST'])
def add_physical_resource():
    data = request.get_json()
    required_fields = ['title', 'author', 'language', 'shelf_location']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({'success': False, 'message': f'{field} is required'}), 400

    # Generate UUID
    resource_uuid = str(uuid.uuid4())

    # Process tags (comma-separated string)
    tags = data.get('tags', '')
    if isinstance(tags, list):
        tags = ','.join(tags)

    # NFC tag (kart numarası) - basılı kaynaklara opsiyonel olarak eklenir
    nfc_tag = (data.get('nfc_tag') or '').strip() or None

    if nfc_tag:
        existing = Resource.find_by_nfc_tag(nfc_tag)
        if existing:
            return jsonify({
                'success': False,
                'message': f'Bu NFC etiketi zaten "{existing.title}" kaynağına kayıtlı'
            }), 400

    with get_db_connection() as conn:
        cursor = conn.cursor()
        for t in [t.strip() for t in tags.split(',') if t.strip()]:
            cursor.execute('INSERT OR IGNORE INTO tags (name) VALUES (?)', (t,))
        cursor.execute(
            '''INSERT INTO resources
               (uuid, title, author, language, shelf_location, resource_type, tags, nfc_tag, is_available)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)''',
            (resource_uuid, data['title'], data['author'], data['language'],
             data['shelf_location'], 'physical', tags, nfc_tag)
        )
        conn.commit()
        resource_id = cursor.lastrowid

        # Log activity
        cursor.execute(
            'INSERT INTO activity_log (action, details) VALUES (?, ?)',
            (f'Added physical resource: {data["title"]}', f'UUID: {resource_uuid}')
        )
        conn.commit()

    return jsonify({
        'success': True,
        'message': 'Physical resource added successfully',
        'resource_id': resource_id,
        'uuid': resource_uuid
    }), 201

@app.route('/api/resources/digital', methods=['POST'])
def add_digital_resource():
    # Check if file is provided
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'}), 400

    # Get form data
    title = request.form.get('title')
    tags = request.form.get('tags', '')
    resource_type = request.form.get('resource_type', 'digital')
    
    try:
        # Save uploaded file
        file_path = save_uploaded_file(file)

        # Generate UUID
        resource_uuid = str(uuid.uuid4())

        # For digital resource, we don't have author, language, shelf_location from form
        author = None
        language = None
        shelf_location = None

        with get_db_connection() as conn:
            cursor = conn.cursor()
            for t in [t.strip() for t in tags.split(',') if t.strip()]:
                cursor.execute('INSERT OR IGNORE INTO tags (name) VALUES (?)', (t,))
            cursor.execute(
                '''INSERT INTO resources
                   (uuid, title, author, language, shelf_location, resource_type, tags, file_path, is_available)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)''',
                (resource_uuid, title, author, language, shelf_location, resource_type, tags, file_path)
            )
            conn.commit()
            resource_id = cursor.lastrowid

            # Log activity
            cursor.execute(
                'INSERT INTO activity_log (action, details) VALUES (?, ?)',
                (f'Added digital resource: {title}')
            )
            conn.commit()

        return jsonify({
            'success': True,
            'message': 'Digital resource added successfully',
            'resource_id': resource_id,
            'uuid': resource_uuid
        }), 201
    except Exception as e:
        return jsonify({'success': False, 'message': f'Failed to add digital resource: {str(e)}'}), 500

#tags api
@app.route('/api/tags', methods=['GET'])
def get_tags():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT name FROM tags ORDER BY name COLLATE NOCASE')
        return jsonify({'success': True, 'tags': [r['name'] for r in cursor.fetchall()]})

@app.route('/api/tags', methods=['POST'])
def add_tag():
    name = (request.get_json() or {}).get('name', '').strip()
    if not name:
        return jsonify({'success': False, 'message': 'Tag name required'}), 400
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO tags (name) VALUES (?)', (name,))
        conn.commit()
    return jsonify({'success': True}), 201

@app.route('/api/tags/<path:name>', methods=['DELETE'])
def delete_tag(name):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM tags WHERE name = ?', (name,))
        conn.commit()
    return jsonify({'success': True})

# Transaction endpoints (Checkout/Return)
@app.route('/api/transactions/checkout', methods=['POST'])
def checkout_resource():
    data = request.get_json()
    if not data or 'student_id' not in data or 'resource_id' not in data:
        return jsonify({'success': False, 'message': 'Student ID and Resource ID are required'}), 400

    student_id = data['student_id']
    resource_id = data['resource_id']

    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Check if student exists
        cursor.execute('SELECT * FROM students WHERE id = ?', (student_id,))
        student = cursor.fetchone()
        if not student:
            return jsonify({'success': False, 'message': 'Student not found'}), 404

        # Check if resource exists and is available
        cursor.execute('SELECT * FROM resources WHERE id = ?', (resource_id,))
        resource = cursor.fetchone()
        if not resource:
            return jsonify({'success': False, 'message': 'Resource not found'}), 404

        if not resource['is_available']:
            return jsonify({'success': False, 'message': 'Resource not available for checkout'}), 400

        # Create transaction
        cursor.execute(
            'INSERT INTO transactions (student_id, resource_id, transaction_type) VALUES (?, ?, ?)',
            (student_id, resource_id, 'checkout')
        )
        # Update resource availability
        cursor.execute('UPDATE resources SET is_available = 0 WHERE id = ?', (resource_id,))
        # Log activity
        cursor.execute(
            'INSERT INTO activity_log (action, details) VALUES (?, ?)',
            (f'Checked out resource: {resource["title"]}', f'To student: {student["student_number"]}')
        )
        conn.commit()
        transaction_id = cursor.lastrowid

    return jsonify({
        'success': True,
        'message': 'Resource checked out successfully',
        'transaction': {
            'id': transaction_id,
            'student_id': student_id,
            'resource_id': resource_id,
            'transaction_type': 'checkout',
            'timestamp': None  # Would be set by database in real implementation
        }
    })

@app.route('/api/transactions/checkout-nfc', methods=['POST'])
def checkout_resource_by_nfc():
    """R20C-USB gibi bir HID NFC kart okuyucusunun okuttuğu kart numarasıyla
    (nfc_tag) doğrudan ödünç alma işlemi yapar. Okuyucu klavye emülasyonu
    yaptığı için frontend tarafında bir input alanına yazılan değer buraya
    POST edilir."""
    data = request.get_json()
    if not data or 'student_id' not in data or 'nfc_tag' not in data:
        return jsonify({'success': False, 'message': 'Student ID and NFC tag are required'}), 400

    student_id = data['student_id']
    nfc_tag = (data['nfc_tag'] or '').strip()
    if not nfc_tag:
        return jsonify({'success': False, 'message': 'NFC tag is required'}), 400

    resource = Resource.find_by_nfc_tag(nfc_tag)
    if not resource:
        return jsonify({'success': False, 'message': 'Bu NFC etiketine kayıtlı bir kaynak bulunamadı'}), 404

    if resource.resource_type != 'physical':
        return jsonify({'success': False, 'message': 'Bu kaynak NFC ile ödünç alınamaz'}), 400

    if not resource.is_available:
        return jsonify({'success': False, 'message': f'"{resource.title}" şu anda ödünç alınmış'}), 400

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM students WHERE id = ?', (student_id,))
        student = cursor.fetchone()
        if not student:
            return jsonify({'success': False, 'message': 'Student not found'}), 404

        cursor.execute(
            'INSERT INTO transactions (student_id, resource_id, transaction_type) VALUES (?, ?, ?)',
            (student_id, resource.id, 'checkout')
        )
        cursor.execute('UPDATE resources SET is_available = 0 WHERE id = ?', (resource.id,))
        cursor.execute(
            'INSERT INTO activity_log (action, details) VALUES (?, ?)',
            (f'Checked out resource (NFC): {resource.title}', f'To student: {student["student_number"]}')
        )
        conn.commit()
        transaction_id = cursor.lastrowid

    return jsonify({
        'success': True,
        'message': 'Resource checked out successfully',
        'transaction': {
            'id': transaction_id,
            'student_id': student_id,
            'resource_id': resource.id,
            'resource_title': resource.title,
            'transaction_type': 'checkout',
            'timestamp': None
        }
    })

@app.route('/api/transactions/return', methods=['POST'])
def return_resource():
    data = request.get_json()
    if not data or 'student_id' not in data or 'resource_id' not in data:
        return jsonify({'success': False, 'message': 'Student ID and Resource ID are required'}), 400

    student_id = data['student_id']
    resource_id = data['resource_id']

    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Check if student exists
        cursor.execute('SELECT * FROM students WHERE id = ?', (student_id,))
        student = cursor.fetchone()
        if not student:
            return jsonify({'success': False, 'message': 'Student not found'}), 404

        # Check if resource exists
        cursor.execute('SELECT * FROM resources WHERE id = ?', (resource_id,))
        resource = cursor.fetchone()
        if not resource:
            return jsonify({'success': False, 'message': 'Resource not found'}), 404

        # Check if resource is currently checked out to this student
        cursor.execute('''
            SELECT t.* FROM transactions t
            WHERE t.student_id = ? AND t.resource_id = ? AND t.transaction_type = 'checkout'
            ORDER BY t.timestamp DESC LIMIT 1
        ''', (student_id, resource_id))
        checkout_transaction = cursor.fetchone()
        if not checkout_transaction:
            return jsonify({'success': False, 'message': 'Resource is not checked out to this student'}), 400

        # Create return transaction
        cursor.execute(
            'INSERT INTO transactions (student_id, resource_id, transaction_type) VALUES (?, ?, ?)',
            (student_id, resource_id, 'return')
        )
        # Update resource availability
        cursor.execute('UPDATE resources SET is_available = 1 WHERE id = ?', (resource_id,))
        # Log activity
        cursor.execute(
            'INSERT INTO activity_log (action, details) VALUES (?, ?)',
            (f'Returned resource: {resource["title"]}', f'From student: {student["student_number"]}')
        )
        conn.commit()
        transaction_id = cursor.lastrowid

    return jsonify({
        'success': True,
        'message': 'Resource returned successfully',
        'transaction': {
            'id': transaction_id,
            'student_id': student_id,
            'resource_id': resource_id,
            'transaction_type': 'return',
            'timestamp': None  # Would be set by database in real implementation
        }
    })

@app.route('/api/transactions', methods=['GET'])
def get_transactions():
    # Optional filtering by student_id
    student_id = request.args.get('student_id')
    limit = request.args.get('limit', 50, type=int)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        if student_id:
            cursor.execute('''
                SELECT t.*, s.student_number, s.name as student_name, r.title as resource_title
                FROM transactions t
                JOIN students s ON t.student_id = s.id
                JOIN resources r ON t.resource_id = r.id
                WHERE t.student_id = ?
                ORDER BY t.timestamp DESC
                LIMIT ?
            ''', (student_id, limit))
        else:
            cursor.execute('''
                SELECT t.*, s.student_number, s.name as student_name, r.title as resource_title
                FROM transactions t
                JOIN students s ON t.student_id = s.id
                JOIN resources r ON t.resource_id = r.id
                ORDER BY t.timestamp DESC
                LIMIT ?
            ''', (limit,))

        rows = cursor.fetchall()
        transactions = []
        for row in rows:
            transactions.append({
                'id': row['id'],
                'student_id': row['student_id'],
                'student_number': row['student_number'],
                'student_name': row['student_name'],
                'resource_id': row['resource_id'],
                'resource_title': row['resource_title'],
                'transaction_type': row['transaction_type'],
                'timestamp': row['timestamp'],
                'notes': row['notes']
            })

        return jsonify({
            'success': True,
            'transactions': transactions,
            'count': len(transactions)
        })

# Admin endpoints
@app.route('/api/admin/export', methods=['GET'])
def export_database_endpoint():
    try:
        # Create exports directory if it doesn't exist
        export_dir = 'exports'
        if not os.path.exists(export_dir):
            os.makedirs(export_dir)

        # Generate export filename with timestamp
        export_path = os.path.join(export_dir, f"library_export_{int(time.time())}.db")
        exported_file = export_database(export_path)

        # Log activity
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO activity_log (action, details) VALUES (?, ?)',
                ('Exported database', f'File: {os.path.basename(exported_file)}')
            )
            conn.commit()

        return send_file(exported_file, as_attachment=True, download_name='library.db')
    except Exception as e:
        return jsonify({'success': False, 'message': f'Export failed: {str(e)}'}), 500

@app.route('/api/admin/import', methods=['POST'])
def import_database_endpoint():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'}), 400

    if not file.filename.endswith('.db'):
        return jsonify({'success': False, 'message': 'Only .db files are allowed for import'}), 400

    try:
        # Save uploaded file temporarily
        temp_path = f"/tmp/{uuid.uuid4()}_{secure_filename(file.filename)}"
        file.save(temp_path)

        # Import the database
        import_database(temp_path)

        # Log activity
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO activity_log (action, details) VALUES (?, ?)',
                ('Imported database', f'File: {file.filename}')
            )
            conn.commit()

        # Clean up temp file
        os.remove(temp_path)

        return jsonify({
            'success': True,
            'message': 'Database imported successfully',
            'note': 'Please restart the application to fully load the imported data'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'Import failed: {str(e)}'}), 500

@app.route('/api/activity', methods=['GET'])
def get_activity_log():
    limit = request.args.get('limit', 50, type=int)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM activity_log
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))

        rows = cursor.fetchall()
        activity = []
        for row in rows:
            activity.append({
                'id': row['id'],
                'action': row['action'],
                'details': row['details'],
                'timestamp': row['timestamp']
            })

        return jsonify({
            'success': True,
            'activity': activity,
            'count': len(activity)
        })

@app.route('/api/students/upload', methods=['POST'])
def upload_students():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'}), 400

    filename_lower = file.filename.lower()
    if not (filename_lower.endswith('.csv') or filename_lower.endswith('.xlsx') or filename_lower.endswith('.xls')):
        return jsonify({'success': False, 'message': 'Only CSV or Excel files are allowed'}), 400

    try:
        # Save uploaded file
        file_path = save_uploaded_file(file)

        rows = read_student_rows(file_path, filename_lower)

        students_added = 0
        students_updated = 0

        for row in rows:
            if len(row) >= 2:  # At least student_number and name
                student_number = _cell_to_str(row[0])
                name = _cell_to_str(row[1])
                class_name = _cell_to_str(row[2]) if len(row) > 2 else ''
                class_name = class_name or None

                if student_number and name:
                    # Check if student already exists
                    existing = Student.find_by_student_number(student_number)
                    if existing:
                        # Update existing student
                        # In a real implementation, you'd have an update method
                        students_updated += 1
                    else:
                        # Create new student
                        Student.create(student_number, name, class_name)
                        students_added += 1

        # Log activity
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO activity_log (action, details) VALUES (?, ?)',
                ('Uploaded student list', f'Added: {students_added}, Updated: {students_updated}')
            )
            conn.commit()

        # Clean up uploaded file (optional - you might want to keep it)
        # os.remove(file_path)

        return jsonify({
            'success': True,
            'message': f'Student list processed successfully',
            'added': students_added,
            'updated': students_updated
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'Upload failed: {str(e)}'}), 500

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/admin.html')
def serve_admin():
    return send_from_directory('.', 'admin.html')

def open_browser():
    webbrowser.open('http://192.168.0.20:5000')

cameranum = 0
if os.environ.get('WERKZEUG_RUN_MAIN') or not app.debug:
    camera2.start_camera_worker(cameranum)

@app.route('/api/camera/list')
def camera_list():
    return jsonify(cameras=camera2.list_cameras(), current=camera2.get_current_index())

@app.route('/api/camera/select', methods=['POST'])
def camera_select():
    idx = int(request.get_json(force=True).get('index', 0))
    ok = camera2.switch_camera(idx)
    return jsonify(success=ok)

@app.route('/api/camera/stream')
def camera_stream():
    return Response(camera2.generate_mjpeg(),
                     mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/camera/capture', methods=['POST'])
def camera_capture():
    jpeg = camera2.get_latest_frame_jpeg()
    if jpeg is None:
        return jsonify(success=False, message='Kamera görüntüsü alınamadı.')
    try:
        return jsonify(success=True, **camera2.analyze_book_cover(jpeg))
    except Exception as e:
        return jsonify(success=False, message=str(e))
    
def detect_text_encoding(path):
    """Find an encoding that can read the whole file without errors.

    Excel/CSV exports made on Turkish-locale Windows are commonly saved as
    windows-1254 or iso-8859-9 rather than UTF-8, which raises
    UnicodeDecodeError if opened with encoding='utf-8'. Try the most likely
    encodings in order; latin-1 is included last as a safety net since it
    can decode any byte sequence (every value 0-255 is a valid code point).
    """
    candidate_encodings = ['utf-8-sig', 'utf-8', 'windows-1254', 'iso-8859-9', 'latin-1']
    for encoding in candidate_encodings:
        try:
            with open(path, 'r', encoding=encoding) as f:
                f.read()
            return encoding
        except (UnicodeDecodeError, UnicodeError):
            continue
    return 'latin-1'


def _cell_to_str(value):
    """Normalize a CSV/Excel cell to a clean string.

    Excel often stores whole-number IDs (e.g. student numbers) as floats
    internally (12345 becomes 12345.0), so this strips a trailing '.0'
    rather than passing it through to the database.
    """
    if value is None:
        return ''
    if isinstance(value, float):
        return str(int(value)) if value.is_integer() else str(value)
    return str(value).strip()


def _rows_have_header(rows, max_sample_rows=5):
    """Detect whether the first row is a header, reusing csv.Sniffer's
    well-tested heuristic for both CSV and Excel data by serializing a
    few rows back to CSV text first.
    """
    if not rows:
        return False
    buf = io.StringIO()
    writer = csv.writer(buf)
    for row in rows[:max_sample_rows]:
        writer.writerow(['' if v is None else v for v in row])
    try:
        return csv.Sniffer().has_header(buf.getvalue())
    except csv.Error:
        return False


def read_csv_rows(file_path):
    """Read all data rows from a CSV file, auto-detecting encoding and
    skipping a header row if one is present."""
    encoding = detect_text_encoding(file_path)
    with open(file_path, 'r', encoding=encoding) as f:
        rows = list(csv.reader(f))
    return rows[1:] if _rows_have_header(rows) else rows


def read_xlsx_rows(file_path):
    """Read all data rows from a modern .xlsx file using openpyxl."""
    try:
        import openpyxl
    except ImportError:
        raise RuntimeError(
            "Reading .xlsx files requires the 'openpyxl' package. "
            "Install it with: pip install openpyxl"
        )

    workbook = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
    try:
        sheet = workbook.active
        rows = [list(r) for r in sheet.iter_rows(values_only=True)]
    finally:
        workbook.close()
    return rows[1:] if _rows_have_header(rows) else rows


def read_xls_rows(file_path):
    """Read all data rows from a legacy .xls file using xlrd."""
    try:
        import xlrd
    except ImportError:
        raise RuntimeError(
            "Reading legacy .xls files requires the 'xlrd' package. "
            "Install it with: pip install xlrd (or re-save the file as .xlsx or .csv)."
        )

    workbook = xlrd.open_workbook(file_path)
    sheet = workbook.sheet_by_index(0)
    rows = [sheet.row_values(i) for i in range(sheet.nrows)]
    return rows[1:] if _rows_have_header(rows) else rows


def read_student_rows(file_path, filename_lower):
    """Dispatch to the right reader based on file extension."""
    if filename_lower.endswith('.csv'):
        return read_csv_rows(file_path)
    elif filename_lower.endswith('.xlsx'):
        return read_xlsx_rows(file_path)
    elif filename_lower.endswith('.xls'):
        return read_xls_rows(file_path)
    raise ValueError('Unsupported file type')

if __name__ == '__main__':
    # debug=True spawns a reloader child process that re-runs this file.
    # WERKZEUG_RUN_MAIN is only set in that child, so checking for its
    # absence here ensures the browser opens exactly once.
    if not os.environ.get('WERKZEUG_RUN_MAIN'):
        Timer(1, open_browser).start()
    app.run(debug=True, host='0.0.0.0', port=5000)