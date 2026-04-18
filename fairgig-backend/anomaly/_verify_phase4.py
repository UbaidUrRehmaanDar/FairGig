from fastapi.testclient import TestClient

from main import app


def run() -> None:
    client = TestClient(app)

    judge_payload = {
        "worker_id": "test-001",
        "earnings": [
            {
                "date": "2026-03-01",
                "platform": "Careem",
                "gross_earned": 5000,
                "platform_deductions": 1000,
                "net_received": 4000,
                "hours_worked": 8,
            },
            {
                "date": "2026-03-02",
                "platform": "Careem",
                "gross_earned": 5000,
                "platform_deductions": 2500,
                "net_received": 2500,
                "hours_worked": 8,
            },
            {
                "date": "2026-03-03",
                "platform": "Careem",
                "gross_earned": 5000,
                "platform_deductions": 1000,
                "net_received": 1000,
                "hours_worked": 8,
            },
        ],
    }

    judge_response = client.post("/anomaly/detect", json=judge_payload)
    assert judge_response.status_code == 200, judge_response.text
    judge_data = judge_response.json()

    assert judge_data.get("anomalies_found", 0) >= 2, judge_data
    assert all(
        all(key in anomaly for key in ("date", "type", "severity", "value", "explanation"))
        for anomaly in judge_data.get("anomalies", [])
    ), judge_data

    crafted_payload = {
        "worker_id": "test-002",
        "earnings": [
            {
                "date": "2026-03-01",
                "platform": "InDrive",
                "gross_earned": 5000,
                "platform_deductions": 500,
                "net_received": 4500,
                "hours_worked": 8,
            },
            {
                "date": "2026-03-02",
                "platform": "InDrive",
                "gross_earned": 5000,
                "platform_deductions": 3200,
                "net_received": 1800,
                "hours_worked": 8,
            },
            {
                "date": "2026-03-03",
                "platform": "InDrive",
                "gross_earned": 4000,
                "platform_deductions": 4100,
                "net_received": 0,
                "hours_worked": 8,
            },
        ],
    }

    crafted_response = client.post("/anomaly/detect", json=crafted_payload)
    assert crafted_response.status_code == 200, crafted_response.text
    crafted_data = crafted_response.json()

    crafted_types = {anomaly.get("type") for anomaly in crafted_data.get("anomalies", [])}
    assert {"unusual_deduction", "income_drop", "zero_net"}.issubset(crafted_types), crafted_data

    legacy_response = client.post("/detect", json=judge_payload)
    assert legacy_response.status_code == 200, legacy_response.text

    print("judge_anomalies_found:", judge_data.get("anomalies_found"))
    print("judge_types:", [anomaly.get("type") for anomaly in judge_data.get("anomalies", [])])
    print("crafted_anomalies_found:", crafted_data.get("anomalies_found"))
    print("crafted_types:", sorted(crafted_types))
    print("legacy_route_status:", legacy_response.status_code)
    print("phase4_verify: PASS")


if __name__ == "__main__":
    run()
