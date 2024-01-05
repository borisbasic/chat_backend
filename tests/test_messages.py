from fastapi.testclient import TestClient
from main import app
from database.database import get_db, Base
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

SQLALCHEMY_DATABASE_URL = "sqlite://"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture()
def session():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db

    finally:
        db.close()


@pytest.fixture()
def client(session):
    def override_get_db():
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db

    yield TestClient(app)


def test_message_post(client):
    response = client.post("/register", json={"id": 1, "username": "boris"})
    response_1 = client.post("/register", json={"id": 2, "username": "boris_1"})

    response_message = client.post(
        "/messages",
        json={
            "sender_id": 1,
            "receiver_id": 2,
            "content": "First message.",
            "type_of_message": "text",
        },
    )

    assert response_message.status_code == 200
    assert response_message.json()["sender_id"] == 1
    assert response_message.json()["receiver_id"] == 2
    assert response_message.json()["content"] == "First message."
    assert response_message.json()["type_of_message"] == "text"


def test_get_message(client):
    response = client.post("/register", json={"id": 1, "username": "boris"})
    response_1 = client.post("/register", json={"id": 2, "username": "boris_1"})

    response_message = client.post(
        "/messages",
        json={
            "sender_id": 1,
            "receiver_id": 2,
            "content": "First message.",
            "type_of_message": "text",
        },
    )
    response_message_2 = client.post(
        "/messages",
        json={
            "sender_id": 2,
            "receiver_id": 1,
            "content": "Second message.",
            "type_of_message": "text",
        },
    )

    response_get_messages = client.get("/messages/1/2")
    # response_get_messages = client.get('/messages/2/1')
    assert response_get_messages.status_code == 200
    assert response_get_messages.json()[0]["content"] == "First message."
    assert response_get_messages.json()[1]["content"] == "Second message."


def test_get_message_user_not_sender(client):
    response = client.get("/messages/1/2")

    assert response.status_code == 404
    assert response.json()["detail"] == "User with id: 1 not found."


def test_get_message_user_not_receiver(client):
    response = client.post("/register", json={"id": 1, "username": "boris"})

    response = client.get("/messages/1/2")

    assert response.status_code == 404
    assert response.json()["detail"] == "User with id: 2 not found."
