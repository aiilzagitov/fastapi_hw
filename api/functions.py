import api.models as md
from sqlalchemy.orm import Session


def get_link_by_orig_url_and_user_id(
    original_url: str,
    user_id: int,
    db: Session
) -> md.Link:
    res = db.query(md.Link).filter(
        md.Link.original_url == original_url,
        md.Link.user_id == user_id
    ).first()

    return res


def get_link_by_short_code_and_user_id(
    short_code: str,
    user_id: int,
    db: Session
) -> md.Link:
    res = db.query(md.Link).filter(
        md.Link.short_code == short_code,
        md.Link.user_id == user_id
    ).first()

    return res