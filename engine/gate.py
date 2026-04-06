RULES = {
    "CRITICAL": {"threshold": 0,  "action": "BLOCK"},
    "HIGH":     {"threshold": 3,  "action": "BLOCK"},
    "MEDIUM":   {"threshold": 10, "action": "WARN"},
    "LOW":      {"threshold": 99, "action": "PASS"},
}


def evaluate(findings):
    counts = {
        "CRITICAL": sum(1 for f in findings if f["severity"] == "CRITICAL"),
        "HIGH":     sum(1 for f in findings if f["severity"] == "HIGH"),
        "MEDIUM":   sum(1 for f in findings if f["severity"] == "MEDIUM"),
        "LOW":      sum(1 for f in findings if f["severity"] == "LOW"),
    }

    result  = "PASS"
    reasons = []

    for severity, rule in RULES.items():
        count = counts[severity]
        if count > rule["threshold"]:
            if rule["action"] == "BLOCK":
                result = "BLOCK"
                reasons.append(f"{count} {severity} finding(s) exceed threshold ({rule['threshold']})")
            elif rule["action"] == "WARN" and result != "BLOCK":
                result = "WARN"
                reasons.append(f"{count} {severity} finding(s) exceed threshold ({rule['threshold']})")

    return {
        "result":  result,
        "counts":  counts,
        "reasons": reasons,
    }