from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer
import requests
import uuid
from json import JSONDecodeError
import os
from dotenv import load_dotenv

from . import schemas

load_dotenv()

LOGIN_SERVICE_URL = os.getenv("API_URL")
http_bearer = HTTPBearer()

def get_current_user(
    token: str = Depends(http_bearer), x_agency_id: str = Header(None)
):
    try:
        headers = {
            "Authorization": f"Bearer {token.credentials}",
            "accept": "application/json",
        }
        if x_agency_id:
            headers["x-agency-id"] = x_agency_id
        response = requests.get(f"{LOGIN_SERVICE_URL}/profile", headers=headers)
        response.raise_for_status()
        user_data = response.json()
        return user_data
    except requests.exceptions.HTTPError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Error connecting to authentication service: {e}",
        )
    except JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invalid response from authentication service",
        )

def get_current_agency(
    x_agency_id: uuid.UUID = Header(...),
    current_user: dict = Depends(get_current_user),
):
    # This is a simplified version. In a real application, you would
    # probably have a more robust way to check agency membership.
    # For now, we will just assume that if the user is authenticated,
    # they have access to the agency.
    return {"id": x_agency_id}
