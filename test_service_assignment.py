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
        # models.Base.metadata.drop_all(bind=engine) # Disabling for now to avoid dependency issues

def test_assign_multiple_services_to_client(db_session: Session):
    # 1. Fetch the Agency id (assuming one exists or creating one)
    agency = db_session.query(models.Agency).first()
    if not agency:
        agency = models.Agency(name="Test Agency", created_by=uuid.uuid4())
        db_session.add(agency)
        db_session.commit()
        db_session.refresh(agency)
    
    # 2. Create a Client
    client_data = {
        "name": "Test Client for Service Assignment",
        "client_type": "individual",
        "email": "test_assignment@example.com",
        "agency_id": agency.id,
        "created_by": uuid.uuid4(),
        "customer_id": f"CUST-{uuid.uuid4().hex[:6].upper()}"
    }
    db_client = models.Client(**client_data)
    db_session.add(db_client)
    db_session.commit()
    db_session.refresh(db_client)

    # 3. List the Services (assuming services are pre-populated or we create them)
    # For this test, we'll assume we have the service IDs.
    service_ids = [uuid.uuid4(), uuid.uuid4()]

    # 4. Assign multiple service id to the Client and save it
    services_data = [{"service_id": str(sid)} for sid in service_ids]
    
    response = client.post(f"/services/{db_client.id}/services", json=services_data)
    
    assert response.status_code == 201
    response_data = response.json()
    assert len(response_data) == 2
    
    # Verify the services were added to the database
    client_services = db_session.query(models.ClientService).filter(models.ClientService.client_id == db_client.id).all()
    assert len(client_services) == 2
    db_session.delete(db_client)
    db_session.commit()
