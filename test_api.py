import requests
import uuid
import json

# --- Configuration ---
BASE_URL = "http://localhost:8002"
LOGIN_URL = "https://login-api.snolep.com/login/"
EMAIL = "democaadmin@yopmail.com"
PASSWORD = "demo@1234"

ACCESS_TOKEN = None
AGENCY_ID = None
HEADERS = {}

def login():
    global ACCESS_TOKEN, AGENCY_ID, HEADERS
    data = {
        'email': EMAIL,
        'password': PASSWORD
    }
    response = requests.post(LOGIN_URL, data=data)
    response.raise_for_status()
    json_response = response.json()
    ACCESS_TOKEN = json_response['access_token']
    AGENCY_ID = json_response['agency_id']
    HEADERS = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "x-agency-id": AGENCY_ID,
        "Content-Type": "application/json"
    }
    print("Login successful.")

def list_clients():
    response = requests.get(f"{BASE_URL}/clients/", headers=HEADERS)
    response.raise_for_status()
    return response.json()

def list_services():
    response = requests.get(f"{BASE_URL}/services/", headers=HEADERS)
    response.raise_for_status()
    return response.json()

def generate_curl_commands(client_id, service_ids):
    # --- List Services ---
    list_command = f"""
curl -X 'GET' \\
  '{BASE_URL}/services/{client_id}/services' \\
  -H 'accept: application/json' \\
  -H 'Authorization: Bearer {ACCESS_TOKEN}' \\
  -H 'x-agency-id: {AGENCY_ID}'
"""
    print("\\n" + "="*50)
    print("CURL COMMAND TO LIST CLIENT SERVICES:")
    print(list_command.strip())
    print("="*50 + "\\n")

    # --- Add Services ---
    add_data = [{"service_id": sid} for sid in service_ids]
    add_command = f"""
curl -X 'POST' \\
  '{BASE_URL}/services/{client_id}/services' \\
  -H 'accept: application/json' \\
  -H 'Authorization: Bearer {ACCESS_TOKEN}' \\
  -H 'x-agency-id: {AGENCY_ID}' \\
  -H 'Content-Type: application/json' \\
  -d '{json.dumps(add_data)}'
"""
    print("\\n" + "="*50)
    print("CURL COMMAND TO ADD SERVICES TO CLIENT:")
    print(add_command.strip())
    print("="*50 + "\\n")

    # --- Remove Services ---
    remove_data = {"service_ids": service_ids}
    remove_command = f"""
curl -X 'DELETE' \\
  '{BASE_URL}/services/{client_id}/services' \\
  -H 'accept: application/json' \\
  -H 'Authorization: Bearer {ACCESS_TOKEN}' \\
  -H 'x-agency-id: {AGENCY_ID}' \\
  -H 'Content-Type: application/json' \\
  -d '{json.dumps(remove_data)}'
"""
    print("\\n" + "="*50)
    print("CURL COMMAND TO REMOVE SERVICES FROM CLIENT:")
    print(remove_command.strip())
    print("="*50 + "\\n")


if __name__ == "__main__":
    login()
    clients = list_clients()
    if clients:
        client_id = clients[0]['id']
        print(f"Using Client ID: {client_id}")
        services = list_services()
        if services:
            service_ids_to_use = [s['id'] for s in services[:2]]
            generate_curl_commands(client_id, service_ids_to_use)
        else:
            print("No services available to generate commands.")
    else:
        print("No clients found.")
