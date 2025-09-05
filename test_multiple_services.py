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

def test_add_multiple_services_to_client(db_session: Session):
    # Create a client to associate services with
    client_data = {
        "name": "Test Client for Multiple Services",
        "client_type": "individual",
        "email": "test_multiple_services@example.com",
        "agency_id": str(uuid.uuid4()),
        "created_by": str(uuid.uuid4())
    }
    db_client = models.Client(**client_data)
    db_session.add(db_client)
    db_session.commit()
    db_session.refresh(db_client)
    
    services_data = [
        {"service_id": str(uuid.uuid4())},
        {"service_id": str(uuid.uuid4())}
    ]
    
    response = client.post(f"/services/{db_client.id}/services", json=services_data)
    
    assert response.status_code == 201
    response_data = response.json()
    assert len(response_data) == 2
    assert response_data[0]["service_id"] == services_data[0]["service_id"]
    assert response_data[1]["service_id"] == services_data[1]["service_id"]
    
    # Verify the services were added to the database
    client_services = db_session.query(models.ClientService).filter(models.ClientService.client_id == db_client.id).all()
    assert len(client_services) == 2
