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

def test_create_tag():
    print("\nTesting POST /settings/tags")
    data = {"name": f"Test Tag {uuid.uuid4()}", "color": "#FF0000"}
    response = requests.post(f"{BASE_URL}/settings/tags", headers=HEADERS, json=data)
    print_curl_and_response(response)
    assert response.status_code == 201
    return response.json()["id"]

def test_list_organizations():
    print("\nTesting GET /organizations/")
    response = requests.get(f"{BASE_URL}/organizations/", headers=HEADERS)
    print_curl_and_response(response)
    assert response.status_code == 200
    return response.json()

def test_create_client_with_tag(organization_id, tag_id):
    print("\nTesting POST /clients/ with a tag")
    data = {
        "is_active": "true",
        "name": f"demo-client-with-tag-{uuid.uuid4()}",
        "client_type": "ngo",
        "opening_balance_amount": "0",
        "organization_id": organization_id,
        "tag_ids": [tag_id],
    }
    files = {'photo': ('', b'')}
    post_headers = HEADERS.copy()
    if 'Content-Type' in post_headers:
        del post_headers['Content-Type']
    response = requests.post(f"{BASE_URL}/clients/", headers=post_headers, data=data, files=files)
    print_curl_and_response(response)
    assert response.status_code == 201
    print("\nClient created successfully with the tag.")
    return response.json()["id"]

if __name__ == "__main__":
    login()

    # 1. Create a new tag
    tag_id = test_create_tag()

    # 2. Get an organization to associate the client with
    organizations = test_list_organizations()
    if not organizations:
        print("No organizations found. Cannot create a client.")
        exit(1)
    organization_id = organizations[0]["id"]

    # 3. Create a client and attach the tag
    client_id = test_create_client_with_tag(organization_id, tag_id)

    print(f"\nTest finished. Created client {client_id} with tag {tag_id}.")
