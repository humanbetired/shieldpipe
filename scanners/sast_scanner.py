import subprocess
import json
import os
from datetime import datetime

SEVERITY_MAP = {
    "HIGH":   "HIGH",
    "MEDIUM": "MEDIUM",
    "LOW":    "LOW",
}


def scan(target_path):
    print("[SAST Scanner] Starting...")
    findings = []

    try:
        result = subprocess.run(
            ["bandit", "-r", target_path, "-f", "json", "-q",
             "--exclude", f"{target_path}/venv,{target_path}/.git"],
            capture_output=True, text=True
        )

        output = result.stdout.strip()
        if not output:
            print("[SAST Scanner] No output from Bandit")
            return findings

        data = json.loads(output)

        for issue in data.get("results", []):
            severity = SEVERITY_MAP.get(issue.get("issue_severity", "LOW"), "LOW")
            rel_path = os.path.relpath(issue.get("filename", ""), target_path)

            findings.append({
                "scanner":     "SAST Scanner",
                "severity":    severity,
                "title":       issue.get("test_name", "Unknown"),
                "description": issue.get("issue_text", ""),
                "file_path":   rel_path,
                "line_number": issue.get("line_number", 0),
                "evidence":    issue.get("code", "").strip()[:120],
                "cve_id":      None,
                "created_at":  datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

    except FileNotFoundError:
        print("[SAST Scanner] Bandit not found — skipping")
    except json.JSONDecodeError:
        print("[SAST Scanner] Failed to parse Bandit output — skipping")
    except Exception as e:
        print(f"[SAST Scanner] Error: {e}")

    print(f"[SAST Scanner] Done — {len(findings)} findings")
    return findings