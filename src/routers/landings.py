from fastapi import APIRouter, Depends, HTTPException

from src.config.redis import enqueue_lead, get_redis
from src.config.security import get_current_affiliate_id
from src.schemas.lead import LeadIn

router = APIRouter(tags=["landings"])


@router.post("/lead")
async def create_lead(
    lead: LeadIn, token_affiliate_id: int = Depends(get_current_affiliate_id)
) -> dict:
    if lead.affiliate_id != token_affiliate_id:
        raise HTTPException(
            status_code=403, detail="affiliate_id mismatch with bearer token"
        )

    redis = get_redis()
    await enqueue_lead(redis, lead)
    await redis.aclose()
    return {"status": "queued"}
