from fastapi import status
import datetime
from datetime import datetime, timedelta, timezone
import api.models as md

def test_shorten_link_unauthenticated(client, db_session):
    response = client.post(
        "/links/shorten",
        json={"original_url": "https://example.com"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "short_code" in data

def test_shorten_link_authenticated_duplicate(auth_client, db_session):
    response = auth_client.post(
        "/links/shorten",
        json={"original_url": "https://example.com"}
    )
    assert response.status_code == 200

    response = auth_client.post(
        "/links/shorten",
        json={"original_url": "https://example.com"}
    )
    assert response.status_code == 400
    assert "already have a shortened link" in response.json()["detail"]

def test_shorten_link_custom_alias_conflict(client, db_session):
    response = client.post(
        "/links/shorten",
        json={"original_url": "https://example.com", "custom_alias": "test"}
    )
    assert response.status_code == 200

    response = client.post(
        "/links/shorten",
        json={"original_url": "https://another.com", "custom_alias": "test"}
    )
    assert response.status_code == 400
    assert "Alias already exists" in response.json()["detail"]

def test_redirect_to_original(client, db_session):
    response = client.post(
        "/links/shorten",
        json={"original_url": "https://example.com"}
    )
    short_code = response.json()["short_code"]

    response = client.get(f"/links/{short_code}")
    assert response.status_code == 200
    assert response.json()["original_url"] == "https://example.com/"

def test_redirect_increments_hit_count(auth_client, db_session):
    response = auth_client.post(
        "/links/shorten",
        json={"original_url": "https://example.com"}
    )
    short_code = response.json()["short_code"]

    auth_client.get(f"/links/{short_code}")

    response = auth_client.get(f"/links/{short_code}/stats")
    assert response.status_code == 200
    assert response.json()["hit_count"] == 1

def test_delete_link(auth_client, db_session, redis_client):
    response = auth_client.post(
        "/links/shorten",
        json={"original_url": "https://example.com"}
    )
    short_code = response.json()["short_code"]

    response = auth_client.delete(f"/links/{short_code}")
    assert response.status_code == 204

    response = auth_client.get(f"/links/{short_code}")
    assert response.status_code == 404

    assert redis_client.get(short_code) is None


def test_update_link_url(auth_client, db_session, redis_client):
    response = auth_client.post(
        "/links/shorten",
        json={"original_url": "https://example.com"}
    )
    short_code = response.json()["short_code"]
    original_ttl = redis_client.ttl(short_code)

    update_data = {"original_url": "https://updated.com"}
    response = auth_client.put(
        f"/links/{short_code}",
        json=update_data
    )
    assert response.status_code == 204

    response = auth_client.get(f"/links/{short_code}/stats")
    assert response.json()["original_url"] == "https://updated.com"

    assert redis_client.get(short_code) == "https://updated.com"
    assert redis_client.ttl(short_code) == original_ttl

def test_get_invalid_link_stats(client):
    response = client.get("/links/invalid/stats")
    assert response.status_code == 404

def test_shorten_link_with_past_expires_at(client, db_session, redis_client):
    past_time = datetime.now(timezone.utc) - timedelta(hours=1)
    expires_at_iso = past_time.isoformat()

    response = client.post(
        "/links/shorten",
        json={
            "original_url": "https://past.example.com",
            "expires_at": expires_at_iso
        }
    )
    assert response.status_code == 200
    data = response.json()

    assert data["expires_at"] == past_time.isoformat().replace("+00:00", "Z")

    db_link = db_session.query(md.Link).filter(md.Link.short_code == data["short_code"]).first()
    assert db_link.expires_at.replace(tzinfo=None) == past_time.replace(tzinfo=None)

    assert redis_client.get(data["short_code"]) is None