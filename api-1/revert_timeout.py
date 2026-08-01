import os
import glob
import json

app_dir = 'c:/Users/harsh/OneDrive/Desktop/Agent OS/AgentOS/api-1/app'
python_files = glob.glob(os.path.join(app_dir, '**/*.py'), recursive=True)

for file_path in python_files:
    if not os.path.exists(file_path): 
        continue
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    modified = False
    
    # Remove request_timeout
    if 'request_timeout=30.0,' in content:
        content = content.replace('\n    request_timeout=30.0,', '')
        content = content.replace('request_timeout=30.0,', '')
        modified = True
    if 'request_timeout=30.0' in content:
        content = content.replace(', request_timeout=30.0', '')
        content = content.replace('request_timeout=30.0', '')
        modified = True

    # Revert groq_api_key to api_key
    if 'groq_api_key=' in content:
        content = content.replace('groq_api_key=', 'api_key=')
        modified = True

    # Add DEBUG ERROR back to main.py
    if 'return {"reply": "An internal error occurred while processing your request. Please check your API keys and try again later."}' in content:
        content = content.replace(
            'return {"reply": "An internal error occurred while processing your request. Please check your API keys and try again later."}',
            'print("CHAT ENDPOINT CRASH:", traceback.format_exc())\n        return {"reply": f"DEBUG ERROR: {str(e)}"}'
        )
        modified = True

    if 'error_payload = json.dumps({"type": "error", "content": "An internal error occurred while processing your request. Please check your API keys and try again later."})' in content:
        content = content.replace(
            'error_payload = json.dumps({"type": "error", "content": "An internal error occurred while processing your request. Please check your API keys and try again later."})',
            'print("CHAT ENDPOINT CRASH:", traceback.format_exc())\n            error_payload = json.dumps({"type": "error", "content": f"DEBUG ERROR: {str(e)}"})'
        )
        modified = True

    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {file_path}")
