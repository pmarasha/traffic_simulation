"""
traffic_dashboard_api.py
"""

from flask import Flask, jsonify, request, send_from_directory, Response
from flask_cors import CORS
from pathlib import Path
from datetime import datetime
import csv
import io
import sys
import threading
import time

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

try:
    from run_simulation import run_simulation
    SIM_AVAILABLE = True
except Exception as e:
    print(f"[warn] Could not import run_simulation: {e}")
    SIM_AVAILABLE = False

try:
    from macro_model import run_macro_model
    MACRO_AVAILABLE = True
except Exception as e:
    print(f"[warn] Could not import macro_model: {e}")
    MACRO_AVAILABLE = False


app = Flask(__name__, static_folder=str(BASE_DIR))
CORS(app)

STATE = {
    "live": False,
    "config": {
        "duration": 500,
        "time_step": 1.0,
        "max_queue": 25,
        "tick_delay": 0.7,
        "demand_multiplier": 1.0, # NEW: 1.0 = Baseline, 0.7 = 70% Morning Peak
    },
    "history": [],
    "latest": {},
    "tick": 0,
    "started_at": None,
    "lock": threading.Lock(),
}

MAX_HISTORY = 500


def _live_loop():
    from run_simulation import run_simulation as sim_fn

    cfg = STATE["config"]
    print(f"[info] Generating simulation (duration={cfg['duration']}, demand={cfg['demand_multiplier']})...")
    result = sim_fn(
        duration=cfg["duration"],
        time_step=cfg["time_step"],
        max_queue=cfg["max_queue"],
        demand_multiplier=cfg["demand_multiplier"], # Pass to engine
    )
    history = result["history"]
    print(f"[info] Generated {len(history)} ticks — streaming live...")

    for snap in history:
        if not STATE["live"]:
            break
        STATE["tick"] += 1
        with STATE["lock"]:
            STATE["latest"] = snap
            STATE["history"].append(snap)
            if len(STATE["history"]) > MAX_HISTORY:
                STATE["history"] = STATE["history"][-MAX_HISTORY:]
        time.sleep(cfg["tick_delay"])

    STATE["live"] = False
    print("[info] live stream finished")


@app.route("/")
def index():
    return send_from_directory(BASE_DIR, "dashboard.html")

@app.route("/macro")
def macro_page():
    return send_from_directory(BASE_DIR, "macro_dashboard.html")

@app.route("/api/status")
def status():
    return jsonify({
        "server": "ok",
        "simulation_available": SIM_AVAILABLE,
        "macro_available": MACRO_AVAILABLE,
        "live": STATE["live"],
        "tick": STATE["tick"],
        "started_at": STATE["started_at"],
        "config": STATE["config"],
        "history_points": len(STATE["history"]),
    })

@app.route("/api/metrics")
def metrics():
    return jsonify(STATE["latest"] or {})

@app.route("/api/history")
def history():
    with STATE["lock"]:
        return jsonify(list(STATE["history"]))

@app.route("/api/config", methods=["GET", "POST"])
def config():
    if request.method == "POST":
        incoming = request.get_json(silent=True) or {}
        for k, v in incoming.items():
            if k in STATE["config"]:
                STATE["config"][k] = v
        return jsonify({"ok": True, "config": STATE["config"]})
    return jsonify(STATE["config"])

@app.route("/api/start", methods=["POST"])
def start():
    if STATE["live"]:
        return jsonify({"ok": True, "message": "already running"})

    STATE["live"] = True
    STATE["history"] = []
    STATE["tick"] = 0
    STATE["latest"] = {}
    STATE["started_at"] = datetime.utcnow().isoformat() + "Z"

    threading.Thread(target=_live_loop, daemon=True).start()
    return jsonify({"ok": True, "message": "live simulation started"})

@app.route("/api/stop", methods=["POST"])
def stop():
    STATE["live"] = False
    return jsonify({"ok": True, "message": "live simulation stopped"})

@app.route("/api/export.csv")
def export_csv():
    with STATE["lock"]:
        rows = list(STATE["history"])

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "tick", "time", "vehicles", "congestion", "congestion_level",
        "avg_speed", "throughput", "queue_length", "avg_waiting_time", "demand_multiplier"
    ])
    for r in rows:
        writer.writerow([
            r.get("tick"), r.get("time"), r.get("vehicles"),
            r.get("congestion"), r.get("congestion_level"),
            r.get("avg_speed"), r.get("throughput"),
            r.get("queue_length"), r.get("avg_waiting_time"),
            r.get("demand_multiplier", 1.0)
        ])

    csv_bytes = output.getvalue().encode("utf-8")
    return Response(
        csv_bytes,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=traffic_run_{datetime.utcnow():%Y%m%d_%H%M%S}.csv"},
    )

@app.route("/api/macro")
def macro():
    if not MACRO_AVAILABLE:
        return jsonify({"ok": False, "error": "macro_model.py not importable"}), 503
    try:
        trip_mult = request.args.get("trip_mult", type=float) or 1.0
        peak = request.args.get("peak", type=float)
        gravity = request.args.get("gravity", type=float)
        result = run_macro_model(trip_multiplier=trip_mult, peak_hour_factor=peak, gravity_beta=gravity)
        result["ok"] = True
        return jsonify(result)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


if __name__ == "__main__":
    print("=" * 60)
    print("  ZITRSIE - Harare Digital Twin Baseline")
    print("=" * 60)
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)