import asyncio
import sys
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import db
from app.config import settings
from app.crypto import hash_password
from app.redis_client import close_redis


async def main():
    email = "noor@gmail.com"
    pwd = "Qwerty@123"
    
    await db.init_pool()
    try:
        tenant = settings.default_tenant_id
        hashed = hash_password(pwd)
        
        async with db.with_tenant(tenant) as conn:
            existing = await conn.fetchval("SELECT user_id FROM users WHERE email = $1", email)
            if existing:
                await conn.execute(
                    "UPDATE users SET password_hash = $1, is_verified = true WHERE email = $2",
                    hashed,
                    email,
                )
                print(f"Updated existing user: {email}")
            else:
                user_id = str(
                    await conn.fetchval(
                        "INSERT INTO users (tenant_id, email, password_hash, is_verified) "
                        "VALUES ($1, $2, $3, true) RETURNING user_id",
                        tenant,
                        email,
                        hashed,
                    )
                )
                await conn.execute(
                    "INSERT INTO notification_preferences (user_id, tenant_id) VALUES ($1, $2)",
                    user_id,
                    tenant,
                )
                print(f"Created new user: {email}")
            
    finally:
        await close_redis()
        await db.close_pool()

if __name__ == "__main__":
    asyncio.run(main())
