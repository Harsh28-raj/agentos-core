import asyncio
from app.db.postgres import init_db
from app.db.vector_store import vector_store

async def main():
    print("Creating core tables (EpisodicLog, UserToken)...")
    await init_db()
    
    print("Creating PGVector tables...")
    if vector_store:
        vector_store.create_tables_if_not_exists()
    else:
        print("Vector store not initialized!")
        
    print("All tables created successfully.")

if __name__ == "__main__":
    asyncio.run(main())
