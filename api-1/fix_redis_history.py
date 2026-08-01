import os

file_path = 'c:/Users/harsh/OneDrive/Desktop/Agent OS/AgentOS/api-1/app/main.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. /api/v1/chat
content = content.replace(
    'config = {"configurable": {"thread_id": request.user_id, "user_id": request.user_id}}',
    'session_id = f"agentos_new:{request.user_id}_{request.thread_id}"\n        config = {"configurable": {"thread_id": session_id, "user_id": request.user_id}}'
)

# 2. /api/v1/chat/stream
content = content.replace(
    '''            thread_id = request.thread_id if request.thread_id else "default_user"
            user_id = request.user_id if request.user_id else "default_user"
            messages = [HumanMessage(content=request.message)]
            config = {"configurable": {"thread_id": thread_id, "user_id": user_id}}''',
    '''            thread_id = request.thread_id if request.thread_id else "default_thread"
            user_id = request.user_id if request.user_id else "default_user"
            messages = [HumanMessage(content=request.message)]
            session_id = f"agentos_new:{user_id}_{thread_id}"
            config = {"configurable": {"thread_id": session_id, "user_id": user_id}}'''
)

# 3. get_chat_history
content = content.replace(
    '''@app.get("/api/v1/chat/history/{thread_id}")
def get_chat_history(thread_id: str):
    try:
        config = {"configurable": {"thread_id": thread_id}}''',
    '''@app.get("/api/v1/chat/history/{thread_id}")
def get_chat_history(thread_id: str, user_id: str = "default_user"):
    try:
        session_id = f"agentos_new:{user_id}_{thread_id}"
        config = {"configurable": {"thread_id": session_id}}'''
)

# 4. delete_chat_history
content = content.replace(
    '''@app.delete("/api/v1/chat/history/{thread_id}")
async def delete_chat_history(thread_id: str):''',
    '''@app.delete("/api/v1/chat/history/{thread_id}")
async def delete_chat_history(thread_id: str, user_id: str = "default_user"):
    session_id = f"agentos_new:{user_id}_{thread_id}"'''
)
content = content.replace(
    'cursor, keys = redis_conn.scan(cursor=cursor, match=f"*{thread_id}*")',
    'cursor, keys = redis_conn.scan(cursor=cursor, match=f"*{session_id}*")'
)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated main.py")
