from fastapi.testclient import TestClient
from main import app
from database.database import get_db, Base
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

SQLALCHEMY_DATABASE_URL = 'sqlite://'
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={'check_same_thread': False},
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


def test_create_user(client):
    response = client.post('/register', json={'id': 1, 'username': 'boris'})

    assert response.status_code == 200
    assert response.json()['message'] == 'New user registered!'


def test_get_all_users_beside_me(client):
    response = client.post('/register', json={'id': 1, 'username': 'boris'})
    response_1 = client.post('/register', json={'id': 2, 'username': 'boris_1'})
    response_2 = client.post('/register', json={'id': 3, 'username': 'boris_2'})

    response = client.get('/users/1')

    assert response.status_code == 200
    assert response.json()[0]['username'] == 'boris_1'
    assert response.json()[1]['username'] == 'boris_2'
