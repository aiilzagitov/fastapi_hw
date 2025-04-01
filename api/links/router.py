from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
import api.models as md
from api.schema import LinkResponse, LinkCreate, RedirectResponse, LinkUpdate, LinkStatsResponse
from api.db import get_db

from datetime import datetime, timezone
from api.cache import get_redis
from api.utils import get_unique_short_code
from api.auth.users import get_current_user_optional, get_current_user
from api.functions import get_link_by_orig_url_and_user_id, get_link_by_short_code_and_user_id

router = APIRouter(prefix="/links")


@router.post("/shorten", response_model=LinkResponse)
def shorten_link(
    link: LinkCreate,
    db: Session = Depends(get_db),
    user: md.User = Depends(get_current_user_optional),
    redis=Depends(get_redis),
):
    if user:
        existing_user_link = get_link_by_orig_url_and_user_id(str(link.original_url), user.id, db)
        if existing_user_link:
            raise HTTPException(
                status_code=400,
                detail="You already have a shortened link for this URL"
            )

    if link.custom_alias:
        existing = db.query(md.Link).filter(md.Link.short_code == link.custom_alias).first()
        if existing:
            raise HTTPException(status_code=400, detail="Alias already exists")
        short_code = link.custom_alias
    else:
        short_code = get_unique_short_code(db)

    db_link = md.Link(
        original_url=str(link.original_url),
        short_code=short_code,
        expires_at=link.expires_at,
        user_id=user.id if user else None
    )
    db.add(db_link)
    db.commit()

    if db_link.expires_at:
        if db_link.expires_at.tzinfo is None:
            db_link.expires_at = db_link.expires_at.replace(tzinfo=timezone.utc)
        ttl = (db_link.expires_at - datetime.now(timezone.utc)).total_seconds()
        # ttl = (db_link.expires_at - datetime.now(timezone.utc)).total_seconds()
    else:
        ttl = 24 * 3600
    if ttl > 0:
        redis.setex(short_code, int(ttl), str(link.original_url))

    return db_link


@router.get("/{short_code}")
def redirect_to_original(
    short_code: str,
    db: Session = Depends(get_db),
    redis=Depends(get_redis),
    user: md.User = Depends(get_current_user_optional),
):
    if user:
        db_link = get_link_by_short_code_and_user_id(short_code, user.id, db)
        if db_link:
            db_link.hit_count += 1
            db_link.last_accessed_at = datetime.now(timezone.utc)
            db.commit()

    original_url = redis.get(short_code)
    if original_url:
        return RedirectResponse(original_url=original_url)

    db_link = db.query(md.Link).filter(md.Link.short_code == short_code).first()
    if not db_link:
        raise HTTPException(status_code=404, detail="Link not found")

    now = datetime.now(timezone.utc)
    if db_link.expires_at and db_link.expires_at < now:
        raise HTTPException(status_code=410, detail="Link expired")

    ttl = 24 * 3600
    if db_link.expires_at:
        ttl = max(0, int((db_link.expires_at - now).total_seconds()))

    if ttl > 0:
        redis.setex(short_code, ttl, db_link.original_url)

    return RedirectResponse(original_url=db_link.original_url)


@router.delete("/{short_code}", status_code=status.HTTP_204_NO_CONTENT)
def delete_link(
    short_code: str,
    db: Session = Depends(get_db),
    user: md.User = Depends(get_current_user),
    redis=Depends(get_redis)
):
    db_link = get_link_by_short_code_and_user_id(short_code, user.id, db)
    if not db_link:
        raise HTTPException(status_code=404, detail="Link not found")

    db.delete(db_link)
    db.commit()
    redis.delete(short_code)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/{short_code}", response_model=LinkResponse)
def update_link(
        short_code: str,
        link_update: LinkUpdate,
        db: Session = Depends(get_db),
        user: md.User = Depends(get_current_user),
        redis=Depends(get_redis)
):
    db_link = get_link_by_short_code_and_user_id(short_code, user.id, db)
    if not db_link:
        raise HTTPException(status_code=404, detail="Link not found")

    db_link.original_url = link_update.original_url
    db.commit()

    current_ttl = redis.ttl(short_code)
    if current_ttl > 0:
        redis.setex(short_code, current_ttl, db_link.original_url)
    elif current_ttl == -1:
        redis.set(short_code, db_link.original_url)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{short_code}/stats", response_model=LinkStatsResponse)
def get_link_stats(
        short_code: str,
        db: Session = Depends(get_db),
        user: md.User = Depends(get_current_user),
):
    db_link = get_link_by_short_code_and_user_id(short_code, user.id, db)

    if not db_link:
        raise HTTPException(status_code=404, detail="Link not found")

    return db_link