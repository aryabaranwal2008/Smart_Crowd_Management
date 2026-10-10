"""
Smart Crowd Management - Dashboard backend (Flask)

Run:   python app.py
Open:  http://localhost:5000

Two data modes:
  * simulated (default) - generates dummy queue data so the dashboard works today.
  * live                - the moment the backend (Role 2) POSTs real counts to
                          /api/update, the simulator stops and real data is shown.
"""
import random
import threading
import time
from collections import deque
from datetime import datetime

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

# ---- Team-agreed settings (change here once the team fixes them in Week 1) ----
THRESHOLD = 15          # predicted queue above this => warning state
HORIZON_MIN = 5         # predict this many minutes ahead
HISTORY_LEN = 40        # points kept for the graph
TICK_SECONDS = 2        # simulator: 1 tick (2 s) stands for 1 minute of demo time

# Demo scenarios: (average people joining per minute, average people served per minute)
SCENARIOS = {
    "low": (2, 3),
    "normal": (3, 3),
    "busy": (5, 3),
    "surge": (8, 3),
}

lock = threading.Lock()
history = deque(maxlen=HISTORY_LEN)  # each item: {"t", "queue", "entries", "served"}
config = {"mode": "simulated", "scenario": "normal"}


def add_record(queue, entries, served):
    history.append(
        {
            "t": datetime.now().strftime("%H:%M:%S"),
            "queue": int(queue),
            "entries": float(entries),
            "served": float(served),
        }
    )


def simulator():
    """Background thread that fakes a queue until real data arrives."""
    queue = 6
    add_record(queue, 3, 3)
    while True:
        time.sleep(TICK_SECONDS)
        with lock:
            if config["mode"] != "simulated":
                continue
            mean_in, mean_out = SCENARIOS[config["scenario"]]
            entries = max(0, round(random.gauss(mean_in, 1)))
            served = max(0, round(random.gauss(mean_out, 0.8)))
            served = min(served, queue + entries)
            queue = queue + entries - served
            add_record(queue, entries, served)


def analyse():
    """Core prediction logic from the project plan.

    growth    = entry rate - service rate           (people per minute)
    predicted = current queue + growth * minutes
    wait      = current queue / service rate
    """
    recent = list(history)[-3:]  # smooth the rates over the last 3 minutes
    queue = recent[-1]["queue"]
    entry_rate = sum(r["entries"] for r in recent) / len(recent)
    service_rate = sum(r["served"] for r in recent) / len(recent)

    growth = entry_rate - service_rate
    predicted = max(0, queue + growth * HORIZON_MIN)
    wait = round(queue / service_rate, 1) if service_rate > 0 else None
    warning = predicted > THRESHOLD

    if warning:
        recommendation = "Open another counter now."
    elif growth > 0:
        recommendation = "Queue is growing. Keep watching."
    else:
        recommendation = "No action needed."

    return {
        "queue": queue,
        "entry_rate": round(entry_rate, 1),
        "service_rate": round(service_rate, 1),
        "growth": round(growth, 1),
        "predicted": round(predicted, 1),
        "wait_minutes": wait,
        "state": "warning" if warning else "normal",
        "recommendation": recommendation,
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/status")
def status():
    with lock:
        data = analyse()
        data.update(
            {
                "threshold": THRESHOLD,
                "horizon": HORIZON_MIN,
                "history_len": HISTORY_LEN,
                "mode": config["mode"],
                "scenario": config["scenario"],
                "history": [r["queue"] for r in history],
                "updated": history[-1]["t"],
            }
        )
    return jsonify(data)


@app.route("/api/scenario", methods=["POST"])
def set_scenario():
    """Demo buttons on the dashboard use this. Also switches back to simulated mode."""
    name = (request.get_json(silent=True) or {}).get("scenario")
    if name not in SCENARIOS:
        return jsonify({"error": f"scenario must be one of {list(SCENARIOS)}"}), 400
    with lock:
        config["scenario"] = name
        config["mode"] = "simulated"
    return jsonify({"ok": True, "scenario": name})


@app.route("/api/update", methods=["POST"])
def update():
    """Role 2 sends one record per minute here, e.g.:
        requests.post("http://localhost:5000/api/update",
                      json={"entries": 4, "served": 2, "current_count": 10})
    """
    body = request.get_json(silent=True) or {}
    try:
        entries = float(body["entries"])
        served = float(body["served"])
        current = int(body["current_count"])
    except (KeyError, TypeError, ValueError):
        return jsonify({"error": "send numbers: entries, served, current_count"}), 400
    with lock:
        config["mode"] = "live"
        add_record(current, entries, served)
    return jsonify({"ok": True})


if __name__ == "__main__":
    threading.Thread(target=simulator, daemon=True).start()
    # host 0.0.0.0 lets other devices on the same network (phone, teammate) open the page
    app.run(host="0.0.0.0", port=5000, debug=False)
