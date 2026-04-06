import sys
import os
from flask import Flask, render_template, jsonify, request
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from database import get_connection, init_db

DASHBOARD_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__,
    template_folder=os.path.join(DASHBOARD_DIR, "templates"),
    static_folder=os.path.join(DASHBOARD_DIR, "static")
)


def query(sql, params=()):
    conn = get_connection()
    conn.row_factory = __import__("sqlite3").Row
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def scalar(sql, params=()):
    conn = get_connection()
    r = conn.execute(sql, params).fetchone()
    conn.close()
    return r[0] if r else 0


# ── API: Stats ───────────────────────────────────────────────────────────────

@app.route("/api/stats")
def api_stats():
    return jsonify({
        "total_scans":    scalar("SELECT COUNT(*) FROM scan_history"),
        "total_findings": scalar("SELECT COUNT(*) FROM scan_findings"),
        "blocked":        scalar("SELECT COUNT(*) FROM scan_history WHERE gate_result='BLOCK'"),
        "passed":         scalar("SELECT COUNT(*) FROM scan_history WHERE gate_result='PASS'"),
        "warned":         scalar("SELECT COUNT(*) FROM scan_history WHERE gate_result='WARN'"),
        "critical":       scalar("SELECT COUNT(*) FROM scan_findings WHERE severity='CRITICAL'"),
        "high":           scalar("SELECT COUNT(*) FROM scan_findings WHERE severity='HIGH'"),
    })

@app.route("/api/scans")
def api_scans():
    return jsonify(query("""
        SELECT scan_id, project_name, target_path, status,
               total_critical, total_high, total_medium, total_low,
               gate_result, scanned_at
        FROM scan_history
        ORDER BY scanned_at DESC
        LIMIT 50
    """))

@app.route("/api/scan/<scan_id>")
def api_scan_detail(scan_id):
    scan = query("SELECT * FROM scan_history WHERE scan_id = ?", (scan_id,))
    if not scan:
        return jsonify({"error": "Scan not found"}), 404
    findings = query("""
        SELECT scanner, severity, title, description,
               file_path, line_number, evidence, cve_id
        FROM scan_findings
        WHERE scan_id = ?
        ORDER BY
            CASE severity
                WHEN 'CRITICAL' THEN 1
                WHEN 'HIGH'     THEN 2
                WHEN 'MEDIUM'   THEN 3
                ELSE 4 END
    """, (scan_id,))
    return jsonify({"scan": scan[0], "findings": findings})

@app.route("/api/findings/distribution")
def api_findings_dist():
    return jsonify(query("""
        SELECT scanner, severity, COUNT(*) as count
        FROM scan_findings
        GROUP BY scanner, severity
        ORDER BY scanner, severity
    """))

@app.route("/api/findings/trend")
def api_findings_trend():
    return jsonify(query("""
        SELECT substr(scanned_at, 1, 10) as date,
               SUM(total_critical) as critical,
               SUM(total_high) as high,
               COUNT(*) as scans
        FROM scan_history
        GROUP BY date
        ORDER BY date DESC
        LIMIT 14
    """))

@app.route("/api/findings/top")
def api_top_findings():
    return jsonify(query("""
        SELECT title, severity, scanner, COUNT(*) as count
        FROM scan_findings
        GROUP BY title, severity, scanner
        ORDER BY
            CASE severity
                WHEN 'CRITICAL' THEN 1
                WHEN 'HIGH'     THEN 2
                WHEN 'MEDIUM'   THEN 3
                ELSE 4 END,
            count DESC
        LIMIT 10
    """))

scan_running = {"status": False, "project": ""}

@app.route("/api/run", methods=["POST"])
def api_run_scan():
    import threading
    global scan_running

    if scan_running["status"]:
        return jsonify({"error": "A scan is already running"}), 409

    data   = request.get_json()
    target = data.get("target", "")
    name   = data.get("name", "")
    image  = data.get("image", None)

    if not target or not os.path.exists(target):
        return jsonify({"error": "Invalid target path"}), 400

    def run_scan():
        global scan_running
        scan_running = {"status": True, "project": name or os.path.basename(target)}
        try:
            from engine.pipeline import run
            run(target_path=target, project_name=name or None, image=image or None)
        finally:
            scan_running = {"status": False, "project": ""}

    t = threading.Thread(target=run_scan, daemon=True)
    t.start()
    return jsonify({"message": "Scan started"})


@app.route("/api/scan-status")
def api_scan_status():
    return jsonify(scan_running)


@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    init_db()
    print("[ShieldPipe] Dashboard running at http://127.0.0.1:5002")
    app.run(debug=False, port=5002)