from api.db import engine, SessionLocal
from api.models import Base

Base.metadata.create_all(bind=engine)