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
    
    # 1. Clean ChatGroq initializations across agents
    bad_syntax = '''llm = ChatGroq(model="llama-3.1-8b-instant", groq_api_key=os.getenv("GROQ_API_KEY"), max_retries=2, temperature=0.2)
    model="llama-3.1-8b-instant",
    max_retries=2, temperature=0.2
)'''
    good_syntax = '''llm = ChatGroq(model="llama-3.1-8b-instant", groq_api_key=os.getenv("GROQ_API_KEY"), max_retries=2, temperature=0.2)'''
    
    if bad_syntax in content:
        content = content.replace(bad_syntax, good_syntax)
        modified = True
        
    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed {file_path}")
