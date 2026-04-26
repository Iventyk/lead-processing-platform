from collections import defaultdict
from datetime import date, datetime, time

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.config.security import get_current_affiliate_id
from src.database.models import Lead
from src.database.session import get_session
from src.schemas.lead import GroupBy, LeadOut

router = APIRouter(tags=["analytics"])


@router.get("/leads")
async def get_leads(
    date_from: date = Query(...),
    date_to: date = Query(...),
    group: GroupBy = Query(...),
    affiliate_id: str = Depends(get_current_affiliate_id),
    session: AsyncSession = Depends(get_session),
) -> dict:
    dt_from = datetime.combine(date_from, time.min)
    dt_to = datetime.combine(date_to, time.max)

    query = (
        select(Lead)
        .where(Lead.affiliate_id == affiliate_id)
        .where(Lead.created_at >= dt_from)
        .where(Lead.created_at <= dt_to)
        .options(selectinload(Lead.offer))
        .order_by(Lead.created_at.asc())
    )
    result = await session.execute(query)
    leads = list(result.scalars().all())

    buckets: dict[str, list[Lead]] = defaultdict(list)
    if group == GroupBy.date:
        for lead in leads:
            buckets[lead.created_at.date().isoformat()].append(lead)
    else:
        for lead in leads:
            buckets[f"{lead.offer_id}:{lead.offer.name}"].append(lead)

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
