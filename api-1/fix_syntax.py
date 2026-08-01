import os
import glob
import re

app_dir = 'c:/Users/harsh/OneDrive/Desktop/Agent OS/AgentOS/api-1/app'
python_files = glob.glob(os.path.join(app_dir, '**/*.py'), recursive=True)

for file_path in python_files:
    if not os.path.exists(file_path): 
        continue
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    modified = False
    
    # Fix agents
    if 'max_retries=2, temperature=0.2,\n    temperature=0' in content:
        content = content.replace('max_retries=2, temperature=0.2,\n    temperature=0', 'max_retries=2, temperature=0.2')
        modified = True
    elif 'max_retries=2, temperature=0.2, \n        temperature=0.7,' in content:
        content = content.replace('max_retries=2, temperature=0.2, \n        temperature=0.7,', 'max_retries=2, temperature=0.2,')
        modified = True
    elif 'max_retries=2, temperature=0.2,\n        temperature=0.7,' in content:
        content = content.replace('max_retries=2, temperature=0.2,\n        temperature=0.7,', 'max_retries=2, temperature=0.2,')
        modified = True

    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed {file_path}")
