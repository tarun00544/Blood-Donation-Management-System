"""Run once:  python load_sample_data.py   (loads demo hospitals, donors, stock, requests)"""
from database import init_db, load_sample_data

init_db()
if load_sample_data():
    print("Sample data loaded successfully.")
else:
    print("Tables already contain data - nothing was loaded.")
