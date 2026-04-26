import json

from redis.asyncio import Redis

from src.config.settings import settings
from src.schemas.lead import LeadIn

QUEUE_NAME = "leads_queue"


def get_redis() -> Redis:
    return Redis.from_url(settings.redis_url, decode_responses=True)


async def enqueue_lead(redis: Redis, lead: LeadIn) -> None:
    await redis.rpush(QUEUE_NAME, json.dumps(lead.model_dump()))
    