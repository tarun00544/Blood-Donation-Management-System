import sys
import json
import urllib.request
import urllib.parse
import urllib.error
import http.cookiejar
from datetime import date, timedelta

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "http://127.0.0.1:5000"
results = []

def record(check_num, name, passed, details=""):
    status = "[PASS]" if passed else "[FAIL]"
    print(f"{status} Check {check_num}: {name} - {details}")
    results.append({"check": check_num, "name": name, "passed": passed, "details": details})

class HTTPClient:
    def __init__(self):
        self.cj = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cj))

    def request(self, method, path, data=None):
        url = f"{BASE_URL}{path}" if path.startswith("/") else f"{BASE_URL}/{path}"
        headers = {"Accept": "application/json"}
        req_data = None
        if data is not None:
            headers["Content-Type"] = "application/json"
            req_data = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
        try:
            with self.opener.open(req) as response:
                status = response.status
                body = response.read().decode("utf-8")
                try:
                    js = json.loads(body)
                except Exception:
                    js = body
                return status, js
        except urllib.error.HTTPError as err:
            err_body = err.read().decode("utf-8")
            try:
                js = json.loads(err_body)
            except Exception:
                js = err_body
            return err.code, js

print("=" * 60)
print("INSPECTING & TESTING LIVE BLOODCARE APPLICATION")
print(f"Target: {BASE_URL}")
print("=" * 60)

client = HTTPClient()

# Check 1: Homepage & Static Assets Loading
try:
    s_home, b_home = client.request("GET", "/")
    s_idx, b_idx = client.request("GET", "/index.html")
    s_css, _ = client.request("GET", "/css/style.css")
    s_js, _ = client.request("GET", "/js/app.js")
    s_api, _ = client.request("GET", "/js/api.js")
    
    home_ok = all(s == 200 for s in [s_home, s_idx, s_css, s_js, s_api]) and "BLOODCARE" in b_home
    record(1, "Homepage Loading", home_ok, f"HTTP {s_home}, HTML size: {len(b_home)} chars")
except Exception as e:
    record(1, "Homepage Loading", False, str(e))

# Check 2: User Registration
user_client = HTTPClient()
test_email = f"liveuser_{date.today().strftime('%Y%m%d%H%M%S')}@example.com"
test_password = "UserPass@123"
try:
    reg_payload = {
        "name": "Live Verification User",
        "email": test_email,
        "phone": "+919876599999",
        "password": test_password,
        "confirm_password": test_password
    }
    s_reg, b_reg = user_client.request("POST", "/api/auth/register", reg_payload)
    reg_ok = s_reg == 201 and b_reg.get("success") and b_reg.get("data", {}).get("role") == "user"
    record(2, "User Registration", reg_ok, f"HTTP {s_reg}, User ID: {b_reg.get('data', {}).get('user_id')}")
except Exception as e:
    record(2, "User Registration", False, str(e))

# Check 3: User Login
user_session = HTTPClient()
try:
    s_login, b_login = user_session.request("POST", "/api/auth/login", {"email": "user@bloodcare.com", "password": "User@123"})
    login_ok = s_login == 200 and b_login.get("success") and b_login.get("data", {}).get("role") == "user"
    record(3, "User Login", login_ok, f"HTTP {s_login}, logged in as: {b_login.get('data', {}).get('email')}")
except Exception as e:
    record(3, "User Login", False, str(e))

# Check 4: Admin Login
admin_session = HTTPClient()
try:
    s_admin, b_admin = admin_session.request("POST", "/api/auth/admin-login", {"email": "admin@bloodcare.com", "password": "Admin@123"})
    admin_ok = s_admin == 200 and b_admin.get("success") and b_admin.get("data", {}).get("role") == "admin"
    record(4, "Admin Login", admin_ok, f"HTTP {s_admin}, authenticated as: {b_admin.get('data', {}).get('name')}")
except Exception as e:
    record(4, "Admin Login", False, str(e))

# Check 5: User Dashboard
try:
    s_udash, b_udash = user_session.request("GET", "/api/user/dashboard")
    d_u = b_udash.get("data", {}) if isinstance(b_udash, dict) else {}
    udash_ok = s_udash == 200 and "user" in d_u and "blood_availability" in d_u
    record(5, "User Dashboard", udash_ok, f"HTTP {s_udash}, user stats retrieved successfully")
except Exception as e:
    record(5, "User Dashboard", False, str(e))

# Check 6: Admin Dashboard
try:
    s_adash, b_adash = admin_session.request("GET", "/api/dashboard")
    d_a = b_adash.get("data", {}) if isinstance(b_adash, dict) else {}
    adash_ok = s_adash == 200 and d_a.get("total_hospitals", 0) > 0 and "blood_inventory" in d_a
    record(6, "Admin Dashboard", adash_ok, f"HTTP {s_adash}, total blood units in DB: {d_a.get('total_blood_units')}")
except Exception as e:
    record(6, "Admin Dashboard", False, str(e))

# Check 7: All API Integrations
try:
    s_hosp, _ = client.request("GET", "/api/hospitals")
    s_stock, _ = client.request("GET", "/api/blood-stock")
    s_search, _ = client.request("GET", "/api/search-donors?blood_group=A%2B")
    s_notif, _ = user_session.request("GET", "/api/user/notifications")
    s_rep, _ = admin_session.request("GET", "/api/reports/total-stock")
    s_users, _ = admin_session.request("GET", "/api/admin/users")

    all_api_ok = (s_hosp == 200 and s_stock == 200 and s_search == 200 and
                  s_notif == 200 and s_rep == 200 and s_users == 200)
    record(7, "All API Integrations", all_api_ok, "Hospitals, stock, search, notifications, reports, and admin endpoints functioning")
except Exception as e:
    record(7, "All API Integrations", False, str(e))

# Check 8: MySQL CRUD Operations
try:
    # 1. Create hospital
    s_ch, b_ch = admin_session.request("POST", "/api/hospitals", {"name": "CRUD Live Clinic", "location": "Ludhiana East", "contact_person": "Sister Mary"})
    h_id = b_ch.get("data", {}).get("hospital_id")
    # 2. Read hospital
    s_rh, _ = admin_session.request("GET", f"/api/hospitals/{h_id}")
    # 3. Update hospital
    s_uh, _ = admin_session.request("PUT", f"/api/hospitals/{h_id}", {"name": "CRUD Live Hospital Updated", "location": "Ludhiana East"})
    # 4. Delete hospital
    s_dh, _ = admin_session.request("DELETE", f"/api/hospitals/{h_id}")

    crud_ok = (s_ch == 201 and s_rh == 200 and s_uh == 200 and s_dh == 200)
    record(8, "MySQL CRUD Operations", crud_ok, "Hospital CRUD flow (POST 201, GET 200, PUT 200, DELETE 200) verified")
except Exception as e:
    record(8, "MySQL CRUD Operations", False, str(e))

# Check 9: Role-based Authorization
try:
    # A. Normal user accessing admin dashboard -> 403
    s_u_dash, _ = user_session.request("GET", "/api/dashboard")
    # B. Normal user accessing admin users -> 403
    s_u_users, _ = user_session.request("GET", "/api/admin/users")
    # C. Unauthenticated user accessing user profile -> 401
    s_unauth, _ = client.request("GET", "/api/user/profile")
    # D. Normal user issuing blood -> 403
    s_u_issue, _ = user_session.request("POST", "/api/blood-requests/1/issue")

    auth_ok = (s_u_dash == 403 and s_u_users == 403 and s_unauth == 401 and s_u_issue == 403)
    record(9, "Role-based Authorization", auth_ok, 
           f"Admin dashboard blocked (HTTP {s_u_dash}), Admin users blocked (HTTP {s_u_users}), Unauth blocked (HTTP {s_unauth}), Issue blood blocked (HTTP {s_u_issue})")
except Exception as e:
    record(9, "Role-based Authorization", False, str(e))

# Check 10: Blood Request and Inventory Functionality
try:
    # 1. User submits request
    s_sub, b_sub = user_session.request("POST", "/api/user/blood-requests", {
        "blood_group": "B+",
        "units_required": 1,
        "hospital_id": 1,
        "patient_name": "Testing Live Flow Recipient",
        "notes": "Automated live verification test"
    })
    req_id = b_sub.get("data", {}).get("request_id")

    # 2. Admin approves request
    s_app, _ = admin_session.request("PUT", f"/api/blood-requests/{req_id}", {"status": "Approved"})

    # 3. Ensure hospital 1 has stock of B+
    admin_session.request("POST", "/api/blood-stock", {
        "blood_group": "B+",
        "units_available": 10,
        "hospital_id": 1,
        "expiry_date": (date.today() + timedelta(days=25)).isoformat()
    })

    # 4. Admin issues blood
    s_issue, b_issue = admin_session.request("POST", f"/api/blood-requests/{req_id}/issue")
    issue_data = b_issue.get("data", {}) if isinstance(b_issue, dict) else {}

    req_inv_ok = (s_sub == 201 and s_app == 200 and s_issue == 200 and issue_data.get("status") == "Fulfilled")
    record(10, "Blood Request and Inventory Functionality", req_inv_ok,
           f"Request #{req_id} created (201), approved (200), and issued (200, status=Fulfilled)")
except Exception as e:
    record(10, "Blood Request and Inventory Functionality", False, str(e))

print("=" * 60)
all_passed = all(r["passed"] for r in results)
print(f"OVERALL INSPECTION RESULT: {'ALL 10 CHECKS PASSED PERFECTLY' if all_passed else 'SOME CHECKS FAILED'}")
print("=" * 60)
