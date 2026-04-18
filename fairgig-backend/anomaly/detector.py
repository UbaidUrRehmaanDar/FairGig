from typing import Dict, List

import numpy as np
from scipy import stats


def detect_anomalies(earnings: List[Dict]) -> List[Dict]:
    anomalies: List[Dict] = []
    if len(earnings) < 2:
        return anomalies

    deductions = [e["platform_deductions"] / max(e["gross_earned"], 1) * 100 for e in earnings]

    if len(deductions) >= 3:
        z_scores = np.abs(stats.zscore(deductions))
        for i, z in enumerate(z_scores):
            if z > 2.0:
                anomalies.append(
                    {
                        "date": earnings[i]["date"],
                        "platform": earnings[i]["platform"],
                        "type": "unusual_deduction",
                        "severity": "high" if z > 3.0 else "medium",
                    }
                )

    sorted_earnings = sorted(earnings, key=lambda x: x["date"])
    for i in range(1, len(sorted_earnings)):
        prev = sorted_earnings[i - 1]["net_received"]
        curr = sorted_earnings[i]["net_received"]
        if prev > 0:
            drop = (prev - curr) / prev
            if drop > 0.20:
                anomalies.append(
                    {
                        "date": sorted_earnings[i]["date"],
                        "platform": sorted_earnings[i]["platform"],
                        "type": "income_drop",
                        "severity": "high" if drop > 0.40 else "medium",
                        "value": round(drop * 100, 1),
                    }
                )

    for e in earnings:
        if e["gross_earned"] > 0 and e["net_received"] <= 0:
            anomalies.append(
                {
                    "date": e["date"],
                    "platform": e["platform"],
                    "type": "zero_net",
                    "severity": "critical",
                    "value": e["net_received"],
                }
            )

    return anomalies
