from flask import Flask, request, jsonify, send_file
from database import get_db_connection
from models import Student, Resource, Transaction
import os
import uuid
from dotenv import load_dotenv
from services.export_import_service import export_database, import_database
from services.upload_service import save_uploaded_file, allowed_file

load_dotenv()

app = Flask(__name__)

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
                'created_at': row['created_at'],
                'is_available': bool(row['is_available'])
            })

        return jsonify({
            'success': True,
            'resources': resources,
            'count': len(resources)
        })

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

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT INTO resources
               (uuid, title, author, language, shelf_location, resource_type, tags, is_available)
               VALUES (?, ?, ?, ?, ?, ?, ?, 1)''',
            (resource_uuid, data['title'], data['author'], data['language'],
             data['shelf_location'], 'physical', tags)
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
    # This will be handled with file upload - simplified version for now
    data = request.get_json()
    required_fields = ['title', 'author', 'language', 'file_path']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({'success': False, 'message': f'{field} is required'}), 400

    # Generate UUID
    resource_uuid = str(uuid.uuid4())

    # Process tags
    tags = data.get('tags', '')
    if isinstance(tags, list):
        tags = ','.join(tags)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT INTO resources
               (uuid, title, author, language, shelf_location, resource_type, tags, file_path, is_available)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)''',
            (resource_uuid, data['title'], data['author'], data['language'],
             data.get('shelf_location', ''), 'digital', tags, data['file_path'])
        )
        conn.commit()
        resource_id = cursor.lastrowid

        # Log activity
        cursor.execute(
            'INSERT INTO activity_log (action, details) VALUES (?, ?)',
            (f'Added digital resource: {data["title"]}', f'UUID: {resource_uuid}')
        )
        conn.commit()

    return jsonify({
        'success': True,
        'message': 'Digital resource added successfully',
        'resource_id': resource_id,
        'uuid': resource_uuid
    }), 201

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

        export_path = os.path.join(export_dir, f"library_export_{int(os.time())}.db")
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

    # Check file extension
    if not (file.filename.endswith('.csv') or file.filename.endswith('.xlsx') or file.filename.endswith('.xls')):
        return jsonify({'success': False, 'message': 'Only CSV or Excel files are allowed'}), 400

    try:
        # Save uploaded file
        file_path = save_uploaded_file(file)

        # Process the file (simplified - in reality you'd use pandas or csv module)
        import csv
        students_added = 0
        students_updated = 0

        with open(file_path, 'r', encoding='utf-8') as f:
            # Try to detect if it's CSV with headers
            sample = f.read(1024)
            f.seek(0)
            has_header = csv.Sniffer().has_header(sample)

            reader = csv.reader(f)
            if has_header:
                next(reader)  # Skip header

            for row in reader:
                if len(row) >= 2:  # At least student_number and name
                    student_number = row[0].strip()
                    name = row[1].strip()
                    class_name = row[2].strip() if len(row) > 2 else None

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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)