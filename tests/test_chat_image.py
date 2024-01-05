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


def test_image_upload(client):
    file_path = "/home/boris/Downloads/profilna_slika.jpg"
    response = client.post("/image", files={"image": open(file_path, "rb")})

    assert response.status_code == 200
    assert "filename" in response.json()


def test_image_ext(client):
    file_path = "/home/boris/Downloads/prezentacija.pptx"

    ext = file_path.split(".")[-1]

    response = client.post("/image", files={"image": open(file_path, "rb")})

    assert response.status_code == 406
    assert response.json()["detail"] == f"Image with extension {ext} not acceptable"


def test_image_chat(client):
    response = client.post("/register", json={"id": 1, "username": "boris"})
    response_1 = client.post("/register", json={"id": 2, "username": "boris_1"})

    response_room_number = client.get("/room_number/1/2")

    file_path = "/home/boris/Downloads/profilna_slika.jpg"
    response_image = client.post("/image", files={"image": open(file_path, "rb")})

    response_chat_image = client.post(
        "/chat_image",
        json={
            "image_name": response_image.json()["filename"],
            "sender_id": 1,
            "receiver_id": 2,
            "room_id": response_room_number.json()["id"],
        },
    )

    assert response_chat_image.status_code == 200
    assert response_chat_image.json()["image_name"] == response_image.json()["filename"]
