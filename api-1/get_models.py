import requests
import os
from dotenv import load_dotenv

load_dotenv()
res = requests.get('https://api.groq.com/openai/v1/models', headers={'Authorization': f'Bearer {os.environ.get("GROQ_API_KEY")}'})
data = res.json().get('data', [])
print("vision models:", [m['id'] for m in data if 'vision' in m['id'].lower()])
print("3.2 models:", [m['id'] for m in data if '3.2' in m['id'].lower()])
