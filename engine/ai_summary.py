import os
import anthropic
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")


def generate(scan_id, project_name, findings, gate_result):
    print("[AI Summary] Generating...")

    try:
        # Hitung statistik
        total     = len(findings)
        critical  = sum(1 for f in findings if f["severity"] == "CRITICAL")
        high      = sum(1 for f in findings if f["severity"] == "HIGH")
        medium    = sum(1 for f in findings if f["severity"] == "MEDIUM")
        low       = sum(1 for f in findings if f["severity"] == "LOW")

        # Ambil top findings per scanner
        scanners = {}
        for f in findings:
            s = f["scanner"]
            if s not in scanners:
                scanners[s] = []
            if len(scanners[s]) < 5:
                scanners[s].append(f)

        scanner_summary = ""
        for scanner, items in scanners.items():
            scanner_summary += f"\n{scanner}:\n"
            for item in items:
                scanner_summary += f"  [{item['severity']}] {item['title']}\n"
                if item.get('description'):
                    scanner_summary += f"  -> {item['description'][:100]}\n"

        prompt = f"""
You are a senior DevSecOps engineer reviewing a security scan report.
Write a concise executive summary in English (max 4 paragraphs, no bullet points).
Be direct, professional, and actionable.

PROJECT: {project_name}
SCAN ID: {scan_id}
GATE RESULT: {gate_result}

FINDING SUMMARY:
- Total: {total}
- Critical: {critical}
- High: {high}
- Medium: {medium}
- Low: {low}

TOP FINDINGS PER SCANNER:
{scanner_summary}

Write the executive summary now. Focus on:
1. Overall security posture
2. Most critical issues found
3. Immediate actions required
4. Deployment recommendation
"""

        client  = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        message = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}]
        )

        summary = message.content[0].text
        print("[AI Summary] Done")
        return summary

    except Exception as e:
        print(f"[AI Summary] Error: {e}")
        return f"AI summary unavailable: {str(e)}"