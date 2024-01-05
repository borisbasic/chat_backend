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


def test_login(client):
    response = client.post('/register', json={'id': 1, 'username': 'boris'})
    
    assert response.status_code == 200
    assert response.json()['message'] == 'New user registered!'

    response = client.post('/login', json={'username': 'boris'})

    assert response.status_code == 200
    assert response.json()['username'] == 'boris'
    assert response.json()['id'] == 1