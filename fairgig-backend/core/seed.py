import asyncio
import os
import random
from datetime import date, timedelta

import asyncpg
from dotenv import load_dotenv

load_dotenv()

PLATFORMS = ["Careem", "InDrive", "Bykea", "Foodpanda", "Cheetay"]


async def seed():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL is missing. Seed skipped.")
        return

    pool = await asyncpg.create_pool(database_url)
    for _ in range(10):
        platform = random.choice(PLATFORMS)
        gross = random.uniform(2000, 8000)
        deduct = gross * random.uniform(0.15, 0.30)
        net = gross - deduct
        shift_date = date.today() - timedelta(days=random.randint(0, 30))
        print(f"Planned seed row: {platform} {shift_date} gross={gross:.0f} net={net:.0f}")

    await pool.close()
    print("Seed skeleton complete")


if __name__ == "__main__":
    asyncio.run(seed())
