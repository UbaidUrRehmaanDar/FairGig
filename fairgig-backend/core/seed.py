import argparse
import asyncio
import os
import random
from datetime import date, timedelta
from typing import Dict, List, Sequence

import asyncpg
from dotenv import load_dotenv

load_dotenv()

PLATFORMS_BY_CATEGORY = {
    "ride_hailing": ["Careem", "InDrive", "Bykea"],
    "food_delivery": ["Foodpanda", "Cheetay"],
    "freelance": ["Upwork", "Fiverr"],
    "domestic": ["Local Services"],
    "general": ["Careem", "InDrive", "Bykea", "Foodpanda", "Cheetay"],
}
DEFAULT_PLATFORMS = ["Careem", "InDrive", "Bykea", "Foodpanda", "Cheetay"]
VERIFICATION_STATUSES = ["verified", "pending", "unverified", "disputed"]


def _pick_platform(category: str) -> str:
    candidates = PLATFORMS_BY_CATEGORY.get((category or "").strip().lower(), DEFAULT_PLATFORMS)
    return random.choice(candidates)


def _build_seed_row(profile: Dict[str, str], days_back: int) -> Sequence:
    gross = round(random.uniform(2500, 9000), 2)
    deduction_pct = random.uniform(0.15, 0.35)
    deductions = round(gross * deduction_pct, 2)
    net = round(max(gross - deductions, 0), 2)
    hours = round(random.uniform(4, 11), 2)
    shift_date = date.today() - timedelta(days=random.randint(0, max(days_back, 0)))

    # Keep most seeded rows verified so Phase 5 certificate demos always have data.
    status = random.choices(VERIFICATION_STATUSES, weights=[0.7, 0.15, 0.1, 0.05], k=1)[0]

    return (
        profile["id"],
        _pick_platform(profile.get("platform_category", "general")),
        shift_date,
        hours,
        gross,
        deductions,
        net,
        "seeded demo data",
        status,
    )


async def seed(target_rows: int = 60, days_back: int = 30) -> None:
    database_url = (os.getenv("DATABASE_URL") or "").strip()
    if not database_url:
        raise RuntimeError("DATABASE_URL is missing. Seed aborted.")

    conn = await asyncpg.connect(database_url)
    try:
        profiles = await conn.fetch(
            """
            SELECT
                id,
                COALESCE(NULLIF(platform_category, ''), 'general') AS platform_category,
                COALESCE(NULLIF(city_zone, ''), 'Unknown') AS city_zone
            FROM profiles
            ORDER BY created_at ASC
            """
        )

        if not profiles:
            raise RuntimeError(
                "No profiles found. Create at least one authenticated profile before seeding shifts."
            )

        profile_dicts: List[Dict[str, str]] = [
            {
                "id": str(row["id"]),
                "platform_category": str(row["platform_category"]),
                "city_zone": str(row["city_zone"]),
            }
            for row in profiles
        ]

        rows_to_insert: List[Sequence] = []

        # Ensure every profile gets at least one current-period verified shift.
        for p in profile_dicts:
            base = list(_build_seed_row(p, days_back=7))
            base[8] = "verified"
            rows_to_insert.append(tuple(base))

        remaining = max(target_rows - len(rows_to_insert), 0)
        for _ in range(remaining):
            p = random.choice(profile_dicts)
            rows_to_insert.append(_build_seed_row(p, days_back=days_back))

        async with conn.transaction():
            await conn.executemany(
                """
                INSERT INTO shifts (
                    worker_id,
                    platform,
                    shift_date,
                    hours_worked,
                    gross_earned,
                    platform_deductions,
                    net_received,
                    notes,
                    verification_status
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                rows_to_insert,
            )

            await conn.execute("REFRESH MATERIALIZED VIEW city_medians")

        total_shifts = await conn.fetchval("SELECT COUNT(*) FROM shifts")
        total_verified = await conn.fetchval(
            "SELECT COUNT(*) FROM shifts WHERE verification_status = 'verified'"
        )
        city_medians_rows = await conn.fetchval("SELECT COUNT(*) FROM city_medians")
        distinct_platforms = await conn.fetchval("SELECT COUNT(DISTINCT platform) FROM shifts")
        distinct_zones = await conn.fetchval(
            """
            SELECT COUNT(DISTINCT p.city_zone)
            FROM shifts s
            JOIN profiles p ON p.id = s.worker_id
            """
        )

        print(
            "Seed complete:",
            {
                "inserted_rows": len(rows_to_insert),
                "total_shifts": int(total_shifts or 0),
                "verified_shifts": int(total_verified or 0),
                "city_medians_rows": int(city_medians_rows or 0),
                "distinct_platforms": int(distinct_platforms or 0),
                "distinct_zones": int(distinct_zones or 0),
            },
        )
    finally:
        await conn.close()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed FairGig demo shifts and refresh city medians")
    parser.add_argument("--rows", type=int, default=60, help="Number of shifts to insert (default: 60)")
    parser.add_argument(
        "--days-back",
        type=int,
        default=30,
        help="Seed shift dates in [today - days_back, today] (default: 30)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    asyncio.run(seed(target_rows=max(args.rows, 1), days_back=max(args.days_back, 0)))
