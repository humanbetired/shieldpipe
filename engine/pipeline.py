import os
import sys
import uuid
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from database import get_connection
from scanners.secret_scanner     import scan as scan_secrets
from scanners.sast_scanner       import scan as scan_sast
from scanners.dependency_scanner import scan as scan_deps
from scanners.container_scanner  import scan as scan_container
from engine.gate                 import evaluate
from engine.ai_summary           import generate as ai_generate
from notifier.telegram           import send as telegram_send


def run(target_path, project_name=None, image=None):
    scan_id      = str(uuid.uuid4())
    project_name = project_name or os.path.basename(target_path)
    started_at   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"\n{'='*50}")
    print(f"  ShieldPipe Security Scan")
    print(f"  Project : {project_name}")
    print(f"  Scan ID : {scan_id[:8]}")
    print(f"  Target  : {target_path}")
    print(f"{'='*50}\n")

    # ── Run all scanners ─────────────────────────────────────────────────────
    all_findings = []
    all_findings += scan_secrets(target_path)
    all_findings += scan_sast(target_path)
    all_findings += scan_deps(target_path)
    all_findings += scan_container(target_path, image=image)

    # ── Security Gate ────────────────────────────────────────────────────────
    gate = evaluate(all_findings)

    print(f"\n{'='*50}")
    print(f"  SECURITY GATE: {gate['result']}")
    for reason in gate["reasons"]:
        print(f"  - {reason}")
    print(f"{'='*50}\n")

    # ── AI Summary ───────────────────────────────────────────────────────────
    ai_summary = ai_generate(scan_id, project_name, all_findings, gate["result"])

    # ── Save to DB ───────────────────────────────────────────────────────────
    conn = get_connection()

    conn.execute("""
        INSERT INTO scan_history
        (scan_id, project_name, target_path, status, total_critical,
         total_high, total_medium, total_low, gate_result, ai_summary, scanned_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        scan_id, project_name, target_path, "completed",
        gate["counts"]["CRITICAL"], gate["counts"]["HIGH"],
        gate["counts"]["MEDIUM"],   gate["counts"]["LOW"],
        gate["result"], ai_summary, started_at
    ))

    for f in all_findings:
        conn.execute("""
            INSERT INTO scan_findings
            (scan_id, scanner, severity, title, description,
             file_path, line_number, evidence, cve_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            scan_id, f["scanner"], f["severity"], f["title"],
            f.get("description", ""), f.get("file_path", ""),
            f.get("line_number", 0), f.get("evidence", ""),
            f.get("cve_id"), f["created_at"]
        ))

    conn.commit()
    conn.close()

    # ── Telegram Alert ───────────────────────────────────────────────────────
    telegram_send(project_name, scan_id, gate)

    print(f"\n[Pipeline] Scan complete — {len(all_findings)} total findings")
    print(f"[Pipeline] Gate result  : {gate['result']}")
    print(f"[Pipeline] Scan ID      : {scan_id}")

    return {
        "scan_id":      scan_id,
        "project_name": project_name,
        "findings":     all_findings,
        "gate":         gate,
        "ai_summary":   ai_summary,
        "scanned_at":   started_at,
    }