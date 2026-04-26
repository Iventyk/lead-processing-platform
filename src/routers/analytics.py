from collections import defaultdict
from datetime import date, datetime, time

from fastapi import APIRouter, Depends, Query
from sqlalchemy import Integer, String, cast, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.security import get_current_affiliate_id
from src.database.models import Lead, Offer
from src.database.session import get_session
from src.schemas.lead import GroupBy, LeadOut

router = APIRouter(tags=["analytics"])


@router.get("/leads")
async def get_leads(
    date_from: date = Query(...),
    date_to: date = Query(...),
    group: GroupBy = Query(...),
    affiliate_id: int = Depends(get_current_affiliate_id),
    session: AsyncSession = Depends(get_session),
) -> dict:
    if date_from > date_to:
        return {
            "affiliate_id": affiliate_id,
            "date_from": date_from.isoformat(),
            "date_to": date_to.isoformat(),
            "group": group.value,
            "items": [],
        }

    dt_from = datetime.combine(date_from, time.min)
    dt_to = datetime.combine(date_to, time.max)

    query = (
        select(Lead)
        .where(cast(Lead.affiliate_id, Integer) == affiliate_id)
        .where(Lead.created_at >= dt_from)
        .where(Lead.created_at <= dt_to)
        .order_by(Lead.created_at.asc())
    )
    result = await session.execute(query)
    leads = list(result.scalars().all())

    buckets: dict[str, list[Lead]] = defaultdict(list)
    if group == GroupBy.date:
        for lead in leads:
            buckets[lead.created_at.date().isoformat()].append(lead)
    else:
        offer_ids = {str(lead.offer_id) for lead in leads}
        offer_names: dict[str, str] = {}
        if offer_ids:
            offers_result = await session.execute(
                select(Offer.id, Offer.name).where(
                    cast(Offer.id, String).in_(offer_ids)
                )
            )
            offer_names = {
                str(offer_id): offer_name
                for offer_id, offer_name in offers_result.all()
            }
        for lead in leads:
            offer_name = offer_names.get(str(lead.offer_id), "unknown")
            buckets[f"{lead.offer_id}:{offer_name}"].append(lead)

    response = []
    for key, items in buckets.items():
        response.append(
            {
                "key": key,
                "count": len(items),
                "leads": [
                    LeadOut.model_validate(
                        lead, from_attributes=True
                    ).model_dump()
                    for lead in items
                ],
            }
        )

    return {
        "affiliate_id": affiliate_id,
        "date_from": date_from.isoformat(),
        "date_to": date_to.isoformat(),
        "group": group.value,
        "items": response,
    }
