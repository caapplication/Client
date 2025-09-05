import requests
import json
import uuid

# --- Configuration ---
BASE_URL = "http://127.0.0.1:8002"
LOGIN_URL = "https://login-api.snolep.com/login"
EMAIL = "democaadmin@yopmail.com"
PASSWORD = "demo@1234"

ACCESS_TOKEN = None
AGENCY_ID = None

HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "X-Agency-Id": f"{AGENCY_ID}"
}

# --- Test Data ---
setting_id = None
tag_id = None
tag_name = f"Test Tag {uuid.uuid4().hex[:6]}"
tag_color = "blue"

def print_curl_command(method, url, headers, data=None):
    """Prints the curl command for a request."""
    command = f"curl -X {method} '{url}'"
    for key, value in headers.items():
        command += f" -H '{key}: {value}'"
    if data:
        command += " -d '"
        command += "&".join([f"{key}={value}" for key, value in data.items()])
        command += "'"
    print("--- CURL Command ---")
    print(command)
    print("--------------------")

def print_response(response, test_name):
    """Helper function to print test results."""
    print(f"--- {test_name} ---")
    print(f"Status Code: {response.status_code}")
    if response.text:
        try:
            print("Response JSON:")
            print(json.dumps(response.json(), indent=2))
        except json.JSONDecodeError:
            print("Response Text:")
            print(response.text)
    else:
        print("Response Body: (No Content)")
    print("-" * (len(test_name) + 8))
    print()

def get_access_token():
    """Fetches a new access token."""
    global ACCESS_TOKEN, AGENCY_ID, HEADERS
    print("--- Fetching Access Token ---")
    payload = {
        "email": EMAIL,
        "password": PASSWORD
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    response = requests.post(LOGIN_URL, data=payload, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        ACCESS_TOKEN = data.get("access_token")
        AGENCY_ID = data.get("agency_id")
        HEADERS["Authorization"] = f"Bearer {ACCESS_TOKEN}"
        HEADERS["X-Agency-Id"] = AGENCY_ID
        print("Successfully fetched new access token.")
        print("-" * 29)
        print()
        return True
    else:
        print("Failed to fetch access token.")
        print_response(response, "Login")
        return False

def test_create_general_setting():
    """Tests the POST /settings/general endpoint."""
    global setting_id
    print("Running: Create General Setting Test")
    payload = {
        "allow_duplicates": True
    }
    print_curl_command("POST", f"{BASE_URL}/settings/general", HEADERS, payload)
    response = requests.post(f"{BASE_URL}/settings/general", headers=HEADERS, json=payload)
    print_response(response, "Create General Setting")
    if response.status_code == 201:
        setting_id = response.json().get("id")
    return response.ok

def test_list_general_settings():
    """Tests the GET /settings/general endpoint."""
    print("Running: List General Settings Test")
    print_curl_command("GET", f"{BASE_URL}/settings/general", HEADERS)
    response = requests.get(f"{BASE_URL}/settings/general", headers=HEADERS)
    print_response(response, "List General Settings")
    return response.ok

def test_update_general_setting():
    """Tests the PATCH /settings/general/{setting_id} endpoint."""
    if not setting_id:
        print("Skipping Update General Setting Test: setting_id not available.")
        return False
    print(f"Running: Update General Setting Test (ID: {setting_id})")
    payload = {
        "allow_duplicates": False
    }
    print_curl_command("PATCH", f"{BASE_URL}/settings/general/{setting_id}", HEADERS, payload)
    response = requests.patch(f"{BASE_URL}/settings/general/{setting_id}", headers=HEADERS, json=payload)
    print_response(response, "Update General Setting")
    return response.ok

def test_create_tag():
    """Tests the POST /settings/tags endpoint."""
    global tag_id
    print("Running: Create Tag Test")
    payload = {
        "name": tag_name,
        "color": tag_color
    }
    print_curl_command("POST", f"{BASE_URL}/settings/tags", HEADERS, payload)
    response = requests.post(f"{BASE_URL}/settings/tags", headers=HEADERS, json=payload)
    print_response(response, "Create Tag")
    if response.status_code == 201:
        tag_id = response.json().get("id")
    return response.ok

def test_list_tags():
    """Tests the GET /settings/tags endpoint."""
    print("Running: List Tags Test")
    print_curl_command("GET", f"{BASE_URL}/settings/tags", HEADERS)
    response = requests.get(f"{BASE_URL}/settings/tags", headers=HEADERS)
    print_response(response, "List Tags")
    return response.ok

def test_update_tag():
    """Tests the PATCH /settings/tags/{tag_id} endpoint."""
    if not tag_id:
        print("Skipping Update Tag Test: tag_id not available.")
        return False
    print(f"Running: Update Tag Test (ID: {tag_id})")
    payload = {
        "name": f"{tag_name} (Updated)",
        "color": "red"
    }
    print_curl_command("PATCH", f"{BASE_URL}/settings/tags/{tag_id}", HEADERS, payload)
    response = requests.patch(f"{BASE_URL}/settings/tags/{tag_id}", headers=HEADERS, json=payload)
    print_response(response, "Update Tag")
    return response.ok

def test_delete_tag():
    """Tests the DELETE /settings/tags/{tag_id} endpoint."""
    if not tag_id:
        print("Skipping Delete Tag Test: tag_id not available.")
        return False
    print(f"Running: Delete Tag Test (ID: {tag_id})")
    print_curl_command("DELETE", f"{BASE_URL}/settings/tags/{tag_id}", HEADERS)
    response = requests.delete(f"{BASE_URL}/settings/tags/{tag_id}", headers=HEADERS)
    print_response(response, "Delete Tag")
    return response.status_code == 204

def run_all_tests():
    """Executes all API tests in sequence."""
    if not get_access_token():
        print("Halting tests due to login failure.")
        return

    results = {}
    results["create_general_setting"] = test_create_general_setting()
    results["list_general_settings"] = test_list_general_settings()
    results["update_general_setting"] = test_update_general_setting()
    results["create_tag"] = test_create_tag()
    results["list_tags"] = test_list_tags()
    results["update_tag"] = test_update_tag()
    results["delete_tag"] = test_delete_tag()

    print("\n--- Test Summary ---")
    for test_name, success in results.items():
        status = "PASSED" if success else "FAILED"
        print(f"{test_name}: {status}")
    print("--------------------")

if __name__ == "__main__":
    run_all_tests()
