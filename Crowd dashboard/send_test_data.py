"""Pretend to be Role 2: push one record to the dashboard.
Run while app.py is running:  python send_test_data.py
Needs:  pip install requests
"""
import requests

record = {"entries": 4, "served": 2, "current_count": 10}  # the example from the plan
r = requests.post("http://localhost:5000/api/update", json=record)
print(r.status_code, r.json())
