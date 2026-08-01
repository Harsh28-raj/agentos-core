import os

file_path = 'c:/Users/harsh/OneDrive/Desktop/Agent OS/AgentOS/api-1/app/main.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

chat_endpoint_replacement = '''        # Keep only the last 4 messages in history safely
        history = current_state.values.get('messages', [])
        if isinstance(history, list) and len(history) > 4:
            try:
                from langchain_core.messages import RemoveMessage
                msgs_to_remove = history[:-4]
                remove_payload = {"messages": [RemoveMessage(id=m.id) for m in msgs_to_remove if hasattr(m, 'id') and m.id]}
                agent_executor.update_state(config, remove_payload)
                current_state = agent_executor.get_state(config)
            except Exception as e:
                import logging
                logging.warning(f"Could not remove old messages: {e}")'''

stream_endpoint_replacement = '''            # 1. State check to see if we are resuming from a HITL pause
            current_state = agent_executor.get_state(config)
            
            # Keep only the last 4 messages in history safely
            history = current_state.values.get('messages', [])
            if isinstance(history, list) and len(history) > 4:
                try:
                    from langchain_core.messages import RemoveMessage
                    msgs_to_remove = history[:-4]
                    remove_payload = {"messages": [RemoveMessage(id=m.id) for m in msgs_to_remove if hasattr(m, 'id') and m.id]}
                    agent_executor.update_state(config, remove_payload)
                    current_state = agent_executor.get_state(config)
                except Exception as e:
                    import logging
                    logging.warning(f"Could not remove old messages: {e}")
                    
            is_resuming = len(current_state.next) > 0'''

# replace in chat_endpoint
content = content.replace(
'''        # Keep only the last 4 messages in history safely
        history = current_state.values.get('messages', [])
        if isinstance(history, list) and len(history) > 4:
            history = history[-4:]
            # We skip aupdate_state here as it causes crashes with RemoveMessage in some versions
            # Let LangGraph handle memory naturally or just trim local payload if necessary.''',
chat_endpoint_replacement
)

# replace in stream_endpoint
content = content.replace(
'''            # 1. State check to see if we are resuming from a HITL pause
            current_state = agent_executor.get_state(config)
            is_resuming = len(current_state.next) > 0''',
stream_endpoint_replacement
)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Trim messages logic updated in app/main.py")
