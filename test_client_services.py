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

def test_list_external_services():
    print("\nTesting GET /services/")
    response = requests.get(f"{BASE_URL}/services/", headers=HEADERS)
    print_curl_and_response(response)
    assert response.status_code == 200
    return response.json()

def test_list_organizations():
    print("\nTesting GET /organizations/")
    response = requests.get(f"{BASE_URL}/organizations/", headers=HEADERS)
    print_curl_and_response(response)
    assert response.status_code == 200
    return response.json()

def test_create_client(organization_id):
    print("\nTesting POST /clients/")
    data = {
        "is_active": "true",
        "name": f"demo-client-with-service-{uuid.uuid4()}",
        "client_type": "ngo",
        "opening_balance_amount": "0",
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

def test_add_service_to_client(client_id, service_id):
    print(f"\nTesting POST /services/{client_id}/services")
    data = {
        "service_id": service_id,
    }
    response = requests.post(f"{BASE_URL}/services/{client_id}/services", headers=HEADERS, json=data)
    print_curl_and_response(response)
    assert response.status_code == 201
    print(f"\nService {service_id} added to client {client_id} successfully.")

if __name__ == "__main__":
    login()

    # 1. List external services
    services = test_list_external_services()
    if not services:
        print("No services found. Cannot attach a service to a client.")
        exit(1)
    service_id = services[0]["id"]

    # 2. Get an organization to associate the client with
    organizations = test_list_organizations()
    if not organizations:
        print("No organizations found. Cannot create a client.")
        exit(1)
    organization_id = organizations[0]["id"]

    # 3. Create a client
    client_id = test_create_client(organization_id)

    # 4. Add a service to the client
    test_add_service_to_client(client_id, service_id)

    print(f"\nTest finished. Attached service {service_id} to client {client_id}.")
