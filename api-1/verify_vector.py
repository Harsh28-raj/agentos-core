import asyncio
from app.db.vector_store import add_to_memory, search_memory
from app.db.postgres import init_db

async def verify():
    print("Initializing Database...")
    await init_db()
    
    print("\n--- Testing Vector Storage ---")
    test_fact = "Neon Postgres is officially the new vector store for the AgentOS system."
    metadata = {"source": "verification_test", "status": "active"}
    
    print(f"Adding memory: '{test_fact}'")
    add_result = add_to_memory(test_fact, metadata)
    print(f"Result: {add_result}")
    
    print("\n--- Testing Vector Retrieval ---")
    search_query = "What is the new vector store?"
    print(f"Querying for: '{search_query}'")
    results = search_memory(search_query, k=1)
    
    print("\nSearch Results:")
    if results:
        for idx, res in enumerate(results):
            print(f"[{idx+1}] {res}")
            
        if test_fact in results[0]:
            print("\n✅ Verification Successful: Memory was successfully embedded, stored in Neon Postgres, and retrieved using similarity search!")
        else:
            print("\n❌ Verification Failed: Retrieved memory does not match the test fact.")
    else:
        print("\n❌ Verification Failed: No results returned.")

if __name__ == "__main__":
    asyncio.run(verify())
