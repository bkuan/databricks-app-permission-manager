import requests
import json

client_id = ""
client_secret = ""
databricks_instance = ""

token_resp = requests.post(
    f"{databricks_instance}/oidc/v1/token",
    data={
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "all-apis"
    }
)

access_token = token_resp.json()["access_token"]

apps_url = f"{databricks_instance}/api/2.0/apps"
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

# GET LIST OF APPS

apps_response = requests.get(apps_url, headers=headers)
if apps_response.status_code != 200:
    print(f"Failed to get apps. Status: {apps_response.status_code}, Response: {apps_response.text}")
    apps = []
else:
    try:
        apps = apps_response.json().get("apps", [])
    except Exception as e:
        print(f"Error decoding apps response as JSON: {e}\nRaw response: {apps_response.text}")
        apps = []
print(f"{apps}\n");
for app in apps:
    app_id = app.get("name")
    perm_url = f"{databricks_instance}/api/2.0/permissions/apps/{app_id}"
    
    # GET LIST OF EACH APP PERMISSIONS
    perm_response = requests.get(perm_url, headers=headers)
    if perm_response.status_code != 200:
        print(f"Failed to get permissions for app {app_id}. Status: {perm_response.status_code}, Response: {perm_response.text}")
        permissions = []
    else:
        try:
            permissions = perm_response.json().get("access_control_list", [])
        except Exception as e:
            print(f"Error decoding permissions response for app {app_id} as JSON: {e}\nRaw response: {perm_response.text}")
            permissions = []
    print(f"Original permissions for app {app_id}: {permissions}\n")
    
    # REMOVE PERMISSIONS FOR "ACCOUNT USERS"
    new_permissions = [
        perm for perm in permissions
        if not (perm.get("group_name") == "account users")
    ]
    print(f"New permissions for app {new_permissions}\n");

    extracted_permissions = [
        {
            "user_name": perm.get("user_name"),
            "group_name": perm.get("group_name"),
            "permission_level": perm.get("all_permissions", [{}])[0].get("permission_level")
        }
        for perm in new_permissions
    ]
    print(f"Extracted permissions for app {app_id}: {extracted_permissions}\n")

    # PUT BACK PERMISSIONS WITHOUT REMOVED ENTRIES
    payload = {"access_control_list": extracted_permissions}
    put_response = requests.put(perm_url, headers=headers, data=json.dumps(payload))
    if put_response.status_code != 200:
        print(f"Failed to update permissions for app {app_id}. Status: {put_response.status_code}, Response: {put_response.text}")
    else:
        try:
            updated = put_response.json()
            print(f"Updated permissions for app {app_id}: {updated}")
        except Exception as e:
            print(f"Error decoding update response for app {app_id} as JSON: {e}\nRaw response: {put_response.text}")