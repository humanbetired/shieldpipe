import subprocess
import json
import os
from datetime import datetime

SEVERITY_MAP = {
    "CRITICAL": "CRITICAL",
    "HIGH":     "HIGH",
    "MEDIUM":   "MEDIUM",
    "LOW":      "LOW",
    "UNKNOWN":  "LOW",
}


def find_dockerfile(target_path):
    """Cari Dockerfile di dalam project"""
    for root, dirs, files in os.walk(target_path):
        dirs[:] = [d for d in dirs if d not in {'venv', '.git', '__pycache__'}]
        for file in files:
            if file == "Dockerfile":
                return os.path.join(root, file)
    return None


def get_image_from_dockerfile(dockerfile_path):
    """Ambil base image dari Dockerfile"""
    try:
        with open(dockerfile_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line.upper().startswith("FROM"):
                    parts = line.split()
                    if len(parts) >= 2:
                        image = parts[1]
                        # Skip ARG variables
                        if not image.startswith("$"):
                            return image
    except Exception:
        pass
    return None


def scan(target_path, image=None):
    print("[Container Scanner] Starting...")
    findings = []

    # Cari image dari Dockerfile kalau tidak dispesifikasi
    if not image:
        dockerfile = find_dockerfile(target_path)
        if dockerfile:
            image = get_image_from_dockerfile(dockerfile)
            if image:
                print(f"[Container Scanner] Found Dockerfile — scanning image: {image}")
            else:
                print("[Container Scanner] Dockerfile found but no valid FROM — using default")
                image = "python:3.10-slim"
        else:
            print("[Container Scanner] No Dockerfile found — scanning default image: python:3.10-slim")
            image = "python:3.10-slim"

    try:
        print(f"[Container Scanner] Scanning {image} (this may take a moment)...")
        result = subprocess.run(
            ["trivy", "image", "--format", "json",
             "--quiet", "--no-progress", image],
            capture_output=True, text=True, timeout=120
        )

        output = result.stdout.strip()
        if not output:
            print("[Container Scanner] No output from Trivy")
            return findings

        data = json.loads(output)
        results = data.get("Results", [])

        for res in results:
            target   = res.get("Target", "")
            vulns    = res.get("Vulnerabilities", []) or []

            for vuln in vulns:
                severity = SEVERITY_MAP.get(vuln.get("Severity", "UNKNOWN"), "LOW")
                cve_id   = vuln.get("VulnerabilityID", "")
                pkg_name = vuln.get("PkgName", "")
                inst_ver = vuln.get("InstalledVersion", "")
                fix_ver  = vuln.get("FixedVersion", "")
                desc     = vuln.get("Description", "")[:300]
                title    = vuln.get("Title", "") or f"{pkg_name} vulnerability"

                findings.append({
                    "scanner":     "Container Scanner",
                    "severity":    severity,
                    "title":       f"{pkg_name} {inst_ver} — {cve_id}",
                    "description": f"{title}. {desc}",
                    "file_path":   f"image:{image} ({target})",
                    "line_number": 0,
                    "evidence":    f"{pkg_name}=={inst_ver} | Fix: {fix_ver or 'N/A'}",
                    "cve_id":      cve_id if cve_id.startswith("CVE-") else None,
                    "created_at":  datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })

        # Limit findings agar tidak overwhelming
        if len(findings) > 50:
            criticals = [f for f in findings if f["severity"] == "CRITICAL"]
            highs     = [f for f in findings if f["severity"] == "HIGH"]
            others    = [f for f in findings if f["severity"] not in ("CRITICAL", "HIGH")]
            findings  = criticals + highs + others[:10]
            print(f"[Container Scanner] Truncated to top {len(findings)} findings")

    except subprocess.TimeoutExpired:
        print("[Container Scanner] Trivy timeout — skipping")
    except FileNotFoundError:
        print("[Container Scanner] Trivy not found — skipping")
    except json.JSONDecodeError:
        print("[Container Scanner] Failed to parse Trivy output — skipping")
    except Exception as e:
        print(f"[Container Scanner] Error: {e}")

    print(f"[Container Scanner] Done — {len(findings)} findings")
    return findings