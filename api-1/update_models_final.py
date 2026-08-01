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
    
    if 'llama-3.3-70b-versatile' in content:
        content = content.replace('llama-3.3-70b-versatile', 'llama-3.1-8b-instant')
        modified = True
        
    if 'api_key=os.getenv("GROQ_API_KEY")' in content:
        content = content.replace('api_key=os.getenv("GROQ_API_KEY")', 'groq_api_key=os.getenv("GROQ_API_KEY")')
        modified = True
            
    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {file_path}")
