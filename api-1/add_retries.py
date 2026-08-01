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
    
    # Simple replace for ChatGroq initialization
    # Target: ChatGroq(api_key=os.getenv("GROQ_API_KEY"), model="llama-3.1-8b-instant", temperature=0) or similar
    if 'max_retries' not in content and 'ChatGroq(' in content:
        # We need to carefully add max_retries=5.
        # It's easier to just do a string replacement on the model string if it's there
        if 'model="llama-3.1-8b-instant",' in content:
            content = content.replace('model="llama-3.1-8b-instant",', 'model="llama-3.1-8b-instant",\n    max_retries=5,')
            modified = True
        elif 'model="llama-3.1-8b-instant"' in content:
            content = content.replace('model="llama-3.1-8b-instant"', 'model="llama-3.1-8b-instant", max_retries=5')
            modified = True
            
    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {file_path}")
