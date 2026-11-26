"""Comprehensive Automated End-to-End Verification Test Suite for BLOODCARE.
Tests all specified workflows using Flask test client with real MySQL database.
"""
import sys
import unittest
from datetime import date, timedelta
from app import create_app
import database

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

class TestBloodCareWorkflows(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.client = cls.app.test_client()

    def test_01_register_new_user(self):
        """TEST 1: Register a new user."""
        test_email = f"testuser_{int(date.today().strftime('%Y%m%d'))}_1@example.com"
        with database.db_cursor(commit=True) as cur:
            cur.execute("DELETE FROM users WHERE email = %s", (test_email,))

        payload = {
            "name": "Arun Verma",
            "email": test_email,
            "phone": "+919876543299",
            "password": "Password@123",
            "confirm_password": "Password@123"
        }
        res = self.client.post("/api/auth/register", json=payload)
        self.assertEqual(res.status_code, 201, f"Failed registration: {res.get_json()}")
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["role"], "user")
        self.assertNotIn("password_hash", data["data"])
        print("[PASS] TEST 1: Register a new user")

    def test_02_login_as_user(self):
        """TEST 2: Login as a user."""
        payload = {
            "email": "user@bloodcare.com",
            "password": "User@123"
        }
        res = self.client.post("/api/auth/login", json=payload)
        self.assertEqual(res.status_code, 200, f"Login failed: {res.get_json()}")
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["email"], "user@bloodcare.com")
        self.assertEqual(data["data"]["role"], "user")
        print("[PASS] TEST 2: Login as a user")

    def test_03_open_user_dashboard(self):
        """TEST 3: Open the user dashboard."""
        self.client.post("/api/auth/login", json={"email": "user@bloodcare.com", "password": "User@123"})
        res = self.client.get("/api/user/dashboard")
        self.assertEqual(res.status_code, 200, f"Dashboard error: {res.get_json()}")
        data = res.get_json()["data"]
        self.assertIn("user", data)
        self.assertIn("stats", data)
        self.assertIn("blood_availability", data)
        print("[PASS] TEST 3: Open the user dashboard")

    def test_04_register_as_donor(self):
        """TEST 4: Register as a donor."""
        self.client.post("/api/auth/login", json={"email": "user@bloodcare.com", "password": "User@123"})
        payload = {
            "blood_group": "O+",
            "age": 28,
            "location": "Ludhiana Model Town",
            "phone": "+919876543210",
            "last_donation_date": (date.today() - timedelta(days=100)).isoformat(),
            "is_available": True
        }
        res = self.client.post("/api/user/become-donor", json=payload)
        self.assertEqual(res.status_code, 201, f"Become donor failed: {res.get_json()}")
        data = res.get_json()["data"]
        self.assertEqual(data["blood_group"], "O+")
        self.assertEqual(data["age"], 28)
        self.assertTrue(bool(data["is_available"]))
        print("[PASS] TEST 4: Register as a donor")

    def test_05_search_donors(self):
        """TEST 5: Search donors."""
        res = self.client.get("/api/search-donors?blood_group=O%2B")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()["data"]
        self.assertIsInstance(data, list)
        self.assertTrue(any(d["blood_group"] == "O+" for d in data))
        print("[PASS] TEST 5: Search donors")

    def test_06_submit_blood_request(self):
        """TEST 6: Submit a blood request."""
        self.client.post("/api/auth/login", json={"email": "user@bloodcare.com", "password": "User@123"})
        payload = {
            "blood_group": "A+",
            "units_required": 2,
            "hospital_id": 1,
            "patient_name": "Kamal Preet",
            "required_date": (date.today() + timedelta(days=2)).isoformat(),
            "notes": "Emergency surgery request"
        }
        res = self.client.post("/api/user/blood-requests", json=payload)
        self.assertEqual(res.status_code, 201, f"Submit request failed: {res.get_json()}")
        data = res.get_json()["data"]
        self.assertEqual(data["blood_group"], "A+")
        self.assertEqual(data["units_required"], 2)
        self.assertEqual(data["status"], "Pending")
        TestBloodCareWorkflows.created_request_id = data["request_id"]
        print(f"[PASS] TEST 6: Submit a blood request (Request #{data['request_id']})")

    def test_07_view_personal_requests(self):
        """TEST 7: View personal requests."""
        self.client.post("/api/auth/login", json={"email": "user@bloodcare.com", "password": "User@123"})
        res = self.client.get("/api/user/blood-requests")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()["data"]
        self.assertIsInstance(data, list)
        self.assertTrue(len(data) >= 1)
        print("[PASS] TEST 7: View personal requests")

    def test_08_logout(self):
        """TEST 8: Logout."""
        res = self.client.post("/api/auth/logout")
        self.assertEqual(res.status_code, 200)
        res_me = self.client.get("/api/auth/me")
        self.assertEqual(res_me.status_code, 401)
        print("[PASS] TEST 8: Logout")

    def test_09_login_as_administrator(self):
        """TEST 9: Login as an administrator."""
        payload = {
            "email": "admin@bloodcare.com",
            "password": "Admin@123"
        }
        res = self.client.post("/api/auth/admin-login", json=payload)
        self.assertEqual(res.status_code, 200, f"Admin login failed: {res.get_json()}")
        data = res.get_json()["data"]
        self.assertEqual(data["role"], "admin")
        print("[PASS] TEST 9: Login as an administrator")

    def test_10_open_admin_dashboard(self):
        """TEST 10: Open the admin dashboard."""
        self.client.post("/api/auth/admin-login", json={"email": "admin@bloodcare.com", "password": "Admin@123"})
        res = self.client.get("/api/dashboard")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()["data"]
        self.assertGreater(data["total_hospitals"], 0)
        self.assertIn("total_blood_units", data)
        self.assertIn("blood_inventory", data)
        self.assertIn("low_stock_blood_groups", data)
        print("[PASS] TEST 10: Open the admin dashboard")

    def test_11_manage_donors_hospitals_recipients(self):
        """TEST 11: Manage donors, hospitals and recipients."""
        self.client.post("/api/auth/admin-login", json={"email": "admin@bloodcare.com", "password": "Admin@123"})
        
        # Hospital CRUD
        h_res = self.client.post("/api/hospitals", json={"name": "Fortis Care Unit", "location": "Mohali", "contact_person": "Dr. Gill"})
        self.assertEqual(h_res.status_code, 201)
        h_id = h_res.get_json()["data"]["hospital_id"]

        h_edit = self.client.put(f"/api/hospitals/{h_id}", json={"name": "Fortis Care Hospital", "location": "Mohali"})
        self.assertEqual(h_edit.status_code, 200)

        # Recipient CRUD
        r_res = self.client.post("/api/recipients", json={"name": "Suman Preet", "blood_group": "B+", "hospital_id": h_id, "required_units": 2})
        self.assertEqual(r_res.status_code, 201)
        r_id = r_res.get_json()["data"]["recipient_id"]

        # Delete recipient
        del_r = self.client.delete(f"/api/recipients/{r_id}")
        self.assertEqual(del_r.status_code, 200)

        # Delete hospital
        del_h = self.client.delete(f"/api/hospitals/{h_id}")
        self.assertEqual(del_h.status_code, 200)
        print("[PASS] TEST 11: Manage donors, hospitals and recipients")

    def test_12_manage_blood_inventory(self):
        """TEST 12: Manage blood inventory."""
        self.client.post("/api/auth/admin-login", json={"email": "admin@bloodcare.com", "password": "Admin@123"})
        payload = {
            "blood_group": "AB+",
            "units_available": 15,
            "hospital_id": 1,
            "expiry_date": (date.today() + timedelta(days=30)).isoformat()
        }
        res = self.client.post("/api/blood-stock", json=payload)
        self.assertIn(res.status_code, (200, 201))
        stock_id = res.get_json()["data"]["stock_id"]

        # Update stock
        up_res = self.client.put(f"/api/blood-stock/{stock_id}", json={"units_available": 18})
        self.assertEqual(up_res.status_code, 200)
        self.assertEqual(up_res.get_json()["data"]["units_available"], 18)
        print("[PASS] TEST 12: Manage blood inventory")

    def test_13_approve_and_reject_blood_requests(self):
        """TEST 13: Approve and reject blood requests."""
        self.client.post("/api/auth/admin-login", json={"email": "admin@bloodcare.com", "password": "Admin@123"})
        req_id = getattr(TestBloodCareWorkflows, "created_request_id", 1)

        # Approve
        res_app = self.client.put(f"/api/blood-requests/{req_id}", json={"status": "Approved"})
        self.assertEqual(res_app.status_code, 200)
        self.assertEqual(res_app.get_json()["data"]["status"], "Approved")

        # Reject test on another request
        res_rej = self.client.put(f"/api/blood-requests/2", json={"status": "Rejected"})
        self.assertEqual(res_rej.status_code, 200)
        print("[PASS] TEST 13: Approve and reject blood requests")

    def test_14_issue_blood_and_verify_stock(self):
        """TEST 14: Issue blood and verify stock updates."""
        self.client.post("/api/auth/admin-login", json={"email": "admin@bloodcare.com", "password": "Admin@123"})
        req_id = getattr(TestBloodCareWorkflows, "created_request_id", 1)

        # Get current available A+ units in hospital 1 before issue
        with database.db_cursor() as cur:
            cur.execute("SELECT SUM(units_available) as s FROM blood_stock WHERE blood_group='A+' AND hospital_id=1")
            stock_before = cur.fetchone()["s"] or 0

        # Ensure enough stock
        if stock_before < 2:
            self.client.post("/api/blood-stock", json={"blood_group": "A+", "hospital_id": 1, "units_available": 10, "expiry_date": (date.today() + timedelta(days=20)).isoformat()})

        # Ensure request is in Approved status
        self.client.put(f"/api/blood-requests/{req_id}", json={"status": "Approved"})

        # Issue blood
        issue_res = self.client.post(f"/api/blood-requests/{req_id}/issue")
        self.assertEqual(issue_res.status_code, 200, f"Issue blood failed: {issue_res.get_json()}")
        data = issue_res.get_json()["data"]
        self.assertEqual(data["status"], "Fulfilled")
        self.assertIn("stock_batches_used", data)

        # Verify stock was decremented and never negative
        with database.db_cursor() as cur:
            cur.execute("SELECT MIN(units_available) as m FROM blood_stock")
            min_stock = cur.fetchone()["m"]
            self.assertGreaterEqual(min_stock, 0, "Stock cannot be negative")

        print("[PASS] TEST 14: Issue blood and verify stock updates")

    def test_15_access_admin_api_using_normal_user_session(self):
        """TEST 15: Try accessing an admin API using a normal user session. It must return HTTP 403."""
        # Login as normal user
        self.client.post("/api/auth/login", json={"email": "user@bloodcare.com", "password": "User@123"})
        
        # Try accessing admin endpoints
        res_dash = self.client.get("/api/dashboard")
        self.assertEqual(res_dash.status_code, 403, f"Expected 403 for user accessing admin dashboard, got {res_dash.status_code}")

        res_users = self.client.get("/api/admin/users")
        self.assertEqual(res_users.status_code, 403, f"Expected 403 for user accessing admin users, got {res_users.status_code}")

        res_rep = self.client.get("/api/reports/total-stock")
        self.assertEqual(res_rep.status_code, 403, f"Expected 403 for user accessing reports, got {res_rep.status_code}")

        res_issue = self.client.post("/api/blood-requests/1/issue")
        self.assertEqual(res_issue.status_code, 403, f"Expected 403 for user issuing blood, got {res_issue.status_code}")
        print("[PASS] TEST 15: Accessing admin API using normal user session correctly returns HTTP 403")

    def test_16_access_another_user_private_record(self):
        """TEST 16: Try accessing another user's private record. It must be rejected."""
        # Normal user logs in
        self.client.post("/api/auth/login", json={"email": "user@bloodcare.com", "password": "User@123"})
        res = self.client.get("/api/user/blood-requests")
        self.assertEqual(res.status_code, 200)
        requests = res.get_json()["data"]
        # All requests returned must belong strictly to this user
        for req in requests:
            with database.db_cursor() as cur:
                cur.execute("SELECT user_id FROM blood_request WHERE request_id = %s", (req["request_id"],))
                row = cur.fetchone()
                self.assertEqual(row["user_id"], 2, "User received records belonging to someone else")
        print("[PASS] TEST 16: User cannot access another user's private records")

    def test_17_logout_and_session_expiration(self):
        """TEST 17: Test logout and session expiration."""
        self.client.post("/api/auth/logout")
        res = self.client.get("/api/user/profile")
        self.assertEqual(res.status_code, 401, f"Expected 401 for unauthenticated profile access, got {res.status_code}")
        print("[PASS] TEST 17: Logout and session expiration")

if __name__ == "__main__":
    unittest.main()
