# Blood Donation Management System - Backend

Flask + MySQL REST API for a college RDBMS project. Your HTML/CSS/JS frontend talks to it with `fetch()`.

```
backend/
├── app.py                 # starts Flask, CORS, error handlers
├── config.py              # reads settings from .env
├── database.py            # MySQL connection, transactions, auto-creation of DB + tables
├── utils.py               # JSON responses + input validation
├── load_sample_data.py    # loads demo data (run once)
├── requirements.txt
├── .env.example
├── routes/                # URL endpoints (thin: receive request -> call service -> send JSON)
├── services/              # business rules + SQL (donors, inventory, requests)
└── sql/
    ├── schema.sql         # 5 tables, keys, indexes, constraints
    └── sample_data.sql
```

## 1. Install

You need Python 3.9+ and MySQL 8.0.16+ (CHECK constraints need 8.0.16+).

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # macOS / Linux
pip install -r requirements.txt
```

## 2. Configure MySQL connection

```bash
copy .env.example .env         # Windows
cp .env.example .env           # macOS / Linux
```
Open `.env` and set `DB_PASSWORD` to your MySQL root password. The password lives only in `.env`, never in code.

## 3. Create the database

**Automatic (default):** just run the app. On start-up `init_db()` creates the database `blood_donation_system` and all five tables if they do not exist.

**Manual (optional):** run `sql/schema.sql` in MySQL Workbench, or
`mysql -u root -p < sql/schema.sql`.

Load demo data (once):
```bash
python load_sample_data.py
```

## 4. Run

```bash
python app.py
```
Open http://127.0.0.1:5000/api/health - you should see `"success": true`. If you see a database error, check that MySQL is running and `.env` is correct.

## 5. Connect the frontend

Keep the API address in ONE place in your JavaScript:

```javascript
const API_BASE_URL = "http://127.0.0.1:5000/api";

async function api(path, options = {}) {
  const res = await fetch(API_BASE_URL + path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const json = await res.json();            // always { success, message, data }
  if (!json.success) throw new Error(json.message);
  return json.data;
}

// examples
const dashboard = await api("/dashboard");
const donors    = await api("/donors?blood_group=" + encodeURIComponent("O+"));
await api("/donors", { method: "POST", body: JSON.stringify({ name: "Asha", blood_group: "B+", phone: "9876543210" }) });
await api("/blood-requests/2/issue", { method: "POST" });
```
**Important:** a `+` in a URL means "space". Always use `encodeURIComponent("O+")` (= `O%2B`). The backend also repairs `O+` typed by hand, but encoding is the correct way.

## 6. Response format

```json
{ "success": true,  "message": "Donor added successfully", "data": { } }
{ "success": false, "message": "Donor not found" }
```
Status codes: `200` OK, `201` created, `400` invalid input / rule violation, `404` not found, `409` duplicate email/phone, `500` server/database error.

## 7. API reference

Base URL: `http://127.0.0.1:5000/api`. `PUT` accepts partial bodies (fields you leave out keep their old value).

| Area | Endpoints |
|---|---|
| Dashboard | `GET /dashboard` |
| Donors | `GET /donors` (`?blood_group=` `?search=` `?location=` `?eligible=true`), `GET /donors/<id>`, `POST /donors`, `PUT /donors/<id>`, `DELETE /donors/<id>` |
| Donor search | `GET /search-donors?blood_group=O%2B` (+ optional `&location=` `&eligible=true`) |
| Hospitals | `GET /hospitals` (`?search=`), `POST /hospitals`, `GET/PUT/DELETE /hospitals/<id>` |
| Recipients | `GET /recipients` (`?blood_group=` `?hospital_id=` `?search=`), `POST /recipients`, `GET/PUT/DELETE /recipients/<id>` |
| Blood stock | `GET /blood-stock` (`?blood_group=` `?hospital_id=` `?expiry=expired\|valid\|expiring_soon`), `POST /blood-stock`, `GET/PUT/DELETE /blood-stock/<id>` |
| Blood requests | `GET /blood-requests` (`?status=` `?blood_group=` `?hospital_id=` `?recipient_id=`), `POST /blood-requests`, `GET/PUT/DELETE /blood-requests/<id>` |
| Issue blood | `POST /blood-requests/<id>/issue`  or  `POST /issue-blood` with `{"request_id": 2}` |
| Reports | `GET /reports/donors-by-blood-group`, `/reports/inventory-by-blood-group`, `/reports/hospital-inventory`, `/reports/total-stock`, `/reports/request-statistics`, `/reports/pending-requests`, `/reports/expired-stock` |
| Health | `GET /health` |

**Request bodies**
```json
POST /donors          {"name":"Asha Rao","blood_group":"B+","phone":"9876543210","email":"asha@example.com","location":"Ludhiana","last_donation_date":"2026-08-15"}
POST /hospitals       {"name":"City Care","location":"Ludhiana","contact_person":"Dr. Kumar"}
POST /recipients      {"name":"Ramesh","blood_group":"B+","hospital_id":1,"required_units":2}
POST /blood-stock     {"blood_group":"O+","units_available":10,"expiry_date":"2027-01-30","hospital_id":1}
POST /blood-requests  {"recipient_id":1,"blood_group":"B+","units_required":2,"hospital_id":1}
PUT  /blood-requests/1 {"status":"Approved"}
```
For `POST /blood-requests`, only `recipient_id` is mandatory; blood group, units and hospital default to the recipient's values.

## 8. Test with curl

```bash
curl http://127.0.0.1:5000/api/health
curl http://127.0.0.1:5000/api/dashboard
curl "http://127.0.0.1:5000/api/donors?blood_group=O%2B"
curl "http://127.0.0.1:5000/api/donors?search=Rahul"
curl "http://127.0.0.1:5000/api/search-donors?blood_group=O%2B&location=Ludhiana"
curl "http://127.0.0.1:5000/api/blood-stock?expiry=expired"
curl http://127.0.0.1:5000/api/reports/hospital-inventory

curl -X POST http://127.0.0.1:5000/api/donors -H "Content-Type: application/json" \
  -d '{"name":"Asha Rao","blood_group":"B+","phone":"9876543210","email":"asha@example.com"}'

curl -X PUT http://127.0.0.1:5000/api/donors/1 -H "Content-Type: application/json" -d '{"location":"Jalandhar"}'
curl -X DELETE http://127.0.0.1:5000/api/donors/1

# Issue blood (sample data: request 2 needs 3 units of O- at hospital 2, which has 5)
curl -X POST http://127.0.0.1:5000/api/blood-requests/2/issue
# Request 6 needs 5 units of B- but hospital 2 has only 3 -> 400 "Insufficient stock", nothing changes
curl -X POST http://127.0.0.1:5000/api/blood-requests/6/issue
```
On Windows `cmd`, use double quotes and escape inner quotes (`"{\"name\":\"Asha\"}"`), or test with Postman / Thunder Client.

## 9. Database design (for your viva)

```
HOSPITAL 1 ──< RECIPIENT 1 ──< BLOOD_REQUEST >── 1 HOSPITAL
HOSPITAL 1 ──< BLOOD_STOCK
DONOR (standalone: donors are searched, not linked to a request)
```
* **Primary keys:** `donor_id`, `hospital_id`, `recipient_id`, `stock_id`, `request_id` (AUTO_INCREMENT).
* **Foreign keys:** `recipient.hospital_id`, `blood_stock.hospital_id`, `blood_request.recipient_id`, `blood_request.hospital_id`.
* **ON DELETE rules:** deleting a hospital deletes its stock and requests and sets `recipient.hospital_id` to NULL; deleting a recipient deletes their requests.
* **Integrity:** UNIQUE on donor `email` and `phone`; CHECK constraints for valid blood groups, non-negative stock, positive request units, valid status.
* **Indexes:** donor blood group / name / location, stock (blood group, hospital) and expiry date, request status / blood group / date.
* **Joins used:** recipient + hospital, stock + hospital, request + recipient + hospital (see `services/` and `routes/`).
* **Extra column:** `donor.location` was added (optional) so donors can be searched by city.
* **Design choices:** a stock row is a *batch* (blood group + hospital + expiry). Adding stock with the same group/hospital/expiry increases that batch instead of creating a duplicate row. "Total blood units" on the dashboard counts only non-expired units. A group is "low stock" below `LOW_STOCK_THRESHOLD` (default 10, set in `.env`).

### How blood issue works (transaction)
`services/request_service.py -> issue_blood()` does everything inside one transaction:
1. Lock the request (`SELECT ... FOR UPDATE`); it must be `Pending` or `Approved`.
2. Lock stock batches of the same blood group at that hospital that are **not expired**.
3. If total units < required -> error, nothing is changed.
4. Subtract units, oldest expiry first. The update has `AND units_available >= x`, so stock can never go negative.
5. Set request status to `Fulfilled` and `COMMIT`. Any error -> `ROLLBACK`.

A request can become `Fulfilled` only through the issue endpoint, so stock and request status can never disagree.

## 10. Troubleshooting
* **"Could not connect to the database"** - MySQL is not running, or `DB_USER` / `DB_PASSWORD` in `.env` is wrong.
* **`Access denied for user`** - fix the password in `.env`.
* **CORS error in the browser** - make sure the backend is running and `API_BASE_URL` is correct; set `CORS_ORIGINS` in `.env` if you restricted it.
* **Duplicate sample data** - `load_sample_data.py` refuses to run when tables already contain data.
