# BLOODCARE — Blood Donation Management System

A production-grade, secure, and modern full-stack Blood Donation Management System featuring **Two Dedicated Role-Based Login Portals** (User Portal and Admin Portal), powered by a unified Python Flask backend, MySQL database, and responsive frontend built strictly with standard HTML5, CSS3, and vanilla JavaScript.

---

## 🌟 Architecture & Features

### 1. Two Separate Role-Based Portals

```
                             BLOODCARE System
                                    |
          +-------------------------+-------------------------+
          |                                                   |
     USER PORTAL                                         ADMIN PORTAL
   (Voluntary Donors & Patients)                       (Hospital Supervisors)
          |                                                   |
  • User Registration                                 • Admin Secure Sign-In
  • Secure User Sign-In                               • Real-time Stats & KPI Cards
  • Personalized Dashboard                            • Interactive Stock & Donor Charts
  • Become a Donor (Status & Eligibility)             • Donor Management (Full CRUD)
  • Search Donors by Group & City                     • Hospital Network Management
  • Blood Availability (Hospital Stock)               • Recipient Registry
  • Submit Blood Requisitions                         • Blood Inventory & Expiry Tracking
  • My Blood Requests (Real-Time Tracker)             • Request Approval & Rejection
  • In-App Notifications                              • Transactional Blood Issue (FIFO)
  • Profile & Password Management                     • Executive Reports & Analytics
                                                      • User Account Administration
```

### 2. Frontend Design & Technology
- **Pure Web Standards**: HTML5, CSS3, and Vanilla JavaScript (Fetch API with `credentials: 'include'`).
- **Strict Compliance**: Zero React, Next.js, Vue, Angular, TypeScript, Bootstrap, Tailwind, or jQuery.
- **Healthcare Theme**:
  - Primary: Crimson Red (`#c62828`, `#8e1b1b`)
  - Secondary: Clean White (`#ffffff`)
  - Background: Crisp Light Grey (`#f8fafc`)
  - Typography: Dark Charcoal (`#0f172a`, `#1e293b`)
  - Accents: Soft Red (`#fee2e2`)
- **Native Visualizations**: Dynamic CSS/SVG bar charts, progress trackers, and real-time status badges without external npm dependencies.

### 3. Backend & Security
- **Backend**: Python 3.14+ with Flask REST API architecture.
- **Security**:
  - Werkzeug password hashing (Scrypt / PBKDF2).
  - Flask session authentication with `HttpOnly` and `SameSite='Lax'` cookies.
  - Role-based access control decorators (`@login_required`, `@admin_required`, `@user_required`).
  - Server-side validation, parameterized MySQL queries preventing SQL injection.
  - Role elevation prevention: public registration restricted exclusively to role `'user'`.
  - Non-negative stock enforcement: database transaction logic guarantees units cannot drop below zero.
  - Strict privacy: normal users can never access or modify other users' records.

---

## 📁 Project Directory Structure

```
Blood-Donation-Management-System/
├── backend/
│   ├── app.py                      # Main Flask application & frontend server
│   ├── config.py                   # Centralized configuration & environment loader
│   ├── database.py                 # MySQL connection pooling & cursor management
│   ├── security.py                 # Role decorators, session checks & password validation
│   ├── utils.py                    # Validation, formatting & JSON response helpers
│   ├── migrate_db.py               # Database migration & table initialization runner
│   ├── backup_db.py                # Database backup script
│   ├── load_sample_data.py         # Sample data loader utility
│   ├── test_workflows.py           # Automated end-to-end verification test suite
│   ├── requirements.txt            # Python dependencies
│   ├── .env                        # Local database & server configurations
│   ├── routes/
│   │   ├── auth_routes.py          # /api/auth/register, /login, /admin-login, /logout, /me
│   │   ├── user_routes.py          # /api/user/profile, /dashboard, /blood-requests, /donor
│   │   ├── admin_routes.py         # /api/admin/users, /api/admin/users/<id>/status
│   │   ├── dashboard_routes.py     # /api/dashboard (Admin aggregated metrics)
│   │   ├── donor_routes.py         # /api/donors, /api/search-donors
│   │   ├── hospital_routes.py      # /api/hospitals (CRUD)
│   │   ├── recipient_routes.py     # /api/recipients (CRUD)
│   │   ├── inventory_routes.py     # /api/blood-stock (Batch CRUD & alerts)
│   │   ├── request_routes.py       # /api/blood-requests, /issue (Transaction)
│   │   └── report_routes.py        # /api/reports/* (Analytics & statistics)
│   ├── services/
│   │   ├── auth_service.py         # Registration, authentication & session service
│   │   ├── user_service.py         # Personal profile, requests & donor service
│   │   ├── donor_service.py        # Donor CRUD & eligibility logic (90-day interval)
│   │   ├── inventory_service.py    # Stock management & expiry categorization
│   │   └── request_service.py      # Request lifecycle & transactional blood issue logic
│   └── sql/
│       ├── schema.sql              # Base database schema
│       ├── sample_data.sql          # Demo hospital, stock & donor dataset
│       ├── auth_migration.sql      # Users table & authentication schema
│       └── backup_before_migration.sql # Automated pre-migration backup
├── frontend/
│   ├── index.html                  # Landing page with live stock & quick donor search
│   ├── user-login.html             # User portal login page
│   ├── admin-login.html            # Protected admin portal login page
│   ├── register.html               # New user registration page
│   ├── user/
│   │   ├── dashboard.html          # User dashboard with personal KPIs & activity
│   │   ├── profile.html            # Profile details & password update
│   │   ├── become-donor.html       # Donor registration & availability status toggle
│   │   ├── find-donors.html        # Donor search & eligibility filters
│   │   ├── blood-availability.html # Live blood stock per hospital
│   │   ├── request-blood.html      # Submit new blood requisition
│   │   └── my-requests.html        # Track personal request statuses
│   ├── admin/
│   │   ├── dashboard.html          # Admin command console with KPI visualizations
│   │   ├── donors.html             # Full donor management (CRUD)
│   │   ├── hospitals.html          # Hospital network management (CRUD)
│   │   ├── recipients.html         # Recipient management (CRUD)
│   │   ├── inventory.html          # Blood batch inventory & expiry alerts
│   │   ├── requests.html           # Requisition approval & transactional blood issue
│   │   ├── reports.html            # Analytics, stock breakdowns & print view
│   │   └── users.html              # System user account administration
│   ├── css/
│   │   ├── style.css               # Core design tokens, typography, buttons, tables, modals
│   │   ├── dashboard.css           # Stat cards, CSS bar charts, badges, alert banners
│   │   ├── landing.css             # Hero, portal selector cards, quick search styles
│   │   └── responsive.css          # Mobile drawer & adaptive breakpoints
│   └── js/
│       ├── api.js                  # Centralized Fetch API client with session credentials
│       ├── auth.js                 # Session guard, role verifier, toast & modal helpers
│       └── app.js                  # Automatic portal layout, navigation & notifications
└── README.md
```

---

## 🛠️ Installation & Setup Instructions

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.14)
- MySQL Server 8.0+ running locally (or remote host)

### 2. Configure Environment (`backend/.env`)
Ensure `backend/.env` contains your MySQL database credentials:
```ini
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=blood_donation_system
DB_PORT=3306

APP_HOST=127.0.0.1
APP_PORT=5000
FLASK_DEBUG=true

SECRET_KEY=bloodcare-super-secret-key-prod-2026-auth
CORS_ORIGINS=http://127.0.0.1:5000,http://localhost:5000,*
LOW_STOCK_THRESHOLD=10
EXPIRING_SOON_DAYS=7
```

### 3. Install Python Dependencies
```bash
pip install -r backend/requirements.txt
```

### 4. Database Setup & Migrations
The database and tables are created and migrated automatically whenever `app.py` runs.
To manually apply migrations or verify demo accounts:
```bash
cd backend
python migrate_db.py
```

---

## 🚀 Running the Application

### Start the Flask Server
From the project root:
```bash
cd backend
python app.py
```
*The server will start at `http://127.0.0.1:5000/`.*

### Access the Application
Open your web browser and navigate to:
- **Landing Page**: [http://127.0.0.1:5000/](http://127.0.0.1:5000/)
- **User Portal**: [http://127.0.0.1:5000/user-login.html](http://127.0.0.1:5000/user-login.html)
- **Admin Portal**: [http://127.0.0.1:5000/admin-login.html](http://127.0.0.1:5000/admin-login.html)

---

## 🔑 Default Credentials

### Administrator Portal
- **URL**: `http://127.0.0.1:5000/admin-login.html`
- **Email**: `admin@bloodcare.com`
- **Password**: `Admin@123`
- *Access*: Full access to manage donors, hospitals, recipients, blood stock, approve/reject requests, issue blood, and view executive reports.

### Standard User / Donor Portal
- **URL**: `http://127.0.0.1:5000/user-login.html`
- **Email**: `user@bloodcare.com`
- **Password**: `User@123`
- *Or register a new account instantly via `http://127.0.0.1:5000/register.html`.*

---

## 🧪 Verification & Test Suite

An automated end-to-end verification suite testing all 17 specified workflows against the live database is included in `backend/test_workflows.py`.

To run the test suite:
```bash
cd backend
python test_workflows.py
```

### Test Coverage Results:
- `TEST 1`: Register a new user (role `'user'`, password hashed) `[PASS]`
- `TEST 2`: Login as user & set session cookie `[PASS]`
- `TEST 3`: Open user dashboard with personal metrics `[PASS]`
- `TEST 4`: Register as voluntary blood donor `[PASS]`
- `TEST 5`: Search donors by blood group & location `[PASS]`
- `TEST 6`: Submit a blood requisition `[PASS]`
- `TEST 7`: View personal blood requests `[PASS]`
- `TEST 8`: Logout user & verify session clearance `[PASS]`
- `TEST 9`: Login as administrator `[PASS]`
- `TEST 10`: Open admin dashboard with real MySQL statistics `[PASS]`
- `TEST 11`: Manage donors, hospitals, and recipients (CRUD) `[PASS]`
- `TEST 12`: Manage blood inventory & stock update `[PASS]`
- `TEST 13`: Approve and reject blood requests `[PASS]`
- `TEST 14`: Issue blood units with FIFO stock deduction & non-negative check `[PASS]`
- `TEST 15`: Access admin endpoints with normal user session (returns HTTP 403 Forbidden) `[PASS]`
- `TEST 16`: Access another user's private records (strictly prevented) `[PASS]`
- `TEST 17`: Session expiration and logout verification (returns HTTP 401 Unauthorized) `[PASS]`
- `TEST 18`: All 27 frontend HTML pages and CSS/JS assets served with HTTP 200 `[PASS]`

---

## 🔒 Security Best Practices Implemented
1. **Zero Plaintext Passwords**: All passwords hashed using Werkzeug Scrypt.
2. **Server-Side Authorization**: Endpoints independently check `session.get('role')`.
3. **Privilege Separation**: Users cannot escalate to `admin`, issue blood, or modify inventory.
4. **Data Isolation**: User queries explicitly filter by `user_id = session['user_id']`.
5. **Database Consistency**: Blood issue operations utilize `SELECT ... FOR UPDATE` row-level locks inside single transactions, deducting oldest valid batches first and aborting if units are insufficient.
