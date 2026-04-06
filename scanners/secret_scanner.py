import os
import re
from datetime import datetime
import fnmatch


SECRET_PATTERNS = [
    {"name": "Generic API Key",       "pattern": r'(?i)(api[_-]?key|apikey)\s*=\s*["\']([A-Za-z0-9_\-]{16,})["\']',        "severity": "CRITICAL"},
    {"name": "Generic Secret Key",    "pattern": r'(?i)(secret[_-]?key|secretkey)\s*=\s*["\']([A-Za-z0-9_\-]{8,})["\']',   "severity": "CRITICAL"},
    {"name": "Hardcoded Password",    "pattern": r'(?i)(password|passwd|pwd)\s*=\s*["\']([^"\']{4,})["\']',                 "severity": "HIGH"},
    {"name": "Hardcoded Token",       "pattern": r'(?i)(token|access_token|auth_token)\s*=\s*["\']([A-Za-z0-9_\-]{16,})["\']', "severity": "CRITICAL"},
    {"name": "Anthropic API Key",     "pattern": r'sk-ant-[A-Za-z0-9\-_]{20,}',                                             "severity": "CRITICAL"},
    {"name": "OpenAI API Key",        "pattern": r'sk-[A-Za-z0-9]{32,}',                                                    "severity": "CRITICAL"},
    {"name": "Telegram Bot Token",    "pattern": r'\d{8,10}:[A-Za-z0-9_\-]{35}',                                            "severity": "CRITICAL"},
    {"name": "Private Key",           "pattern": r'-----BEGIN (RSA |EC )?PRIVATE KEY-----',                                  "severity": "CRITICAL"},
    {"name": "AWS Access Key",        "pattern": r'AKIA[0-9A-Z]{16}',                                                        "severity": "CRITICAL"},
    {"name": "Database URL",          "pattern": r'(?i)(mysql|postgresql|mongodb|redis):\/\/[^:]+:[^@]+@',                   "severity": "HIGH"},
    {"name": "Basic Auth in URL",     "pattern": r'https?:\/\/[^:]+:[^@]+@',                                                 "severity": "HIGH"},
    {"name": "Hardcoded IP + Port",   "pattern": r'(?i)(host|server|endpoint)\s*=\s*["\'](\d{1,3}\.){3}\d{1,3}:\d+["\']',  "severity": "MEDIUM"},
]

SKIP_EXTENSIONS = {'.pyc', '.png', '.jpg', '.jpeg', '.gif', '.svg',
                   '.ico', '.pdf', '.zip', '.tar', '.gz', '.exe', '.db'}

SKIP_DIRS = {'venv', '.git', '__pycache__', 'node_modules', '.env',
             'dist', 'build', '.idea', '.vscode'}


def load_gitignore(target_path):
    """Baca .gitignore dan return list pattern yang harus diskip"""
    gitignore_path = os.path.join(target_path, ".gitignore")
    patterns = []
    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    patterns.append(line)
    return patterns


def is_ignored(filepath, target_path, patterns):
    """Cek apakah file match dengan pattern .gitignore"""
    rel_path = os.path.relpath(filepath, target_path)
    rel_path = rel_path.replace("\\", "/")

    for pattern in patterns:
        if fnmatch.fnmatch(rel_path, pattern):
            return True
        if fnmatch.fnmatch(os.path.basename(filepath), pattern):
            return True
        if any(fnmatch.fnmatch(part, pattern) for part in rel_path.split("/")):
            return True
    return False

def scan(target_path):
    print("[Secret Scanner] Starting...")
    findings  = []
    gitignore = load_gitignore(target_path)
    skipped   = 0

    for root, dirs, files in os.walk(target_path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in SKIP_EXTENSIONS:
                continue
            if file.startswith('.env'):
                continue

            filepath = os.path.join(root, file)

            if gitignore and is_ignored(filepath, target_path, gitignore):
                skipped += 1
                continue

            rel_path = os.path.relpath(filepath, target_path)

            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()

                for line_num, line in enumerate(lines, 1):
                    for pattern in SECRET_PATTERNS:
                        matches = re.findall(pattern["pattern"], line)
                        if matches:
                            evidence = line.strip()[:120]
                            findings.append({
                                "scanner":     "Secret Scanner",
                                "severity":    pattern["severity"],
                                "title":       pattern["name"],
                                "description": f"Potential hardcoded secret detected: {pattern['name']}",
                                "file_path":   rel_path,
                                "line_number": line_num,
                                "evidence":    evidence,
                                "cve_id":      None,
                                "created_at":  datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            })

            except Exception:
                continue

    print(f"[Secret Scanner] Done — {len(findings)} findings ({skipped} files skipped via .gitignore)")
    return findings