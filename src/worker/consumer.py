import asyncio
import hashlib
import json

from sqlalchemy import Integer, cast, select

from src.config.redis import QUEUE_NAME, get_redis
from src.database.models import Affiliate, Lead, Offer
from src.database.session import SessionLocal


def dedup_key(payload: dict) -> str:
    raw = f"{payload['name']}|{payload['phone']}|{payload['offer_id']}|{payload['affiliate_id']}"  # noqa
    return "lead_dedup:" + hashlib.sha256(raw.encode()).hexdigest()


async def process_message(payload: dict) -> None:
    async with SessionLocal() as session:
        offer_exists = await session.execute(
            select(Offer.id).where(
                cast(Offer.id, Integer) == payload["offer_id"]
            )
        )
        aff_exists = await session.execute(
            select(Affiliate.id).where(
                cast(Affiliate.id, Integer) == payload["affiliate_id"]
            )
        )
        if (
            offer_exists.scalar_one_or_none() is None
            or aff_exists.scalar_one_or_none() is None
        ):
            return

        lead = Lead(**payload)
        session.add(lead)
        await session.commit()


async def run_worker() -> None:
    redis = get_redis()
    while True:
        item = await redis.blpop(QUEUE_NAME, timeout=5)
        if item is None:
            continue

        _, value = item
        payload = json.loads(value)
        key = dedup_key(payload)
        if await redis.get(key):
            continue
        await redis.set(key, "1", ex=600)
        await process_message(payload)


if __name__ == "__main__":
    asyncio.run(run_worker())
