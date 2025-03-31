from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
from api.db import engine, SessionLocal
from api.models import Base
from api.links.router import router as links_router
from api.auth.router import router as auth_router

from api.cache import get_redis
from datetime import datetime, timezone
from api.models import Link

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(auth_router)
app.include_router(links_router)

def delete_expired_links():
    db = SessionLocal()
    redis = get_redis()
    try:
        now = datetime.now(timezone.utc)
        links = db.query(Link).filter(Link.expires_at <= now).all()
        for link in links:
            db.delete(link)
            redis.delete(link.short_code)
            redis.delete(f"stats:{link.short_code}")
        db.commit()
    finally:
        db.close()

scheduler = BackgroundScheduler()
scheduler.add_job(delete_expired_links, 'interval', minutes=1)
scheduler.start()