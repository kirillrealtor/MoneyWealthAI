import asyncio
import sys

# Add the parent directory to the Python path if running directly
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import db
from app.redis_client import close_redis


async def main() -> None:
    await db.init_pool()
    try:
        await db.execute("UPDATE users SET is_verified = true WHERE email = 'noor@gmail.com'")
        print("Successfully verified noor@gmail.com!")
    finally:
        await close_redis()
        await db.close_pool()

if __name__ == "__main__":
    asyncio.run(main())
