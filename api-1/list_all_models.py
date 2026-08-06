import requests
import os
from dotenv import load_dotenv

load_dotenv()
res = requests.get('https://api.groq.com/openai/v1/models', headers={'Authorization': 'Bearer ' + os.environ.get("GROQ_API_KEY", "")})
data = res.json().get('data', [])
ids = sorted([m['id'] for m in data])
print("All available models:")
for m in ids:
    print(" -", m)
