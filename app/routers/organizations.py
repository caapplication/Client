import uuid
import requests
from fastapi import APIRouter, Depends, status, HTTPException, Header, Form
from ..dependencies import get_current_user, http_bearer
import os

router = APIRouter()

LOGIN_API_URL = os.getenv("API_URL")

@router.get("/", status_code=status.HTTP_200_OK)
def list_organizations(
    user: dict = Depends(get_current_user),
    token: str = Depends(http_bearer),
):
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {token.credentials}",
    }
    try:
        response = requests.get(f"{LOGIN_API_URL}/organizations/", headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Error connecting to login API: {e}")
