from typing import List
import uuid
import os
from fastapi import APIRouter, Depends, status, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import SessionLocal
from ..dependencies import get_current_user, get_current_agency
from ..utils.s3 import upload_file_to_s3, delete_file_from_s3, get_file_from_s3, get_presigned_url
from fastapi.responses import StreamingResponse, RedirectResponse
from fastapi.responses import StreamingResponse
import shutil

router = APIRouter()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

import os
from fastapi import Form, HTTPException

@router.post("/", response_model=schemas.ClientRead, status_code=status.HTTP_201_CREATED)
def create_client(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    current_agency: dict = Depends(get_current_agency),
    photo: UploadFile = File(None),
    is_active: bool = Form(True),
    name: str = Form(...),
    client_type: str = Form(...),
    organization_id: uuid.UUID = Form(None),
    pan: str = Form(None),
    gstin: str = Form(None),
    contact_person_name: str = Form(None),
    date_of_birth: str = Form(None),
    user_ids: List[uuid.UUID] = Form([]),
    assigned_ca_user_id: uuid.UUID = Form(None),
    tag_ids: List[uuid.UUID] = Form([]),
    mobile: str = Form(None),
    secondary_phone: str = Form(None),
    email: str = Form(None),
    address_line1: str = Form(None),
    address_line2: str = Form(None),
    city: str = Form(None),
    postal_code: str = Form(None),
    state: str = Form(None),
    opening_balance_date: str = Form(None),
    opening_balance_amount: float = Form(0.0),
    opening_balance_type: str = Form(None),
):
    user_id = current_user.get("id")
    agency_id = current_agency.get("id")

    # Handle file upload
    if photo and photo.filename:
        # You would typically save the file to a designated folder and store the path in the database.
        # For this example, we'll just print the filename.
        os.makedirs("uploads", exist_ok=True)
        with open(f"uploads/{photo.filename}", "wb") as buffer:
            shutil.copyfileobj(photo.file, buffer)
        # You would save the file path to the client model here.

    # Generate a unique customer ID
    # This is a simplified example. You would likely have a more robust system for this.
    customer_id = f"CUST-{uuid.uuid4().hex[:6].upper()}"

    # Check for duplicates
    general_setting = db.query(models.GeneralSetting).first()
    if general_setting and not general_setting.allow_duplicates:
        existing_client = db.query(models.Client).filter(models.Client.name == name).first()
        if existing_client:
            raise HTTPException(status_code=400, detail="Client with this name already exists.")

    client_data = schemas.ClientCreate(
        is_active=is_active,
        name=name,
        client_type=client_type.lower(),
        organization_id=organization_id,
        pan=pan,
        gstin=gstin,
        contact_person_name=contact_person_name,
        date_of_birth=date_of_birth,
        user_ids=user_ids,
        assigned_ca_user_id=assigned_ca_user_id,
        tag_ids=tag_ids,
        mobile=mobile,
        secondary_phone=secondary_phone,
        email=email,
        address_line1=address_line1,
        address_line2=address_line2,
        city=city,
        postal_code=postal_code,
        state=state,
        opening_balance_date=opening_balance_date,
        opening_balance_amount=opening_balance_amount,
        opening_balance_type=opening_balance_type,
    )
    
    client_dict = client_data.dict()
    user_ids_list = client_dict.pop("user_ids", [])
    tag_ids_list = client_dict.pop("tag_ids", [])

    db_client = models.Client(
        **client_dict,
        created_by=user_id,
        agency_id=agency_id,
        customer_id=customer_id,
    )

    if user_ids_list:
        users = db.query(models.User).filter(models.User.id.in_(user_ids_list)).all()
        if len(users) != len(user_ids_list):
            raise HTTPException(status_code=404, detail="One or more users not found")
        db_client.users = users

    if tag_ids_list:
        tags = db.query(models.Tag).filter(models.Tag.id.in_(tag_ids_list)).all()
        if len(tags) != len(tag_ids_list):
            raise HTTPException(status_code=404, detail="One or more tags not found")
        db_client.tags = tags

    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    
    # Create activity log in Finance service
    try:
        import requests
        import os
        finance_api_url = os.getenv("FINANCE_API_URL", "http://finance:8003")
        activity_log_data = {
            "user_id": str(user_id),
            "action": f"Created client {db_client.name}",
            "details": f"Client {db_client.name} (ID: {db_client.id}) was created",
            "client_id": str(db_client.id)
        }
        # Note: This requires authentication token to be passed or service-to-service auth
        # For now, we'll skip if it fails (non-blocking)
        try:
            requests.post(
                f"{finance_api_url}/api/activity_logs/",
                json=activity_log_data,
                timeout=2
            )
        except Exception:
            pass  # Non-blocking - activity log creation failure shouldn't break client creation
    except Exception:
        pass  # Non-blocking
    
    return db_client

@router.get("/", response_model=List[schemas.ClientRead])
def list_clients(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    current_agency: dict = Depends(get_current_agency),
):
    agency_id = current_agency.get("id")
    return db.query(models.Client).filter(models.Client.agency_id == agency_id).all()

@router.post("/{client_id}/portals", response_model=schemas.ClientPortalRead, status_code=status.HTTP_201_CREATED)
def create_client_portal(
    client_id: uuid.UUID,
    portal_in: schemas.ClientPortalCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    client = db.query(models.Client).filter(models.Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    user_id = current_user.get("id")
    portal_data = portal_in.dict()
    portal_data["username_cipher"] = portal_data.pop("username")
    portal_data["password_cipher"] = portal_data.pop("password")
    portal_data["notes_cipher"] = portal_data.pop("notes")
    db_client_portal = models.ClientPortal(
        **portal_data, client_id=client_id, created_by=user_id
    )
    db.add(db_client_portal)
    db.commit()
    db.refresh(db_client_portal)
    return db_client_portal

@router.patch("/{client_id}/portals/{portal_id}", response_model=schemas.ClientPortalRead)
def update_client_portal(
    client_id: uuid.UUID,
    portal_id: uuid.UUID,
    portal_in: schemas.ClientPortalUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    db_client_portal = db.query(models.ClientPortal).filter(
        models.ClientPortal.client_id == client_id,
        models.ClientPortal.id == portal_id,
    ).first()
    if db_client_portal is None:
        raise HTTPException(status_code=404, detail="Client portal not found")

    update_data = portal_in.dict(exclude_unset=True)
    if "username" in update_data:
        update_data["username_cipher"] = update_data.pop("username")
    if "password" in update_data:
        update_data["password_cipher"] = update_data.pop("password")
    if "notes" in update_data:
        update_data["notes_cipher"] = update_data.pop("notes")

    for key, value in update_data.items():
        setattr(db_client_portal, key, value)

    db.commit()
    db.refresh(db_client_portal)
    return db_client_portal

@router.get("/{client_id}/portals", response_model=List[schemas.ClientPortalWithSecrets])
def list_client_portals(
    client_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return db.query(models.ClientPortal).filter(models.ClientPortal.client_id == client_id).all()


@router.get("/{client_id}/portals/{portal_id}", response_model=schemas.ClientPortalWithSecrets)
def get_client_portal(
    client_id: uuid.UUID,
    portal_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    db_client_portal = db.query(models.ClientPortal).filter(
        models.ClientPortal.client_id == client_id,
        models.ClientPortal.id == portal_id,
    ).first()
    if db_client_portal is None:
        raise HTTPException(status_code=404, detail="Client portal not found")
    return db_client_portal


@router.delete("/{client_id}/portals/{portal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client_portal(
    client_id: uuid.UUID,
    portal_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    db_client_portal = db.query(models.ClientPortal).filter(
        models.ClientPortal.client_id == client_id,
        models.ClientPortal.id == portal_id,
    ).first()
    if db_client_portal is None:
        raise HTTPException(status_code=404, detail="Client portal not found")
    db.delete(db_client_portal)
    db.commit()

@router.patch("/{client_id}", response_model=schemas.ClientRead)
def update_client(
    client_id: uuid.UUID,
    client_in: schemas.ClientUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    current_agency: dict = Depends(get_current_agency),
):
    db_client = db.query(models.Client).filter(models.Client.id == client_id).first()
    if db_client is None:
        raise HTTPException(status_code=404, detail="Client not found")

    update_data = client_in.dict(exclude_unset=True)
    
    # Helper function to format values for display
    def format_value(val):
        if val is None:
            return 'None'
        if isinstance(val, bool):
            return 'Yes' if val else 'No'
        if isinstance(val, list):
            if not val:
                return 'None'
            return ', '.join(str(v) for v in val)
        if isinstance(val, uuid.UUID):
            return str(val)
        # Check if it's a date/datetime
        if hasattr(val, 'isoformat'):
            try:
                return val.isoformat().split('T')[0]  # Just the date part
            except:
                return str(val)
        return str(val)
    
    # Track old values before updating
    changed_fields_details = []
    
    for key, value in update_data.items():
        # Get old value before updating
        old_value = getattr(db_client, key, None)
        
        # Format values for display
        old_formatted = format_value(old_value)
        new_formatted = format_value(value)
        
        # Only track if value actually changed (compare formatted strings)
        if old_formatted != new_formatted:
            # Use human-readable field names
            field_display = key.replace('_', ' ').title()
            changed_fields_details.append(f"{field_display}: '{old_formatted}' → '{new_formatted}'")
        
        setattr(db_client, key, value)

    db.commit()
    db.refresh(db_client)
    
    # Create activity log in Finance service
    try:
        import requests
        import os
        finance_api_url = os.getenv("FINANCE_API_URL", "http://finance:8003")
        user_id = current_user.get("id")
        
        # Build details with old → new values
        if changed_fields_details:
            details = f"Client {db_client.name} (ID: {db_client.id}) was updated. Changes: {'; '.join(changed_fields_details)}"
        else:
            details = f"Client {db_client.name} (ID: {db_client.id}) was updated."
        
        activity_log_data = {
            "user_id": str(user_id),
            "action": f"Updated client {db_client.name}",
            "details": details,
            "client_id": str(db_client.id)
        }
        try:
            requests.post(
                f"{finance_api_url}/api/activity_logs/",
                json=activity_log_data,
                timeout=2
            )
        except Exception:
            pass  # Non-blocking
    except Exception:
        pass  # Non-blocking
    
    return db_client

@router.get("/{client_id}/dashboard", response_model=schemas.ClientDashboard)
def get_client_dashboard(
    client_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    current_agency: dict = Depends(get_current_agency),
):
    db_client = db.query(models.Client).filter(models.Client.id == client_id).first()
    if db_client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    return db_client

@router.post("/invites/organization-user", status_code=status.HTTP_204_NO_CONTENT)
def invite_organization_user(
    invite_in: schemas.InviteUser,
    current_user: dict = Depends(get_current_user),
    current_agency: dict = Depends(get_current_agency),
):
    # This is a placeholder for the actual invite logic.
    # You would typically make a request to the login service here.
    print(f"Inviting {invite_in.email} to organization {invite_in.org_id}")
    return

@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client(
    client_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    current_agency: dict = Depends(get_current_agency),
):
    db_client = db.query(models.Client).filter(models.Client.id == client_id).first()
    if db_client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    
    client_name = db_client.name
    client_id_str = str(db_client.id)
    
    db.delete(db_client)
    db.commit()
    
    # Create activity log in Finance service
    try:
        import requests
        import os
        finance_api_url = os.getenv("FINANCE_API_URL", "http://finance:8003")
        user_id = current_user.get("id")
        activity_log_data = {
            "user_id": str(user_id),
            "action": f"Deleted client {client_name}",
            "details": f"Client {client_name} (ID: {client_id_str}) was deleted",
            "client_id": client_id_str
        }
        try:
            requests.post(
                f"{finance_api_url}/api/activity_logs/",
                json=activity_log_data,
                timeout=2
            )
        except Exception:
            pass  # Non-blocking
    except Exception:
        pass  # Non-blocking

@router.get("/{client_id}/ledger-balance", response_model=schemas.LedgerBalance)
def get_ledger_balance(
    client_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    current_agency: dict = Depends(get_current_agency),
):
    db_client = db.query(models.Client).filter(models.Client.id == client_id).first()
    if db_client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    return db_client

@router.post("/{client_id}/photo", status_code=status.HTTP_200_OK)
def upload_client_photo(
    client_id: uuid.UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    current_agency: dict = Depends(get_current_agency),
):
    """
    Endpoint to upload a photo for a client.
    """
    db_client = db.query(models.Client).filter(models.Client.id == client_id).first()
    if db_client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded or file has no name.")

    _, file_extension = os.path.splitext(file.filename)
    object_name = f"clients/{client_id}{file_extension}"

    try:
        # Delete old photo if exists
        if db_client.photo_url:
            # Extract object name from URL (format: https://bucket.s3.amazonaws.com/object_name)
            try:
                old_object_name = db_client.photo_url.split('.s3.amazonaws.com/')[-1]
                delete_file_from_s3(old_object_name)
            except Exception:
                pass  # Ignore errors when deleting old photo
        
        photo_url = upload_file_to_s3(file, object_name)
        db_client.photo_url = photo_url
        db.commit()
        db.refresh(db_client)
        return {"message": "Client photo updated successfully", "photo_url": photo_url}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred during S3 upload: {e}")

@router.delete("/{client_id}/photo", status_code=status.HTTP_200_OK)
def delete_client_photo(
    client_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    current_agency: dict = Depends(get_current_agency),
):
    """
    Endpoint to delete the photo for a client.
    """
    db_client = db.query(models.Client).filter(models.Client.id == client_id).first()
    if db_client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    
    if not db_client.photo_url:
        raise HTTPException(status_code=404, detail="No client photo to delete.")
    
    try:
        # Extract object name from URL (format: https://bucket.s3.amazonaws.com/object_name)
        object_name = db_client.photo_url.split('.s3.amazonaws.com/')[-1]
        delete_file_from_s3(object_name)
        db_client.photo_url = None
        db.commit()
        db.refresh(db_client)
        return {"message": "Client photo deleted successfully"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred during S3 deletion: {e}")

@router.get("/{client_id}/photo", status_code=status.HTTP_302_FOUND)
def get_client_photo(
    client_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    current_agency: dict = Depends(get_current_agency),
):
    """
    Endpoint to serve client photo from S3 with authentication via a presigned URL.
    """
    db_client = db.query(models.Client).filter(models.Client.id == client_id).first()
    if db_client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    
    if not db_client.photo_url:
        raise HTTPException(status_code=404, detail="No client photo available.")
    
    try:
        # Extract object name from URL (format: https://bucket.s3.amazonaws.com/object_name)
        object_name = db_client.photo_url.split('.s3.amazonaws.com/')[-1]
        presigned_url = get_presigned_url(object_name, expiration=3600)  # URL valid for 1 hour
        
        # Redirect to the presigned URL
        return RedirectResponse(url=presigned_url, status_code=status.HTTP_302_FOUND)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred during S3 access: {e}")
