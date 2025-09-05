from typing import List
import uuid
import requests
from fastapi import APIRouter, Depends, status, HTTPException, Header
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import SessionLocal
from ..dependencies import get_current_user, get_current_agency, http_bearer
from ..security import has_role, Role
import os

router = APIRouter()

SERVICE_API_URL = os.getenv("SERVICE_API_URL")

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", status_code=status.HTTP_200_OK)
def list_external_services(
    current_user: dict = Depends(get_current_user),
    current_agency: dict = Depends(get_current_agency),
    token: str = Depends(http_bearer),
):
    headers = {
        "accept": "application/json",
        "x-agency-id": str(current_agency.get("id")),
        "Authorization": f"Bearer {token.credentials}",
    }
    try:
        response = requests.get(f"{SERVICE_API_URL}/services/", headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Error connecting to services API: {e}")

@router.post("/{client_id}/services", response_model=List[schemas.ClientServiceLink], status_code=status.HTTP_201_CREATED, dependencies=[Depends(has_role([Role.SUPER_ADMIN, Role.AGENCY_ADMIN, Role.CA_ACCOUNTANT]))])
def add_service_to_client(
    client_id: uuid.UUID,
    services_in: List[schemas.ClientServiceLink],
    db: Session = Depends(get_db),
):
    # Get existing service IDs for the client to avoid duplicates
    existing_service_ids = {
        s.service_id for s in
        db.query(models.ClientService).filter(models.ClientService.client_id == client_id).all()
    }

    db_client_services = []
    try:
        for service_in in services_in:
            if service_in.service_id not in existing_service_ids:
                db_client_service = models.ClientService(
                    client_id=client_id, service_id=service_in.service_id
                )
                db.add(db_client_service)
                db_client_services.append(db_client_service)
        
        if db_client_services:
            db.commit()
            for db_client_service in db_client_services:
                db.refresh(db_client_service)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    
    return db_client_services

@router.get("/{client_id}/services", response_model=List[schemas.ClientServiceLink], dependencies=[Depends(has_role([Role.SUPER_ADMIN, Role.AGENCY_ADMIN, Role.CA_ACCOUNTANT, Role.CA_TEAM]))])
def get_client_services(
    client_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    return db.query(models.ClientService).filter(models.ClientService.client_id == client_id).all()

@router.delete("/{client_id}/services", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(has_role([Role.SUPER_ADMIN, Role.AGENCY_ADMIN, Role.CA_ACCOUNTANT]))])
def remove_services_from_client(
    client_id: uuid.UUID,
    services_in: schemas.ClientServiceRemove,
    db: Session = Depends(get_db),
):
    try:
        db.query(models.ClientService).filter(
            models.ClientService.client_id == client_id,
            models.ClientService.service_id.in_(services_in.service_ids)
        ).delete(synchronize_session=False)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
