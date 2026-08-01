import os
import glob

app_dir = 'c:/Users/harsh/OneDrive/Desktop/Agent OS/AgentOS/api-1/app'
python_files = glob.glob(os.path.join(app_dir, '**/*.py'), recursive=True)

models_to_replace = [
    'llama3-8b-8192',
    'llama3-70b-8192',
    'mixtral-8x7b-32768'
]
new_model = 'llama-3.3-70b-versatile'

for file_path in python_files:
    if not os.path.exists(file_path): 
        continue
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    modified = False
    
    for old_model in models_to_replace:
        if old_model in content:
            content = content.replace(old_model, new_model)
            modified = True
            
    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {file_path}")
