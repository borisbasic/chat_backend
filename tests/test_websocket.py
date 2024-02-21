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


def test_websockets(client):
    response = client.post("/register", json={"id": 1, "username": "boris"})
    response_1 = client.post("/register", json={"id": 2, "username": "boris_1"})

    response_room_number = client.get("/room_number/1/2")

    assert response_room_number.json()['id'] == 1

    response_websocket = client.websocket_connect("/ws/1")
    data = {
        "sender_id": 1,
        "receiver_id": 2,
        "content": "First message",
        "type_of_message": "text",
    }
    response_websocket.send_json(data)
    assert 'message'in response_websocket.receive_json()
