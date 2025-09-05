import requests
import uuid
import os
import json

# --- Configuration ---
BASE_URL = "http://127.0.0.1:8002"
LOGIN_URL = "https://login-api.snolep.com/login/"
EMAIL = "democaadmin@yopmail.com"
PASSWORD = "demo@1234"

ACCESS_TOKEN = None
AGENCY_ID = None
HEADERS = {}

def login():
    global ACCESS_TOKEN, AGENCY_ID, HEADERS
    print("Attempting to log in...")
    data = {"email": EMAIL, "password": PASSWORD}
    response = requests.post(LOGIN_URL, data=data)
    if response.status_code == 200:
        json_response = response.json()
        ACCESS_TOKEN = json_response.get("access_token")
        AGENCY_ID = json_response.get("agency_id")
        HEADERS.update({
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "accept": "application/json",
            "x-agency-id": str(AGENCY_ID),
        })
        print("Login successful.")
    else:
        print(f"Login failed with status code {response.status_code}: {response.text}")
        exit(1)

def print_curl_and_response(response):
    print(f"\n--- Testing {response.request.method} {response.request.url} ---")
    print("\n--- cURL Command ---")
    method = response.request.method
    uri = response.request.url
    headers = " ".join([f"-H '{k}: {v}'" for k, v in response.request.headers.items()])
    body = response.request.body.decode('utf-8') if response.request.body else ""
    print(f"curl -X '{method}' '{uri}' {headers} -d '{body}'")
    print("\n--- Server Response ---")
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response: {response.json()}")
    except json.JSONDecodeError:
        print(f"Response text: {response.text}")

def test_create_portal():
    data = {"name": f"Test Portal {uuid.uuid4()}", "login_url": "https://example.com"}
    response = requests.post(f"{BASE_URL}/portals/", headers=HEADERS, json=data)
    print_curl_and_response(response)
    assert response.status_code == 201
    return response.json()["id"]

def test_list_portals():
    response = requests.get(f"{BASE_URL}/portals/", headers=HEADERS)
    print_curl_and_response(response)
    assert response.status_code == 200

def test_delete_portal(portal_id):
    response = requests.delete(f"{BASE_URL}/portals/{portal_id}", headers=HEADERS)
    print_curl_and_response(response)
    assert response.status_code == 204

def test_create_client(organization_id):
    data = {
        "is_active": "true",
        "name": f"demo-client-for-portal-test-{uuid.uuid4()}",
        "client_type": "ngo",
        "organization_id": organization_id,
    }
    files = {'photo': ('', b'')}
    post_headers = HEADERS.copy()
    if 'Content-Type' in post_headers:
        del post_headers['Content-Type']
    response = requests.post(f"{BASE_URL}/clients/", headers=post_headers, data=data, files=files)
    print_curl_and_response(response)
    assert response.status_code == 201
    return response.json()["id"]

def test_create_client_portal(client_id, portal_id):
    data = {
        "portal_id": portal_id,
        "username": "initial_username",
        "password": "initial_password",
        "notes": "Initial notes"
    }
    response = requests.post(f"{BASE_URL}/clients/{client_id}/portals", headers=HEADERS, json=data)
    print_curl_and_response(response)
    assert response.status_code == 201

def test_list_client_portals(client_id):
    response = requests.get(f"{BASE_URL}/clients/{client_id}/portals", headers=HEADERS)
    print_curl_and_response(response)
    assert response.status_code == 200
    assert len(response.json()) > 0

def test_update_client_portal(client_id, portal_id):
    data = {
        "username": "updated_username",
        "password": "updated_password",
        "notes": "Updated notes"
    }
    response = requests.patch(f"{BASE_URL}/clients/{client_id}/portals/{portal_id}", headers=HEADERS, json=data)
    print_curl_and_response(response)
    assert response.status_code == 200

def test_delete_client_portal(client_id, portal_id):
    response = requests.delete(f"{BASE_URL}/clients/{client_id}/portals/{portal_id}", headers=HEADERS)
    print_curl_and_response(response)
    assert response.status_code == 204

def test_list_organizations():
    response = requests.get(f"{BASE_URL}/organizations/", headers=HEADERS)
    print_curl_and_response(response)
    assert response.status_code == 200
    return response.json()

if __name__ == "__main__":
    login()

    # Portal Management
    portal_id = test_create_portal()
    test_list_portals()

    # Client and Client-Portal Management
    client_id = "f4662887-f1d0-4205-aa6d-91874f4c208a"
    
    test_create_client_portal(client_id, portal_id)
    test_list_client_portals(client_id)
    test_update_client_portal(client_id, portal_id)
    test_delete_client_portal(client_id, portal_id)

    # Cleanup
    test_delete_portal(portal_id)

    print("\nFull portal lifecycle test completed successfully.")
