import os
import glob

app_dir = 'c:/Users/harsh/OneDrive/Desktop/Agent OS/AgentOS/api-1/app'
python_files = glob.glob(os.path.join(app_dir, '**/*.py'), recursive=True)

for file_path in python_files:
    if not os.path.exists(file_path): 
        continue
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    modified = False
    
    # Add request_timeout=30.0
    if 'max_retries=5' in content:
        content = content.replace('max_retries=5,', 'max_retries=3,\n    request_timeout=30.0,')
        content = content.replace('max_retries=5', 'max_retries=3, request_timeout=30.0')
        modified = True
            
    if 'recursion_limit=10' in content:
        content = content.replace('recursion_limit=10', 'recursion_limit=5')
        modified = True

    # Revert chat handler generic errors
    if 'return {"reply": f"ERROR DETAILS: {str(e)}"}' in content:
        content = content.replace('return {"reply": f"ERROR DETAILS: {str(e)}"}', 'return {"reply": "An internal error occurred while processing your request. Please check your API keys and try again later."}')
        modified = True

    if 'error_payload = json.dumps({"type": "error", "content": f"ERROR DETAILS: {str(e)}"})' in content:
        content = content.replace('error_payload = json.dumps({"type": "error", "content": f"ERROR DETAILS: {str(e)}"})', 'error_payload = json.dumps({"type": "error", "content": "An internal error occurred while processing your request. Please check your API keys and try again later."})')
        modified = True

    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {file_path}")
