#!/usr/bin/env python3
"""
Authentication Testing Script
Demonstrates and tests the signature authentication functionality
"""

import requests
import time
import json

BASE_URL = "http://localhost:5000"

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def print_response(response, title="Response"):
    """Print formatted JSON response"""
    print(f"\n{title}:")
    print(json.dumps(response.json(), indent=2))

def test_list_users():
    """Test listing enrolled users"""
    print_section("TEST 1: List Enrolled Users")
    response = requests.get(f"{BASE_URL}/api/auth/users")
    print_response(response, "Current Users")
    return response.json()

def test_enrollment(username):
    """Test user enrollment process"""
    print_section(f"TEST 2: Start Enrollment for '{username}'")
    
    # Start enrollment
    response = requests.post(
        f"{BASE_URL}/api/auth/enroll",
        json={"username": username}
    )
    print_response(response, "Enrollment Started")
    
    if response.status_code == 200:
        print("\n✓ Enrollment initiated successfully!")
        print("👉 Now draw your signature in the camera view")
        print("👉 Show TWO FINGERS (index + middle) when done")
        
        # Wait for user to complete enrollment
        print("\nWaiting for enrollment completion...")
        for i in range(30):
            time.sleep(1)
            status = requests.get(f"{BASE_URL}/api/auth/status")
            status_data = status.json()
            
            if status_data['status'] == 'success':
                auth_status = status_data.get('auth_status', {})
                if auth_status.get('has_result'):
                    result = auth_status.get('result', {})
                    if 'success' in result:
                        print_response(status, "Enrollment Result")
                        return result.get('success', False)
        
        print("\n⚠ Enrollment timeout. User may need more time.")
        return None
    else:
        print("\n✗ Failed to start enrollment")
        return False

def test_verification(username):
    """Test signature verification"""
    print_section(f"TEST 3: Verify Signature for '{username}'")
    
    # Start verification
    response = requests.post(
        f"{BASE_URL}/api/auth/verify",
        json={"username": username}
    )
    print_response(response, "Verification Started")
    
    if response.status_code == 200:
        print("\n✓ Verification initiated successfully!")
        print("👉 Now draw your signature again in the camera view")
        print("👉 Show TWO FINGERS (index + middle) when done")
        
        # Wait for user to complete verification
        print("\nWaiting for verification completion...")
        for i in range(30):
            time.sleep(1)
            status = requests.get(f"{BASE_URL}/api/auth/status")
            status_data = status.json()
            
            if status_data['status'] == 'success':
                auth_status = status_data.get('auth_status', {})
                if auth_status.get('has_result'):
                    result = auth_status.get('result', {})
                    if 'authenticated' in result:
                        print_response(status, "Verification Result")
                        return result
        
        print("\n⚠ Verification timeout. User may need more time.")
        return None
    else:
        print("\n✗ Failed to start verification")
        return None

def test_delete_user(username):
    """Test deleting a user"""
    print_section(f"TEST 4: Delete User '{username}'")
    
    response = requests.delete(f"{BASE_URL}/api/auth/delete/{username}")
    print_response(response, "Delete Result")
    
    if response.status_code == 200:
        print(f"\n✓ User '{username}' deleted successfully")
        return True
    else:
        print(f"\n✗ Failed to delete user '{username}'")
        return False

def test_thresholds():
    """Test getting and updating thresholds"""
    print_section("TEST 5: Authentication Thresholds")
    
    # Get current thresholds
    response = requests.get(f"{BASE_URL}/api/auth/thresholds")
    print_response(response, "Current Thresholds")
    
    current = response.json().get('thresholds', {})
    
    print("\n📊 Threshold Explanation:")
    print(f"  DTW Threshold: {current.get('dtw_threshold')}")
    print("    - Maximum trajectory distance for match")
    print("    - Lower = stricter, Higher = more lenient")
    print(f"  Feature Threshold: {current.get('feature_threshold')}")
    print("    - Maximum normalized feature distance")
    print("    - Range: 0.0 (exact) to 1.0 (very different)")

def test_system_status():
    """Check if system is running"""
    print_section("System Status Check")
    
    try:
        response = requests.get(f"{BASE_URL}/api/status", timeout=2)
        print_response(response, "System Status")
        
        data = response.json()
        if data.get('status') == 'running':
            print("\n✓ System is running and ready")
            return True
        else:
            print("\n⚠ System is stopped. Please start it first.")
            return False
    except requests.exceptions.RequestException as e:
        print(f"\n✗ Cannot connect to system: {e}")
        print("Make sure the Flask server is running:")
        print("  cd backend")
        print("  python app.py")
        return False

def interactive_menu():
    """Interactive testing menu"""
    print_section("Air Signature Authentication - Interactive Tester")
    
    # Check system status first
    if not test_system_status():
        return
    
    while True:
        print("\n" + "-"*60)
        print("Choose an option:")
        print("  1. List enrolled users")
        print("  2. Enroll new user")
        print("  3. Verify existing user")
        print("  4. Delete user")
        print("  5. View thresholds")
        print("  6. Run full test sequence")
        print("  0. Exit")
        print("-"*60)
        
        choice = input("\nEnter your choice: ").strip()
        
        if choice == "1":
            test_list_users()
        
        elif choice == "2":
            username = input("Enter username to enroll: ").strip()
            if username:
                test_enrollment(username)
        
        elif choice == "3":
            username = input("Enter username to verify: ").strip()
            if username:
                test_verification(username)
        
        elif choice == "4":
            username = input("Enter username to delete: ").strip()
            if username:
                test_delete_user(username)
        
        elif choice == "5":
            test_thresholds()
        
        elif choice == "6":
            run_full_test()
        
        elif choice == "0":
            print("\nExiting tester. Goodbye!")
            break
        
        else:
            print("\n⚠ Invalid choice. Please try again.")

def run_full_test():
    """Run a complete test sequence"""
    print_section("FULL TEST SEQUENCE")
    
    test_username = f"test_user_{int(time.time())}"
    
    print(f"\nTest username: {test_username}")
    print("\nThis will test the complete authentication workflow:")
    print("  1. List users")
    print("  2. Enroll new user")
    print("  3. Verify user (should succeed)")
    print("  4. Delete user")
    print("  5. List users again")
    
    input("\nPress ENTER to begin...")
    
    # Step 1: List users
    test_list_users()
    time.sleep(2)
    
    # Step 2: Enroll
    enrollment_success = test_enrollment(test_username)
    if not enrollment_success:
        print("\n⚠ Enrollment failed or timed out. Stopping test.")
        return
    
    time.sleep(2)
    
    # Step 3: Verify
    verification_result = test_verification(test_username)
    if verification_result:
        if verification_result.get('authenticated'):
            print("\n✓✓✓ VERIFICATION SUCCESSFUL! ✓✓✓")
            print(f"Confidence: {verification_result.get('confidence', 0):.1f}%")
        else:
            print("\n✗✗✗ VERIFICATION FAILED ✗✗✗")
            print("This might happen if signatures were too different.")
    
    time.sleep(2)
    
    # Step 4: Delete
    test_delete_user(test_username)
    time.sleep(1)
    
    # Step 5: List users again
    test_list_users()
    
    print_section("FULL TEST COMPLETE")

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════╗
║  AERO MOUSE - Signature Authentication Test Suite       ║
║  Make sure the Flask server is running before testing   ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    try:
        interactive_menu()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting...")
    except Exception as e:
        print(f"\n\n✗ Error: {e}")
