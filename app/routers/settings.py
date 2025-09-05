from typing import List
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import SessionLocal
from ..dependencies import get_current_user, get_current_agency
from ..security import has_role, Role

router = APIRouter()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/general", response_model=schemas.GeneralSettingRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(has_role([Role.SUPER_ADMIN, Role.AGENCY_ADMIN, Role.CA_ACCOUNTANT]))])
def create_general_setting(
    setting_in: schemas.GeneralSettingCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    current_agency: dict = Depends(get_current_agency),
):
    user_id = current_user.get("id")
    agency_id = current_agency.get("id")
    
    existing_setting = db.query(models.GeneralSetting).filter(models.GeneralSetting.agency_id == agency_id).first()
    if existing_setting:
        raise HTTPException(status_code=409, detail="General setting for this agency already exists.")

    db_setting = models.GeneralSetting(
        **setting_in.dict(), agency_id=agency_id, created_by=user_id
    )
    db.add(db_setting)
    db.commit()
    db.refresh(db_setting)
    return db_setting

@router.get("/general", response_model=List[schemas.GeneralSettingRead], dependencies=[Depends(has_role([Role.SUPER_ADMIN, Role.AGENCY_ADMIN, Role.CA_ACCOUNTANT, Role.CA_TEAM]))])
def list_general_settings(db: Session = Depends(get_db)):
    return db.query(models.GeneralSetting).all()

@router.patch("/general/{setting_id}", response_model=schemas.GeneralSettingRead, dependencies=[Depends(has_role([Role.SUPER_ADMIN, Role.AGENCY_ADMIN, Role.CA_ACCOUNTANT]))])
def update_general_setting(
    setting_id: uuid.UUID,
    setting_in: schemas.GeneralSettingUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    db_setting = db.query(models.GeneralSetting).filter(models.GeneralSetting.id == setting_id).first()
    if db_setting is None:
        raise HTTPException(status_code=404, detail="Setting not found")

    update_data = setting_in.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_setting, key, value)

    db.commit()
    db.refresh(db_setting)
    return db_setting

@router.delete("/general/{setting_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(has_role([Role.SUPER_ADMIN, Role.AGENCY_ADMIN, Role.CA_ACCOUNTANT]))])
def delete_general_setting(
    setting_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    db_setting = db.query(models.GeneralSetting).filter(models.GeneralSetting.id == setting_id).first()
    if db_setting is None:
        raise HTTPException(status_code=404, detail="Setting not found")
    db.delete(db_setting)
    db.commit()

@router.post("/tags", response_model=schemas.TagRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(has_role([Role.SUPER_ADMIN, Role.AGENCY_ADMIN, Role.CA_ACCOUNTANT]))])
def create_tag(
    tag_in: schemas.TagCreate,
    db: Session = Depends(get_db),
):
    db_tag = models.Tag(**tag_in.dict())
    db.add(db_tag)
    db.commit()
    db.refresh(db_tag)
    return db_tag

@router.get("/tags", response_model=List[schemas.TagRead], dependencies=[Depends(has_role([Role.SUPER_ADMIN, Role.AGENCY_ADMIN, Role.CA_ACCOUNTANT, Role.CA_TEAM]))])
def list_tags(db: Session = Depends(get_db)):
    return db.query(models.Tag).all()

@router.patch("/tags/{tag_id}", response_model=schemas.TagRead, dependencies=[Depends(has_role([Role.SUPER_ADMIN, Role.AGENCY_ADMIN, Role.CA_ACCOUNTANT]))])
def update_tag(
    tag_id: uuid.UUID,
    tag_in: schemas.TagUpdate,
    db: Session = Depends(get_db),
):
    db_tag = db.query(models.Tag).filter(models.Tag.id == tag_id).first()
    if db_tag is None:
        raise HTTPException(status_code=404, detail="Tag not found")

    update_data = tag_in.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_tag, key, value)

    db.commit()
    db.refresh(db_tag)
    return db_tag

@router.delete("/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(has_role([Role.SUPER_ADMIN, Role.AGENCY_ADMIN, Role.CA_ACCOUNTANT]))])
def delete_tag(
    tag_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    db_tag = db.query(models.Tag).filter(models.Tag.id == tag_id).first()
    if db_tag is None:
        raise HTTPException(status_code=404, detail="Tag not found")
    db.delete(db_tag)
    db.commit()

@router.post("/business-types", response_model=schemas.BusinessTypeRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(has_role([Role.SUPER_ADMIN, Role.AGENCY_ADMIN, Role.CA_ACCOUNTANT]))])
def create_business_type(
    business_type_in: schemas.BusinessTypeCreate,
    db: Session = Depends(get_db),
):
    db_business_type = models.BusinessType(**business_type_in.dict())
    db.add(db_business_type)
    db.commit()
    db.refresh(db_business_type)
    return db_business_type

@router.get("/business-types", response_model=List[schemas.BusinessTypeRead], dependencies=[Depends(has_role([Role.SUPER_ADMIN, Role.AGENCY_ADMIN, Role.CA_ACCOUNTANT, Role.CA_TEAM]))])
def list_business_types(db: Session = Depends(get_db)):
    return db.query(models.BusinessType).all()

@router.patch("/business-types/{business_type_id}", response_model=schemas.BusinessTypeRead, dependencies=[Depends(has_role([Role.SUPER_ADMIN, Role.AGENCY_ADMIN, Role.CA_ACCOUNTANT]))])
def update_business_type(
    business_type_id: uuid.UUID,
    business_type_in: schemas.BusinessTypeUpdate,
    db: Session = Depends(get_db),
):
    db_business_type = db.query(models.BusinessType).filter(models.BusinessType.id == business_type_id).first()
    if db_business_type is None:
        raise HTTPException(status_code=404, detail="Business type not found")

    update_data = business_type_in.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_business_type, key, value)

    db.commit()
    db.refresh(db_business_type)
    return db_business_type

@router.delete("/business-types/{business_type_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(has_role([Role.SUPER_ADMIN, Role.AGENCY_ADMIN, Role.CA_ACCOUNTANT]))])
def delete_business_type(
    business_type_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    db_business_type = db.query(models.BusinessType).filter(models.BusinessType.id == business_type_id).first()
    if db_business_type is None:
        raise HTTPException(status_code=404, detail="Business type not found")
    db.delete(db_business_type)
    db.commit()
