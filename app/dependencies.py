from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer
import requests
import uuid
from json import JSONDecodeError
import os
from dotenv import load_dotenv

from . import schemas

load_dotenv()

# Get Login service URL - use local service for development, fallback to env variable
LOGIN_SERVICE_URL = os.getenv("API_URL") or "http://login:8001"
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
        # Use /profile/ with trailing slash to match the router prefix
        profile_url = f"{LOGIN_SERVICE_URL}/profile/" if not LOGIN_SERVICE_URL.endswith('/') else f"{LOGIN_SERVICE_URL}profile/"
        response = requests.get(profile_url, headers=headers, timeout=10)
        response.raise_for_status()
        user_data = response.json()
        return user_data
    except requests.exceptions.HTTPError as e:
        error_detail = f"Invalid authentication credentials"
        try:
            error_response = e.response.json() if e.response else {}
            error_detail = error_response.get('detail', error_detail)
        except:
            pass
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_detail,
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
