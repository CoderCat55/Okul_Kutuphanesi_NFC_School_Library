# Okul Kutuphanesi Library System Design Specification
**Date:** 2026-06-15  
**Project:** Okul Kutuphanesi - NFC-based School Library System  

## 📋 Overview
A complete working library system with NFC capability for tracking book checkouts/returns, resource cataloging, and administrative functions. Built for a school environment with two user roles: Student and Admin.

## 🏗️ Architecture

### Technology Stack
- **Frontend:** Enhanced existing HTML/CSS/JS with AJAX calls (no framework changes)
- **Backend:** Python Flask REST API
- **Database:** SQLite file-based database
- **NFC Handling:** USB keyboard emulation (NFC reader outputs text when tag scanned)

### Core Principles
- Preserve existing frontend work - enhance with AJAX only
- Simple, maintainable code for users with no backend experience
- Local-first design with easy database portability (copy .db file)
- Role-based access: Student (limited) and Admin (full)

## 🧩 Components

### Frontend Components (Enhanced)
1. **Main Interface (`index.html`)**
   - Student ID input + "Kitapları Okut" button
   - AJAX validation to `/api/student/validate`
   - Dynamic book section shown after validation
   - Search bar with AJAX to `/api/resources/search`
   - Catalog table populated via AJAX
   - All interactions use fetch/AJAX instead of hardcoded data

2. **Admin Panel (`admin.html`)**
   - Load resources via GET `/api/resources`
   - Add physical resource form → POST `/api/resources/physical`
   - Add digital resource form + file upload → POST `/api/resources/digital`
   - Student list upload → POST `/api/students/upload`
   - Database export → GET `/api/admin/export`
   - Database import → POST `/api/admin/import`
   - Activity log via GET `/api/activity`

### Backend Components (Flask REST API)
**API Endpoints:**
- **Auth:** POST `/api/login` (admin password check)
- **Students:** 
  - POST `/api/student/validate` (check student number)
  - POST `/api/students/upload` (process CSV/XLSX)
- **Resources:**
  - GET `/api/resources` (list with filtering)
  - GET `/api/resources/search` (search by name/tags)
  - POST `/api/resources/physical` (add physical book)
  - POST `/api/resources/digital` (add digital resource + file)
- **Transactions:**
  - POST `/api/transactions/checkout` (checkout book)
  - POST `/api/transactions/return` (return book)
  - GET `/api/transactions` (history)
- **Admin:**
  - GET `/api/admin/export` (SQLite dump download)
  - POST `/api/admin/import` (restore database)
  - GET `/api/activity` (recent actions)

**Services:**
- Database service (SQLite CRUD operations)
- NFC service (placeholder for future enhancement)
- File upload service (student lists, digital resources)
- Export/import service (database backup/restore)

### Database Schema (SQLite)
**Students Table:**
- `id` INTEGER PRIMARY KEY
- `student_number` TEXT UNIQUE
- `name` TEXT
- `class` TEXT
- `created_at` TIMESTAMP

**Resources Table:**
- `id` INTEGER PRIMARY KEY
- `uuid` TEXT UNIQUE
- `title` TEXT
- `author` TEXT
- `language` TEXT
- `shelf_location` TEXT
- `resource_type` TEXT ('physical'|'digital')
- `tags` TEXT (comma-separated)
- `file_path` TEXT NULLABLE (for digital resources)
- `created_at` TIMESTAMP
- `is_available` BOOLEAN DEFAULT 1

**Transactions Table:**
- `id` INTEGER PRIMARY KEY
- `student_id` INTEGER (FK to students.id)
- `resource_id` INTEGER (FK to resources.id)
- `transaction_type` TEXT ('checkout'|'return')
- `timestamp` TIMESTAMP
- `notes` TEXT

**Activity Log Table:**
- `id` INTEGER PRIMARY KEY
- `action` TEXT
- `details` TEXT
- `timestamp` TIMESTAMP

## 🔄 Data Flow

### Student Validation
1. Student enters ID manually, clicks "Kitapları Okut"
2. Frontend → POST `/api/student/validate` with student_number
3. Backend validates against students table
4. Frontend shows greeting, enables book section, shows flow arrow

### Book Checkout/Return
1. After validation, system ready for book operations
2. For checkout: Student scans book tag (NFC outputs ID), clicks "Çıkış Yap"
3. Frontend → POST `/api/transactions/checkout` with student_id + resource_id
4. Backend:
   - Validates student access
   - Checks resource availability
   - Creates checkout transaction
   - Sets resource.is_available = false
   - Logs activity
5. Frontend shows success by giving an alert text stating book has been chechkedout/returned by studentname, resets form
6. Return flow similar but with return endpoint

### Resource Search
1. User types search term, clicks "Ara" or Enter
2. Frontend → GET `/api/resources/search?q=term`
3. Backend searches title/author/tags
4. Returns matching resources as JSON
5. Frontend populates catalog table with results
6. Users can filter the tags to see resources corresponding to it without clicking on "Ara" or Enter

### Admin Operations
- **Add Resource:** Form submission → POST to appropriate endpoint
- **Upload Students:** File → POST `/api/students/upload` (parses CSV/XLSX)
- **Export DB:** Button → GET `/api/admin/export` (downloads .db file)
- **Import DB:** File → POST `/api/admin/import` (replaces current db)
- **Activity Log:** Page load → GET `/api/activity`

### NFC Handling
- NFC reader acts as USB keyboard
- When tag scanned, outputs the tag ID as text (like typing)
- System focuses appropriate input when ready for scanning
- Student enters their number manually (as requested)
- For book operations, system waits for NFC scan after validation
- No complex Web NFC API needed - leverages keyboard emulation

## ⚙️ Configuration & Setup
1. **Prerequisites:** Python 3.x, pip
2. **Setup:**
   ```bash
   pip install flask
   ```
3. **Run:**
   ```bash
   python app.py
   ```
4. **Access:** http://localhost:5000
5. **Database:** `library.db` file in project root
6. **Uploads:** `uploads/` folder for digital resources
7. **Admin Password:** Configured in `.env` or config file (default: secure random)

## ✅ Success Criteria
- System handles 1000+ resources efficiently
- Database exports as single .db file for easy migration
- NFC scanning works via keyboard emulation (no drivers needed beyond OS)
- Two roles: Student (checkout/return/search) and Admin (full management)
- Responsive design works on mobile/tablet/desktop
- All existing HTML/CSS/JS enhanced, not replaced
- Clear audit trail of all transactions

## 🔒 Security Considerations
- Admin panel protected by password validation
- SQLite database file permissions restrict access
- File uploads validated for type/size  files can be any type and any size
- Input sanitization on all endpoints
- No sensitive data exposed in API responses

## 📝 Future Enhancements (Post-MVP)
- Due date tracking and overdue notifications
- Reservation system for popular books
- Reports/statistics dashboard
- Multi-language support (Turkish/English)
- Barcode/QR code fallback for NFC
- Offline capability with sync