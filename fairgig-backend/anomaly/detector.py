from typing import Any, Dict, List

import numpy as np


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _deduction_pct(record: Dict[str, Any]) -> float:
    gross = _to_float(record.get("gross_earned"), 0.0)
    deductions = _to_float(record.get("platform_deductions"), 0.0)
    if gross <= 0:
        return 0.0
    return (deductions / gross) * 100.0


def detect_anomalies(earnings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    anomalies: List[Dict[str, Any]] = []
    if not earnings:
        return anomalies

    ordered = sorted(earnings, key=lambda x: x.get("date", ""))

    deduction_pcts = [_deduction_pct(item) for item in ordered]
    for i in range(1, len(ordered)):
        baseline = deduction_pcts[:i]
        baseline_mean = float(np.mean(baseline))
        baseline_std = float(np.std(baseline))

        # With short or flat history, std can be near zero. A floor keeps z-scores usable.
        if baseline_std < 1.0:
            baseline_std = 1.0

        current_pct = deduction_pcts[i]
        z = (current_pct - baseline_mean) / baseline_std
        if z > 2.0:
            severity = "critical" if z >= 4.0 else "high"
            anomalies.append(
                {
                    "date": ordered[i].get("date"),
                    "platform": ordered[i].get("platform"),
                    "type": "unusual_deduction",
                    "severity": severity,
                    "value": round(z, 2),
                    "explanation": (
                        f"Deductions reached {current_pct:.1f}% of gross earnings, "
                        f"which is {z:.2f} standard deviations above prior shifts."
                    ),
                }
            )

    for i in range(1, len(ordered)):
        prev_net = _to_float(ordered[i - 1].get("net_received"), 0.0)
        curr_net = _to_float(ordered[i].get("net_received"), 0.0)

        if prev_net <= 0:
            continue

        drop_pct = ((prev_net - curr_net) / prev_net) * 100.0
        if drop_pct > 20.0:
            if drop_pct >= 50.0:
                severity = "critical"
            elif drop_pct >= 35.0:
                severity = "high"
            else:
                severity = "medium"

            anomalies.append(
                {
                    "date": ordered[i].get("date"),
                    "platform": ordered[i].get("platform"),
                    "type": "income_drop",
                    "severity": severity,
                    "value": round(drop_pct, 1),
                    "explanation": (
                        f"Net income dropped by {drop_pct:.1f}% compared to the previous "
                        f"shift ({prev_net:.2f} to {curr_net:.2f})."
                    ),
                }
            )

    for record in ordered:
        gross = _to_float(record.get("gross_earned"), 0.0)
        net = _to_float(record.get("net_received"), 0.0)
        if gross > 0 and net <= 0:
            anomalies.append(
                {
                    "date": record.get("date"),
                    "platform": record.get("platform"),
                    "type": "zero_net",
                    "severity": "critical",
                    "value": round(net, 2),
                    "explanation": (
                        f"Gross earnings were {gross:.2f}, but net received was {net:.2f}. "
                        "This indicates full deduction or payout failure."
                    ),
                }
            )

    return anomalies
