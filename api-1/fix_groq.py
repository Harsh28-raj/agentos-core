import os
import glob

agents_dir = 'c:/Users/harsh/OneDrive/Desktop/Agent OS/AgentOS/api-1/app/ai/agents'
agent_files = glob.glob(os.path.join(agents_dir, '*.py'))
agent_files.append('c:/Users/harsh/OneDrive/Desktop/Agent OS/AgentOS/api-1/app/ai/agent.py')

for file_path in agent_files:
    if not os.path.exists(file_path): 
        continue
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    modified = False
    
    if 'import os' not in content:
        content = 'import os\n' + content
        modified = True
        
    if 'api_key=os.getenv("GROQ_API_KEY")' not in content:
        content = content.replace('ChatGroq(', 'ChatGroq(api_key=os.getenv("GROQ_API_KEY"), ')
        modified = True
        
    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
