import os
import glob
import re

app_dir = 'c:/Users/harsh/OneDrive/Desktop/Agent OS/AgentOS/api-1/app'
python_files = glob.glob(os.path.join(app_dir, '**/*.py'), recursive=True)

instruction = "\nYou must output tool calls in valid JSON structure only. Do not wrap function calls in raw XML tags like <function>."

for file_path in python_files:
    if not os.path.exists(file_path): 
        continue
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    modified = False

    # 1. Update system prompts
    if 'system_prompt = SystemMessage(content="""' in content and 'XML tags like <function>' not in content:
        content = content.replace('""")', instruction + '\n""")')
        modified = True
        
    if 'system_prompt = (' in content and file_path.endswith('supervisor.py') and 'XML tags like <function>' not in content:
        # insert before the last )
        content = content.replace('\n)', f'"{instruction}"\n)')
        modified = True

    # 2. Revert main.py crash handlers
    if file_path.endswith('main.py'):
        if 'return {"reply": f"DEBUG BACKEND CRASH: {type(e).__name__} - {str(e)}"}' in content:
            content = content.replace(
                'print(traceback.format_exc())\n        return {"reply": f"DEBUG BACKEND CRASH: {type(e).__name__} - {str(e)}"}',
                'return {"reply": "An internal error occurred while processing your request. Please check your API keys and try again later."}'
            )
            modified = True
        
        if 'error_payload = json.dumps({"type": "error", "content": f"DEBUG BACKEND CRASH: {type(e).__name__} - {str(e)}"})' in content:
            content = content.replace(
                'print(traceback.format_exc())\n            error_payload = json.dumps({"type": "error", "content": f"DEBUG BACKEND CRASH: {type(e).__name__} - {str(e)}"})',
                'error_payload = json.dumps({"type": "error", "content": "An internal error occurred while processing your request. Please check your API keys and try again later."})'
            )
            modified = True
            
    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {file_path}")
