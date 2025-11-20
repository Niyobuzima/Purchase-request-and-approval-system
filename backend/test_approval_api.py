"""
Test script for approval workflow API endpoints.
"""
import requests
import json

BASE_URL = "http://localhost:8000/api"

def print_section(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)

def print_response(response, show_data=True):
    print(f"Status Code: {response.status_code}")
    if show_data:
        try:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
        except:
            print(f"Response: {response.text}")
    print()

# Test credentials
STAFF_CREDS = {"email": "teststaff@procure.com", "password": "password123"}
APPROVER_L1_CREDS = {"email": "approver.l1@procure.com", "password": "password123"}
APPROVER_L2_CREDS = {"email": "approver.l2@procure.com", "password": "password123"}

def get_token(credentials):
    """Get JWT token"""
    response = requests.post(f"{BASE_URL}/auth/login/", json=credentials)
    if response.status_code == 200:
        return response.json()['access']
    else:
        print(f"Failed to get token: {response.status_code}")
        print(response.text)
        return None

def main():
    print_section("APPROVAL WORKFLOW API TEST")

    # 1. Login as staff
    print_section("1. LOGIN AS STAFF")
    staff_token = get_token(STAFF_CREDS)
    if not staff_token:
        print("[FAIL] Failed to login as staff")
        return
    print(f"[OK] Staff token obtained: {staff_token[:20]}...")

    # 2. Create a purchase request
    print_section("2. CREATE PURCHASE REQUEST")
    headers = {"Authorization": f"Bearer {staff_token}"}
    request_data = {
        "title": "API Test - Office Supplies",
        "description": "Testing approval workflow via API",
        "items": [
            {
                "item_name": "Desk Chair",
                "description": "Ergonomic office chair",
                "quantity": "3",
                "unit_price": "250.00"
            },
            {
                "item_name": "Desk Lamp",
                "description": "LED desk lamp",
                "quantity": "5",
                "unit_price": "45.00"
            }
        ]
    }

    response = requests.post(
        f"{BASE_URL}/requests/",
        headers=headers,
        json=request_data
    )
    print_response(response)

    if response.status_code != 201:
        print("[FAIL] Failed to create request")
        return

    request_id = response.json()['data']['id']
    print(f"[OK] Request created with ID: {request_id}")

    # 3. Submit request for approval
    print_section("3. SUBMIT REQUEST FOR APPROVAL")
    response = requests.patch(
        f"{BASE_URL}/requests/{request_id}/submit/",
        headers=headers
    )
    print_response(response)

    if response.status_code != 200:
        print("[FAIL] Failed to submit request")
        return

    print("[OK] Request submitted successfully")

    # 4. View approval history (should show SUBMITTED)
    print_section("4. VIEW APPROVAL HISTORY (AFTER SUBMISSION)")
    response = requests.get(
        f"{BASE_URL}/requests/{request_id}/approval-history/",
        headers=headers
    )
    print_response(response)

    # 5. Login as Approver L1
    print_section("5. LOGIN AS APPROVER L1")
    l1_token = get_token(APPROVER_L1_CREDS)
    if not l1_token:
        print("[FAIL] Failed to login as approver L1")
        return
    print(f"[OK] Approver L1 token obtained: {l1_token[:20]}...")

    # 6. View pending requests (L1 should see it)
    print_section("6. VIEW PENDING REQUESTS (APPROVER L1)")
    l1_headers = {"Authorization": f"Bearer {l1_token}"}
    response = requests.get(
        f"{BASE_URL}/requests/?status=PENDING",
        headers=l1_headers
    )
    print_response(response, show_data=False)
    print(f"Found {response.json()['data']['count']} pending requests")

    # 7. Approve at L1
    print_section("7. APPROVE REQUEST (LEVEL 1)")
    response = requests.patch(
        f"{BASE_URL}/requests/{request_id}/approve/",
        headers=l1_headers,
        json={"comments": "Approved - necessary items for team"}
    )
    print_response(response)

    if response.status_code != 200:
        print("[FAIL] Failed to approve at L1")
        return

    print("[OK] Request approved at Level 1")

    # 8. View approval history (should show SUBMITTED + APPROVED L1)
    print_section("8. VIEW APPROVAL HISTORY (AFTER L1 APPROVAL)")
    response = requests.get(
        f"{BASE_URL}/requests/{request_id}/approval-history/",
        headers=headers
    )
    print_response(response)

    # 9. Login as Approver L2
    print_section("9. LOGIN AS APPROVER L2")
    l2_token = get_token(APPROVER_L2_CREDS)
    if not l2_token:
        print("[FAIL] Failed to login as approver L2")
        return
    print(f"[OK] Approver L2 token obtained: {l2_token[:20]}...")

    # 10. View pending requests (L2 should see it)
    print_section("10. VIEW PENDING REQUESTS (APPROVER L2)")
    l2_headers = {"Authorization": f"Bearer {l2_token}"}
    response = requests.get(
        f"{BASE_URL}/requests/?status=PENDING",
        headers=l2_headers
    )
    print_response(response, show_data=False)
    print(f"Found {response.json()['data']['count']} pending requests")

    # 11. Approve at L2 (final approval)
    print_section("11. APPROVE REQUEST (LEVEL 2 - FINAL)")
    response = requests.patch(
        f"{BASE_URL}/requests/{request_id}/approve/",
        headers=l2_headers,
        json={"comments": "Final approval granted - proceed with purchase"}
    )
    print_response(response)

    if response.status_code != 200:
        print("[FAIL] Failed to approve at L2")
        return

    print("[OK] Request approved at Level 2 (FINAL)")

    # 12. View final approval history
    print_section("12. VIEW FINAL APPROVAL HISTORY")
    response = requests.get(
        f"{BASE_URL}/requests/{request_id}/approval-history/",
        headers=headers
    )
    print_response(response)

    # 13. View approval logs via new endpoint
    print_section("13. VIEW ALL APPROVAL LOGS (STAFF)")
    response = requests.get(
        f"{BASE_URL}/approval-logs/",
        headers=headers
    )
    print_response(response, show_data=False)
    print(f"Found {response.json()['data']['count']} approval logs visible to staff")

    # 14. View approver's own actions
    print_section("14. VIEW APPROVER L1'S OWN ACTIONS")
    response = requests.get(
        f"{BASE_URL}/approval-logs/my-actions/",
        headers=l1_headers
    )
    print_response(response)

    print_section("[SUCCESS] ALL TESTS PASSED SUCCESSFULLY!")
    print(f"\nTest Request ID: {request_id}")
    print("You can view this request in the admin panel or via API")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[FAIL] Test failed with error: {e}")
        import traceback
        traceback.print_exc()
