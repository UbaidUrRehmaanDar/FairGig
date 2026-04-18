import asyncio
import os
import random
import uuid
from datetime import date, timedelta

import asyncpg
from dotenv import load_dotenv

load_dotenv()

PLATFORMS = ["Careem", "InDrive", "Bykea", "Foodpanda", "Cheetay"]
CITY_ZONES = ["Gulberg", "DHA", "Johar Town", "Model Town", "Bahria Town"]
PLATFORM_CATEGORIES = ["ride_hailing", "food_delivery"]


def _choice_or_default(values, default):
    if not values:
        return default
    return random.choice(values)


def _build_shift_row(worker_id: uuid.UUID, days_back_limit: int = 60):
    platform = random.choice(PLATFORMS)
    gross = round(random.uniform(1600, 9000), 2)
    deduction_pct = random.uniform(0.12, 0.42)
    platform_deductions = round(gross * deduction_pct, 2)
    net = round(max(gross - platform_deductions, 0), 2)
    hours_worked = round(random.uniform(4, 12), 2)
    shift_date = date.today() - timedelta(days=random.randint(0, days_back_limit))

    return {
        "worker_id": worker_id,
        "platform": platform,
        "shift_date": shift_date,
        "hours_worked": hours_worked,
        "gross_earned": gross,
        "platform_deductions": platform_deductions,
        "net_received": net,
        "notes": "Seeded demo shift",
        "verification_status": "verified",
    }


async def _upsert_seed_profiles(conn: asyncpg.Connection, count: int = 12):
    ids = [uuid.uuid4() for _ in range(count)]

    for idx, profile_id in enumerate(ids, start=1):
        await conn.execute(
            """
            INSERT INTO profiles (id, full_name, city_zone, platform_category, role)
            VALUES ($1, $2, $3, $4, 'worker')
            ON CONFLICT (id) DO UPDATE SET
                full_name = EXCLUDED.full_name,
                city_zone = EXCLUDED.city_zone,
                platform_category = EXCLUDED.platform_category,
                role = EXCLUDED.role
            """,
            profile_id,
            f"Seed Worker {idx}",
            _choice_or_default(CITY_ZONES, "Gulberg"),
            _choice_or_default(PLATFORM_CATEGORIES, "ride_hailing"),
        )

    return ids


async def seed():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is missing. Cannot run seed.")

    desired_shift_count = int(os.getenv("SEED_SHIFT_COUNT", "60"))
    if desired_shift_count < 50:
        desired_shift_count = 50

    print(f"Starting seed with target verified shifts: {desired_shift_count}")

    pool = await asyncpg.create_pool(database_url, min_size=1, max_size=4)
    inserted = 0

    async with pool.acquire() as conn:
        async with conn.transaction():
            worker_ids = await _upsert_seed_profiles(conn)

            rows = []
            for _ in range(desired_shift_count):
                rows.append(_build_shift_row(random.choice(worker_ids)))

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
                [
                    (
                        row["worker_id"],
                        row["platform"],
                        row["shift_date"],
                        row["hours_worked"],
                        row["gross_earned"],
                        row["platform_deductions"],
                        row["net_received"],
                        row["notes"],
                        row["verification_status"],
                    )
                    for row in rows
                ],
            )
            inserted = len(rows)

        await conn.execute("REFRESH MATERIALIZED VIEW city_medians")

        medians_count = await conn.fetchval("SELECT COUNT(*)::int FROM city_medians")
        non_null_medians = await conn.fetchval(
            """
            SELECT COUNT(*)::int
            FROM city_medians
            WHERE median_hourly IS NOT NULL
               OR median_daily IS NOT NULL
            """
        )

        print(f"Inserted verified shifts: {inserted}")
        print(f"city_medians rows: {medians_count}")
        print(f"city_medians non-null rows: {non_null_medians}")

    await pool.close()
    print("Seed completed successfully.")


async def verify_city_median_sample():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is missing. Cannot verify city medians.")

    conn = await asyncpg.connect(database_url)
    try:
        sample = await conn.fetchrow(
            """
            SELECT
                platform,
                city_zone,
                platform_category,
                month,
                median_hourly,
                median_daily,
                avg_commission_pct,
                sample_size
            FROM city_medians
            ORDER BY month DESC, sample_size DESC
            LIMIT 1
            """
        )

        if sample is None:
            print("city_medians verification: no rows found")
            return

        print("city_medians verification sample:")
        for key in sample.keys():
            print(f"- {key}: {sample[key]}")
    finally:
        await conn.close()


async def main():
    await seed()
    await verify_city_median_sample()


if __name__ == "__main__":
    asyncio.run(main())
