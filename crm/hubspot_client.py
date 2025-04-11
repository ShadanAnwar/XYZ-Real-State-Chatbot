import requests
import os
from dotenv import load_dotenv

load_dotenv()
HUBSPOT_API_KEY = os.getenv('HUBSPOT_API_KEY')

def create_or_update_contact(email, name, budget, lead_type, lead_score, qualification, chat_history, user_type):
    """Create or update a contact in HubSpot CRM."""
    if not HUBSPOT_API_KEY:
        print("Warning: HUBSPOT_API_KEY not set. CRM integration disabled.")
        return 200, {"status": "skipped", "message": "CRM integration disabled - API key not set"}
        
    url = "https://api.hubapi.com/crm/v3/objects/contacts"
    headers = {
        "Authorization": f"Bearer {HUBSPOT_API_KEY}",
        "Content-Type": "application/json"
    }
    properties = {
        "email": email,
        "firstname": name,
        "budget": str(budget),
        "lead_type": lead_type,
        "lead_score": str(lead_score),
        "lead_qualification": qualification,
        "chat_history": chat_history[:5000],
        "user_type": user_type
    }
    search_url = "https://api.hubapi.com/crm/v3/objects/contacts/search"
    search_payload = {
        "filterGroups": [
            {
                "filters": [
                    {
                        "propertyName": "email",
                        "operator": "EQ",
                        "value": email
                    }
                ]
            }
        ]
    }
    try:
        search_response = requests.post(search_url, headers=headers, json=search_payload)
        search_response.raise_for_status()
        results = search_response.json().get("results", [])
        if results:
            contact_id = results[0]["id"]
            update_url = f"{url}/{contact_id}"
            response = requests.patch(update_url, headers=headers, json={"properties": properties})
        else:
            response = requests.post(url, headers=headers, json={"properties": properties})
        return response.status_code, response.json()
    except requests.RequestException as e:
        return 500, {"error": str(e)}