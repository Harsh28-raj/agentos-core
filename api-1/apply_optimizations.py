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
    
    # 1. Update ChatGroq instantiations
    if 'ChatGroq(' in content:
        # We need to replace temperature, max_retries, and api_key
        # Let's just use regex to replace the whole ChatGroq(...) block if it's simple enough
        # Actually it's easier to just replace the parameters using regex or string replace.
        content = re.sub(r'api_key=os\.getenv\("GROQ_API_KEY"\)', 'groq_api_key=os.getenv("GROQ_API_KEY")', content)
        content = re.sub(r'max_retries=3', 'max_retries=2', content)
        content = re.sub(r'temperature=0\)', 'temperature=0.2)', content)
        content = re.sub(r'temperature=0,', 'temperature=0.2,', content)
        if 'temperature=0.2' not in content and 'max_retries=2' in content:
            # If temperature wasn't there, add it
            content = content.replace('max_retries=2', 'max_retries=2, temperature=0.2')
        modified = True

    # 2. Main.py updates: trimming, execution time, and clean response
    if file_path.endswith('main.py'):
        # Add memory trimming before invoking
        if '# Agent Execution with recursion guardrail' in content:
            trim_logic = """
        # Keep only the last 4 messages in history to save 90% of tokens
        if 'messages' in current_state.values and len(current_state.values['messages']) > 4:
            from langchain_core.messages import RemoveMessage
            messages_to_remove = [RemoveMessage(id=m.id) for m in current_state.values['messages'][:-4]]
            await agent_executor.aupdate_state(config, {"messages": messages_to_remove})
        
        # Agent Execution with recursion guardrail and timeout
"""
            content = content.replace('# Agent Execution with recursion guardrail\n', trim_logic)
        
        # Add max execution time
        if 'response = await agent_executor.ainvoke(payload, config=config, recursion_limit=5)' in content:
            content = content.replace(
                'response = await agent_executor.ainvoke(payload, config=config, recursion_limit=5)',
                'response = await asyncio.wait_for(agent_executor.ainvoke(payload, config=config, recursion_limit=5), timeout=20.0)'
            )
        
        # Revert chat handler generic errors
        if 'return {"reply": f"DEBUG ERROR: {str(e)}"}' in content:
            content = content.replace(
                'print("CHAT ENDPOINT CRASH:", traceback.format_exc())\n        return {"reply": f"DEBUG ERROR: {str(e)}"}',
                'return {"reply": "An internal error occurred while processing your request. Please check your API keys and try again later."}'
            )

        if 'error_payload = json.dumps({"type": "error", "content": f"DEBUG ERROR: {str(e)}"})' in content:
            content = content.replace(
                'print("CHAT ENDPOINT CRASH:", traceback.format_exc())\n            error_payload = json.dumps({"type": "error", "content": f"DEBUG ERROR: {str(e)}"})',
                'error_payload = json.dumps({"type": "error", "content": "An internal error occurred while processing your request. Please check your API keys and try again later."})'
            )
        modified = True

    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {file_path}")
