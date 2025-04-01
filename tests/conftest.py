import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import Generator
import redis

from api.main import app
from api.db import Base, get_db
from api import models as md
from api.cache import get_redis
from api.auth.users import get_current_user, get_current_user_optional

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

TEST_REDIS_URL = "redis://localhost:6379/1"


def override_get_redis():
    return redis.Redis.from_url(TEST_REDIS_URL, decode_responses=True)


@pytest.fixture(scope="function")
def db_session() -> Generator:
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def redis_client() -> Generator:
    redis_client = override_get_redis()
    redis_client.flushdb()
    yield redis_client
    redis_client.flushdb()

# @pytest.fixture
# def auth_test_client():
#     with TestClient(app) as client:
#         yield client

@pytest.fixture(scope="function")
def client(db_session, redis_client):
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_redis] = override_get_redis

    def override_get_current_user():
        return md.User(id=1, username="example_username")

    def override_get_current_user_optional():
        return None

    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_current_user_optional] = override_get_current_user_optional

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture
def auth_client(client):
    def override_get_current_user():
        return md.User(id=1, username="example_username")

    client.app.dependency_overrides[get_current_user] = override_get_current_user
    client.app.dependency_overrides[get_current_user_optional] = override_get_current_user
    return client