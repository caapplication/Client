import os
import requests
import json

# --- Configuration ---
BASE_URL = "https://client-api.snolep.com"
# It's recommended to use environment variables for sensitive data like tokens
JWT_TOKEN = os.environ.get("JWT_TOKEN", "your_jwt_token_here")
CLIENT_ID = os.environ.get("CLIENT_ID", "your_client_id_here")
PORTAL_ID = os.environ.get("PORTAL_ID", "your_portal_id_here")

# --- Headers ---
headers = {
    "Authorization": f"Bearer {JWT_TOKEN}",
    "Content-Type": "application/json"
}

def print_response(response):
    """Helper function to print response status and JSON body."""
    print(f"Status Code: {response.status_code}")
    try:
        print("Response JSON:")
        print(json.dumps(response.json(), indent=2))
    except json.JSONDecodeError:
        print("Response Body (not JSON):")
        print(response.text)
    print("-" * 30)

def test_get_portal(step):
    """Tests the GET endpoint."""
    print(f"--- {step}: Testing GET /clients/{CLIENT_ID}/portals/{PORTAL_ID} ---")
    url = f"{BASE_URL}/clients/{CLIENT_ID}/portals/{PORTAL_ID}"
    response = requests.get(url, headers=headers)
    print_response(response)
    return response

def test_update_portal():
    """Tests the PATCH endpoint."""
    print(f"--- Testing PATCH /clients/{CLIENT_ID}/portals/{PORTAL_ID} ---")
    url = f"{BASE_URL}/clients/{CLIENT_ID}/portals/{PORTAL_ID}"
    payload = {
        "username": "updated_test_username",
        "password": "updated_test_password_123"
    }
    response = requests.patch(url, headers=headers, data=json.dumps(payload))
    print_response(response)
    return response

def test_delete_portal():
    """Tests the DELETE endpoint."""
    print(f"--- Testing DELETE /clients/{CLIENT_ID}/portals/{PORTAL_ID} ---")
    url = f"{BASE_URL}/clients/{CLIENT_ID}/portals/{PORTAL_ID}"
    response = requests.delete(url, headers=headers)
    print(f"Status Code: {response.status_code}")
    print("-" * 30)
    return response

if __name__ == "__main__":
    if "your_" in JWT_TOKEN or "your_" in CLIENT_ID or "your_" in PORTAL_ID:
        print("!!! WARNING: Please replace placeholder values for JWT_TOKEN, CLIENT_ID, and PORTAL_ID.")
        print("You can set them as environment variables or edit the script directly.")
    else:
        # 1. Get the initial state of the portal
        test_get_portal("Step 1: Initial Fetch")

        # 2. Update the portal
        test_update_portal()

        # 3. Get the updated state to verify the patch
        test_get_portal("Step 3: Fetch After Update")

        # 4. Delete the portal
        test_delete_portal()

        # 5. Try to get the portal again (should fail with 404)
        test_get_portal("Step 5: Fetch After Delete (Expect 404)")
