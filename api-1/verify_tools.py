import requests
import json
import time

API_URL = "http://127.0.0.1:8000/api/chat"
USER_ID = "local_test_user"

def test_query(prompt: str):
    print(f"\n--- Testing Query: '{prompt}' ---")
    payload = {
        "message": prompt,
        "thread_id": USER_ID,
        "user_id": USER_ID
    }
    
    try:
        response = requests.post(API_URL, json=payload)
        result = response.json()
        print(f"Response: {result.get('reply')}")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    print("Testing Multi-Tool Chaining (Read email -> Check Calendar -> Schedule event)")
    test_query("Check my emails for any meetings requested by my boss, then check my calendar if I am free for that time. If I am, create a calendar event.")
