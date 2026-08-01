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
    if 'ChatGroq(' in content:
        # We need to ensure it looks like:
        # ChatGroq(model="llama-3.1-8b-instant", groq_api_key=os.getenv("GROQ_API_KEY"), max_retries=2, temperature=0.2)
        # Without any other kwargs
        content = re.sub(r'ChatGroq\([^)]+\)', 'ChatGroq(model="llama-3.1-8b-instant", groq_api_key=os.getenv("GROQ_API_KEY"), max_retries=2, temperature=0.2)', content)
        modified = True

    # 2. Revert main.py crash handlers
    if file_path.endswith('main.py'):
        if 'return {"reply": "An internal error occurred while processing your request. Please check your API keys and try again later."}' in content:
            content = content.replace(
                'return {"reply": "An internal error occurred while processing your request. Please check your API keys and try again later."}',
                'print(traceback.format_exc())\n        return {"reply": f"DEBUG BACKEND CRASH: {type(e).__name__} - {str(e)}"}'
            )
            modified = True
        
        if 'error_payload = json.dumps({"type": "error", "content": "An internal error occurred while processing your request. Please check your API keys and try again later."})' in content:
            content = content.replace(
                'error_payload = json.dumps({"type": "error", "content": "An internal error occurred while processing your request. Please check your API keys and try again later."})',
                'print(traceback.format_exc())\n            error_payload = json.dumps({"type": "error", "content": f"DEBUG BACKEND CRASH: {type(e).__name__} - {str(e)}"})'
            )
            modified = True

        # 3. Fix trimming safely
        if '# Keep only the last 4 messages in history' in content:
            old_trim = """        # Keep only the last 4 messages in history to save 90% of tokens
        if 'messages' in current_state.values and len(current_state.values['messages']) > 4:
            from langchain_core.messages import RemoveMessage
            messages_to_remove = [RemoveMessage(id=m.id) for m in current_state.values['messages'][:-4]]
            await agent_executor.aupdate_state(config, {"messages": messages_to_remove})"""
            new_trim = """        # Keep only the last 4 messages in history safely
        history = current_state.values.get('messages', [])
        if isinstance(history, list) and len(history) > 4:
            history = history[-4:]
            # We skip aupdate_state here as it causes crashes with RemoveMessage in some versions
            # Let LangGraph handle memory naturally or just trim local payload if necessary."""
            if old_trim in content:
                content = content.replace(old_trim, new_trim)
                modified = True
            
    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {file_path}")
