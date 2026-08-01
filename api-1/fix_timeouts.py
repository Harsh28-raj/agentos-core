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

    target_str = 'llm = ChatGroq(model="llama-3.1-8b-instant", groq_api_key=os.getenv("GROQ_API_KEY"), max_retries=2, temperature=0.2)'
    new_str = 'llm = ChatGroq(model="llama-3.1-8b-instant", groq_api_key=os.getenv("GROQ_API_KEY"), max_retries=2, temperature=0.2, timeout=60.0)'
    
    if target_str in content:
        content = content.replace(target_str, new_str)
        modified = True
        
    target_str2 = 'vision_llm = ChatGroq(model="llama-3.1-8b-instant", groq_api_key=os.getenv("GROQ_API_KEY"), max_retries=2, temperature=0.2)'
    new_str2 = 'vision_llm = ChatGroq(model="llama-3.1-8b-instant", groq_api_key=os.getenv("GROQ_API_KEY"), max_retries=2, temperature=0.2, timeout=60.0)'
    
    if target_str2 in content:
        content = content.replace(target_str2, new_str2)
        modified = True

    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {file_path}")

print("Timeout update complete.")
