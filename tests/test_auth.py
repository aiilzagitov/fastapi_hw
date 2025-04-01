def test_create_user(client):
    response = client.post(
        "/users/createUsers",
        json={"username": "testuser", "password": "testpass"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "User created successfully"

    response = client.post(
        "/users/createUsers",
        json={"username": "testuser", "password": "testpass"}
    )
    assert response.status_code == 400
    assert "Username already exists" in response.json()["detail"]

def test_login_for_access_token(client):
    client.post("/users/createUsers", json={"username": "testuser", "password": "testpass"})

    response = client.post(
        "/token",
        data={"username": "testuser", "password": "testpass"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

    response = client.post(
        "/token",
        data={"username": "testuser", "password": "wrongpass"}
    )
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]

def test_read_users_me(client):
    client.post("/users/createUsers", json={"username": "testuser", "password": "testpass"})
    token_response = client.post(
        "/token",
        data={"username": "testuser", "password": "testpass"}
    )
    token = token_response.json()["access_token"]

    response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["username"] == "testuser"

    response = client.get(
        "/users/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401