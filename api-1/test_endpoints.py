import time
import requests

BASE_URL = "http://127.0.0.1:8000"

def wait_for_server():
    for _ in range(60):
        try:
            res = requests.get(f"{BASE_URL}/")
            if res.status_code == 200:
                print("Server is up!")
                return True
        except requests.exceptions.ConnectionError:
            time.sleep(2)
    print("Server failed to start")
    return False

def test():
    if not wait_for_server():
        return
        
    print("\n--- Test 1: GET /docs ---")
    res = requests.get(f"{BASE_URL}/docs")
    print(f"Status: {res.status_code}")

    print("\n--- Test 2: POST /api/chat/stream (Code Interpreter) ---")
    try:
        res = requests.post(f"{BASE_URL}/api/chat/stream", json={
            "message": "Calculate 25 * 42 using python_code_interpreter tool.",
            "thread_id": "test_thread_1234"
        }, stream=True)
        print(f"Status: {res.status_code}")
        # Just consume stream
        for chunk in res.iter_lines():
            if chunk:
                pass
        print("Stream completed.")
    except Exception as e:
        print(f"Failed /api/chat/stream: {e}")

    print("\n--- Test 3: GET /api/logs/{thread_id} ---")
    time.sleep(2) # Give background tasks time to complete
    try:
        res = requests.get(f"{BASE_URL}/api/logs/test_thread_1234")
        print(f"Status: {res.status_code}")
        data = res.json()
        if "logs" in data:
            logs = data["logs"]
            print(f"Logs count: {len(logs)}")
            for log in logs:
                print(f"  - {log.get('status')} | Tool: {log.get('tool_name')} | output: {str(log.get('tool_output'))[:100]} | Reasoning steps: {bool(log.get('reasoning_steps'))}")
        else:
            print(f"Response: {data}")
    except Exception as e:
        print(f"Failed /api/logs: {e}")

test()
