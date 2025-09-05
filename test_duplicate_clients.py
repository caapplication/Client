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

def set_general_setting(allow_duplicates: bool):
    print(f"\nSetting allow_duplicates to {allow_duplicates}")
    data = {"allow_duplicates": allow_duplicates}
    response = requests.post(f"{BASE_URL}/settings/general", headers=HEADERS, json=data)
    if response.status_code == 409: # Setting already exists
        response = requests.get(f"{BASE_URL}/settings/general", headers=HEADERS)
        setting_id = response.json()[0]["id"]
        response = requests.patch(f"{BASE_URL}/settings/general/{setting_id}", headers=HEADERS, json=data)
    print_curl_and_response(response)
    assert response.status_code == 200 or response.status_code == 201

def test_create_client(organization_id, name):
    print(f"\nTesting POST /clients/ with name '{name}'")
    data = {
        "is_active": "true",
        "name": name,
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
    return response

def test_list_organizations():
    print("\nTesting GET /organizations/")
    response = requests.get(f"{BASE_URL}/organizations/", headers=HEADERS)
    print_curl_and_response(response)
    assert response.status_code == 200
    return response.json()

if __name__ == "__main__":
    login()

    organizations = test_list_organizations()
    organization_id = organizations[0]["id"]
    client_name = f"duplicate-client-test-{uuid.uuid4()}"

    # Test case 1: allow_duplicates = True
    set_general_setting(True)
    response1 = test_create_client(organization_id, client_name)
    assert response1.status_code == 201
    response2 = test_create_client(organization_id, client_name)
    assert response2.status_code == 201
    print("\nSuccessfully created duplicate clients when allow_duplicates is True.")

    # Test case 2: allow_duplicates = False
    set_general_setting(False)
    response3 = test_create_client(organization_id, f"unique-client-{uuid.uuid4()}")
    assert response3.status_code == 201
    response4 = test_create_client(organization_id, response3.json()["name"])
    assert response4.status_code == 400
    print("\nSuccessfully prevented duplicate clients when allow_duplicates is False.")
