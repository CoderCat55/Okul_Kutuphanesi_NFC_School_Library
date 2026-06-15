# Okul Kutuphanesi - NFC-based School Library System

A complete working library system with NFC capability for tracking book checkouts/returns, resource cataloging, and administrative functions.

## 🚀 Features

- Student validation via manual entry or NFC tag scanning
- Book checkout/return tracking with NFC tags
- Resource cataloging (physical and digital)
- Search and filter resources
- Administrative panel for managing resources, students, and system
- Database export/import for easy backup and migration
- Activity logging of all transactions
- Responsive design for mobile/tablet/desktop
- Two user roles: Student (limited) and Admin (full)

## 🛠️ Technology Stack

- **Backend:** Python Flask REST API
- **Database:** SQLite (file-based)
- **Frontend:** HTML/CSS/JS (enhanced with AJAX)
- **NFC Handling:** USB keyboard emulation (NFC reader outputs text)

## 📋 Prerequisites

- Python 3.x
- pip
- NFC USB reader (acting as USB keyboard)

## ⚙️ Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd Okul_Kutuphanesi
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env to set your admin password
   ```

4. Initialize the database (done automatically on first run):
   ```bash
   python app.py
   ```

5. Start the application:
   ```bash
   python app.py
   ```

6. Access the system:
   - Main interface: http://localhost:5000
   - Admin panel: http://localhost:5000/admin.html

## 📁 Project Structure

```
Okul_Kutuphanesi/
├── app.py                  # Main Flask application
├── database.py             # Database service
├── models.py               # Data models
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (admin password)
├── index.html              # Main interface (enhanced)
├── admin.html              # Admin panel (enhanced)
├── stylesheet.css          # Styles (fixed filename)
├── uploads/                # Uploaded digital resources
├── exports/                # Exported database backups
├── services/
│   ├── upload_service.py   # File upload handling
│   └── export_import_service.py # Database export/import
└── tests/
    ├── test_database.py    # Database tests
    ├── test_models.py      # Model tests
    └── test_api.py         # API endpoint tests
```

## 🔐 Security

- Admin panel functions are protected by server-side validation
- Database file should be kept secure and backed up regularly
- File uploads are validated for type and size
- Input sanitization on all API endpoints

## 📱 NFC Usage

The system is designed to work with NFC readers that output text when a tag is scanned (acting as a USB keyboard):

1. **Student Validation:** Student enters their number manually, then clicks "Kitapları Okut"
2. **Book Operations:** After validation, scan book NFC tags to check out/return books
3. The NFC tag ID will appear in the appropriate input field as if typed

## 🧪 Testing

Run the test suite:
```bash
python -m pytest tests/ -v
```

## 📝 License

MIT License