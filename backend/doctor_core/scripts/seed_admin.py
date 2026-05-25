from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
import sys

service_root = Path(__file__).resolve().parents[1]
if str(service_root) not in sys.path:
    sys.path.insert(0, str(service_root))

from core.cruds.user_crud import user_crud
from core.database.mongodb import mongo_manager
from core.utils.security import hash_secret, now_utc


async def seed_admin(email: str, password: str, name: str) -> None:
    await mongo_manager.connect()
    try:
        admin = await user_crud.upsert_admin(
            email=email.lower(),
            name=name,
            password_hash=hash_secret(password),
            now=now_utc(),
        )
        print(f"Admin ready: {admin['email']}")
    finally:
        await mongo_manager.disconnect()


def main() -> None:
    parser = argparse.ArgumentParser(description="Create or update a Doctor AI admin user.")
    parser.add_argument("--email", required=True, help="Admin email address")
    parser.add_argument("--password", required=True, help="Admin password")
    parser.add_argument("--name", default="Admin User", help="Admin display name")
    args = parser.parse_args()
    asyncio.run(seed_admin(email=args.email, password=args.password, name=args.name))


if __name__ == "__main__":
    main()
