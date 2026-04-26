from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import Integer, cast, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.redis import enqueue_lead, get_redis
from src.config.security import get_current_affiliate_id
from src.database.models import Offer
from src.database.session import get_session
from src.schemas.lead import LeadIn

router = APIRouter(tags=["landings"])


@router.post("/lead")
async def create_lead(
        lead: LeadIn,
        token_affiliate_id: int = Depends(get_current_affiliate_id),
        session: AsyncSession = Depends(get_session),
) -> dict:
    if lead.affiliate_id != token_affiliate_id:
        raise HTTPException(
            status_code=403, detail="affiliate_id mismatch with bearer token"
        )

    offer_result = await session.execute(
        select(Offer.id).where(cast(Offer.id, Integer) == lead.offer_id)
    )
    if offer_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=400, detail="Offer not found")

    redis = get_redis()
    await enqueue_lead(redis, lead)
    await redis.aclose()
    return {"status": "queued"}
