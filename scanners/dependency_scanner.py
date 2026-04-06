import subprocess
import json
import os
import re
from datetime import datetime


def find_requirements(target_path):
    """Cari semua requirements.txt di dalam project"""
    req_files = []
    for root, dirs, files in os.walk(target_path):
        dirs[:] = [d for d in dirs if d not in {'venv', '.git', '__pycache__', 'node_modules'}]
        for file in files:
            if file == "requirements.txt":
                req_files.append(os.path.join(root, file))
    return req_files


def scan(target_path):
    print("[Dependency Scanner] Starting...")
    findings = []

    req_files = find_requirements(target_path)
    if not req_files:
        print("[Dependency Scanner] No requirements.txt found — skipping")
        return findings

    for req_file in req_files:
        rel_path = os.path.relpath(req_file, target_path)
        print(f"[Dependency Scanner] Scanning {rel_path}...")

        try:
            result = subprocess.run(
                ["pip-audit", "-r", req_file, "-f", "json", "--no-deps"],
                capture_output=True, text=True
            )

            output = result.stdout.strip()
            if not output:
                continue

            data = json.loads(output)
            dependencies = data.get("dependencies", [])

            for dep in dependencies:
                pkg_name  = dep.get("name", "Unknown")
                installed = dep.get("version", "")
                vulns     = dep.get("vulns", [])

                for vuln in vulns:
                    vuln_id     = vuln.get("id", "")
                    description = vuln.get("description", "")
                    fix_version = vuln.get("fix_versions", [])
                    aliases     = vuln.get("aliases", [])
                    cve_id      = next((a for a in aliases if a.startswith("CVE-")), None)

                    desc_lower = description.lower()
                    if any(k in desc_lower for k in ["critical", "remote code", "rce", "arbitrary code"]):
                        severity = "CRITICAL"
                    elif any(k in desc_lower for k in ["high", "denial of service", "privilege", "execute"]):
                        severity = "HIGH"
                    elif any(k in desc_lower for k in ["medium", "moderate", "xss", "csrf"]):
                        severity = "MEDIUM"
                    else:
                        severity = "LOW"

                    fix_str = f"Fix: upgrade to {', '.join(fix_version)}" if fix_version else "No fix available"

                    findings.append({
                        "scanner":     "Dependency Scanner",
                        "severity":    severity,
                        "title":       f"{pkg_name} {installed} — {vuln_id}",
                        "description": f"{description[:300]} | {fix_str}",
                        "file_path":   rel_path,
                        "line_number": 0,
                        "evidence":    f"{pkg_name}=={installed} | CVE: {cve_id or 'N/A'} | {vuln_id}",
                        "cve_id":      cve_id,
                        "created_at":  datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })

        except json.JSONDecodeError as e:
            print(f"[Dependency Scanner] JSON parse error: {e}")
        except FileNotFoundError:
            print("[Dependency Scanner] pip-audit not found — skipping")
        except Exception as e:
            print(f"[Dependency Scanner] Error: {e}")

    print(f"[Dependency Scanner] Done — {len(findings)} findings")
    return findings