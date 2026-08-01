import os
import glob

agents_dir = 'c:/Users/harsh/OneDrive/Desktop/Agent OS/AgentOS/api-1/app/ai/agents'
agent_files = glob.glob(os.path.join(agents_dir, '*.py'))
agent_files.append('c:/Users/harsh/OneDrive/Desktop/Agent OS/AgentOS/api-1/app/ai/agent.py')
agent_files.append('c:/Users/harsh/OneDrive/Desktop/Agent OS/AgentOS/api-1/app/main.py')

for file_path in agent_files:
    if not os.path.exists(file_path): 
        continue
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    modified = False
    
    if 'llama-3.3-70b-versatile' in content:
        content = content.replace('llama-3.3-70b-versatile', 'llama3-8b-8192')
        modified = True
        
    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
