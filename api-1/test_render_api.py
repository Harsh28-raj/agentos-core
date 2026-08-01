import urllib.request
import json

url = "https://agentos-core-ssl7.onrender.com/api/v1/chat"
headers = {'Content-Type': 'application/json'}
data = {
    "message": "Hello, what is your name and what can you do?",
    "thread_id": "test_thread_777",
    "user_id": "test_user_777"
}

req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers, method='POST')

try:
    print(f"Testing {url} ...")
    with urllib.request.urlopen(req, timeout=120) as response:
        response_body = response.read().decode('utf-8')
        print(f"Status Code: {response.getcode()}")
        print(f"Response Body: {response_body}")
except urllib.error.HTTPError as e:
    print(f"HTTPError: {e.code} - {e.reason}")
    print(e.read().decode('utf-8'))
except Exception as e:
    print(f"Error: {str(e)}")
