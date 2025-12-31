import os
import requests

APPLINK_API_URL = os.environ.get('HEROKU_APPLINK_API_URL')
APPLINK_TOKEN = os.environ.get('HEROKU_APPLINK_TOKEN')

def get_sf_token():
    """Get fresh Salesforce token via AppLink"""
    url = f"{APPLINK_API_URL}/authorizations/toronto_auth"
    headers = {"Authorization": f"Bearer {APPLINK_TOKEN}"}
    resp = requests.get(url, headers=headers)
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.text}")
    return resp.json()

if __name__ == "__main__":
    get_sf_token()
