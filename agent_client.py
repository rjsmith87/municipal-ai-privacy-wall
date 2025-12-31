import os
import requests

APPLINK_API_URL = os.environ.get('HEROKU_APPLINK_API_URL')
APPLINK_TOKEN = os.environ.get('HEROKU_APPLINK_TOKEN')

def get_sf_credentials():
    """Get fresh Salesforce credentials via AppLink"""
    url = f"{APPLINK_API_URL}/authorizations/toronto_auth"
    headers = {"Authorization": f"Bearer {APPLINK_TOKEN}"}
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        data = resp.json()
        return data.get('access_token'), data.get('instance_url')
    return None, None

def chat_with_austin(message, session_id=None):
    """Send message to Austin via Apex REST"""
    access_token, instance_url = get_sf_credentials()
    
    if not access_token:
        return {'success': False, 'error': 'Could not get Salesforce credentials'}
    
    url = f"{instance_url}/services/apexrest/austin"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    payload = {'message': message}
    if session_id:
        payload['sessionId'] = session_id
    
    resp = requests.post(url, headers=headers, json=payload, timeout=60)
    if resp.status_code == 200:
        return resp.json()
    return {'success': False, 'error': f'Salesforce error: {resp.status_code}'}
