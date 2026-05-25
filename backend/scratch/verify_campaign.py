import requests
import sys
import uuid

BASE_URL = "http://127.0.0.1:8000"

def run_campaign_verification():
    print("=== STARTING CAMPAIGN REST API VERIFICATION ===")
    
    # 1. Try to create a campaign without token
    camp_url = f"{BASE_URL}/api/campaigns"
    camp_payload = {
        "name": f"Verification Campaign {uuid.uuid4().hex[:6]}",
        "target_role": "Python developer",
        "max_emails_per_hour": 10,
        "max_contacts_per_company": 3,
        "stagger_interval_minutes": 15
    }
    
    print("\n1. Testing unauthenticated campaign creation...")
    try:
        response = requests.post(camp_url, json=camp_payload)
        print(f"Status Code (unauthenticated): {response.status_code}")
        if response.status_code != 401:
            print(f"Error: Expected 401, got {response.status_code}. Response: {response.text}")
            sys.exit(1)
        print("✓ Successfully rejected unauthenticated request.")
    except Exception as e:
        print(f"Exception during unauthenticated check: {e}")
        sys.exit(1)

    # 2. Register User 1 and get token
    email_u1 = f"verify_u1_{uuid.uuid4().hex[:6]}@example.com"
    print(f"\n2. Registering User 1: {email_u1}...")
    try:
        res = requests.post(f"{BASE_URL}/auth/register", json={
            "full_name": "Verification User One",
            "email": email_u1,
            "password": "securepassword123"
        })
        if res.status_code != 201:
            print(f"Failed to register User 1: {res.text}")
            sys.exit(1)
        token_u1 = res.json()["access_token"]
        headers_u1 = {"Authorization": f"Bearer {token_u1}"}
        print("✓ User 1 registered and authenticated successfully.")
    except Exception as e:
        print(f"Exception registering User 1: {e}")
        sys.exit(1)

    # 3. Create campaign for User 1
    print(f"\n3. Creating campaign for User 1...")
    try:
        res = requests.post(f"{BASE_URL}/api/campaigns/", json=camp_payload, headers=headers_u1)
        print(f"Status Code: {res.status_code}")
        if res.status_code != 200:
            print(f"Failed to create campaign: {res.text}")
            sys.exit(1)
        campaign_data = res.json()
        campaign_id = campaign_data["id"]
        print(f"✓ Campaign created successfully! ID: {campaign_id}, Name: '{campaign_data['name']}'")
        assert campaign_data["target_role"] == "Python developer"
    except Exception as e:
        print(f"Exception creating campaign: {e}")
        sys.exit(1)

    # 4. List campaigns for User 1
    print("\n4. Listing campaigns for User 1...")
    try:
        res = requests.get(f"{BASE_URL}/api/campaigns/", headers=headers_u1)
        print(f"Status Code: {res.status_code}")
        if res.status_code != 200:
            print(f"Failed to list campaigns: {res.text}")
            sys.exit(1)
        campaigns = res.json()
        print(f"User 1 campaigns count: {len(campaigns)}")
        assert any(c["id"] == campaign_id for c in campaigns), "Created campaign not found in list"
        print("✓ Created campaign found in list.")
    except Exception as e:
        print(f"Exception listing campaigns: {e}")
        sys.exit(1)

    # 5. Register User 2 and try to access User 1's campaign
    email_u2 = f"verify_u2_{uuid.uuid4().hex[:6]}@example.com"
    print(f"\n5. Registering User 2: {email_u2}...")
    try:
        res = requests.post(f"{BASE_URL}/auth/register", json={
            "full_name": "Verification User Two",
            "email": email_u2,
            "password": "securepassword123"
        })
        if res.status_code != 201:
            print(f"Failed to register User 2: {res.text}")
            sys.exit(1)
        token_u2 = res.json()["access_token"]
        headers_u2 = {"Authorization": f"Bearer {token_u2}"}
        print("✓ User 2 registered and authenticated successfully.")
        
        # Access campaign
        print(f"User 2 trying to GET User 1's campaign {campaign_id}...")
        res_get = requests.get(f"{BASE_URL}/api/campaigns/{campaign_id}", headers=headers_u2)
        print(f"Status Code (GET cross-access): {res_get.status_code}")
        if res_get.status_code != 403:
            print(f"Error: Expected 403 Forbidden, got {res_get.status_code}")
            sys.exit(1)
        print("✓ Cross-access GET correctly rejected with 403.")
        
        # Delete campaign
        print(f"User 2 trying to DELETE User 1's campaign {campaign_id}...")
        res_del = requests.delete(f"{BASE_URL}/api/campaigns/{campaign_id}", headers=headers_u2)
        print(f"Status Code (DELETE cross-access): {res_del.status_code}")
        if res_del.status_code != 403:
            print(f"Error: Expected 403 Forbidden, got {res_del.status_code}")
            sys.exit(1)
        print("✓ Cross-access DELETE correctly rejected with 403.")
    except Exception as e:
        print(f"Exception verifying authorization: {e}")
        sys.exit(1)

    # 6. Delete campaign as User 1
    print(f"\n6. Deleting campaign {campaign_id} as User 1...")
    try:
        res = requests.delete(f"{BASE_URL}/api/campaigns/{campaign_id}", headers=headers_u1)
        print(f"Status Code: {res.status_code}")
        if res.status_code != 200:
            print(f"Failed to delete campaign: {res.text}")
            sys.exit(1)
        print("✓ Campaign deleted successfully.")
    except Exception as e:
        print(f"Exception deleting campaign: {e}")
        sys.exit(1)

    print("\n=== ALL CAMPAIGN REST API TESTS PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    run_campaign_verification()
