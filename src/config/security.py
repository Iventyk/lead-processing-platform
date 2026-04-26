from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from jwt import InvalidTokenError
from sqlalchemy import String, cast, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import settings
from src.database.models import Affiliate
from src.database.session import get_session

bearer = HTTPBearer(auto_error=True)


async def get_current_affiliate_id(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    session: AsyncSession = Depends(get_session),
) -> int:
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        affiliate_id = int(payload["id"])
        affiliate_id_lookup = str(affiliate_id)
    except (InvalidTokenError, KeyError, TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    result = await session.execute(
        select(Affiliate.id).where(
            cast(Affiliate.id, String) == affiliate_id_lookup
        )
    )

    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Affiliate not found",
        )

    return affiliate_id
