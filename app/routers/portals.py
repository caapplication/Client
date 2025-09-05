from typing import List
import uuid
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import SessionLocal
from ..dependencies import get_current_user
from ..security import has_role, Role

router = APIRouter()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.PortalRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(has_role([Role.SUPER_ADMIN, Role.AGENCY_ADMIN, Role.CA_ACCOUNTANT]))])
def create_portal(
    portal_in: schemas.PortalCreate,
    db: Session = Depends(get_db),
):
    db_portal = models.Portal(**portal_in.dict())
    db.add(db_portal)
    db.commit()
    db.refresh(db_portal)
    return db_portal

@router.get("/", response_model=List[schemas.PortalRead], dependencies=[Depends(has_role([Role.SUPER_ADMIN, Role.AGENCY_ADMIN, Role.CA_ACCOUNTANT, Role.CA_TEAM]))])
def list_portals(db: Session = Depends(get_db)):
    return db.query(models.Portal).all()

@router.delete("/{portal_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(has_role([Role.SUPER_ADMIN, Role.AGENCY_ADMIN, Role.CA_ACCOUNTANT]))])
def delete_portal(
    portal_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    db_portal = db.query(models.Portal).filter(models.Portal.id == portal_id).first()
    if db_portal is None:
        raise HTTPException(status_code=404, detail="Portal not found")
    db.delete(db_portal)
    db.commit()
