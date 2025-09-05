import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal, engine
from app import models
from sqlalchemy.orm import Session
import pytest

client = TestClient(app)

@pytest.fixture(scope="module")
def db_session():
    # Setup: Create tables
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Teardown: Drop tables
        models.Base.metadata.drop_all(bind=engine)

def test_create_client_portal_client_not_found(db_session: Session):
    # A non-existent client ID
    non_existent_client_id = uuid.uuid4()
    
    portal_data = {
        "portal_id": str(uuid.uuid4()),
        "username": "testuser",
        "password": "testpassword",
        "notes": "Test notes"
    }
    
    response = client.post(f"/clients/{non_existent_client_id}/portals", json=portal_data)
    
    assert response.status_code == 404
    assert response.json() == {"detail": "Client not found"}
