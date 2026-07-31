import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("NEON_DATABASE_URL", os.getenv("DATABASE_URL"))

def run_migration():
    if not DATABASE_URL:
        print("DATABASE_URL not found!")
        return

    # Replace asyncpg with psycopg2 for synchronous execution
    sync_url = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    engine = create_engine(sync_url)

    alter_statements = [
        "ALTER TABLE episodic_logs ADD COLUMN IF NOT EXISTS action_taken VARCHAR;",
        "ALTER TABLE episodic_logs ADD COLUMN IF NOT EXISTS original_args JSONB;",
        "ALTER TABLE episodic_logs ADD COLUMN IF NOT EXISTS modified_args JSONB;",
        "ALTER TABLE episodic_logs ADD COLUMN IF NOT EXISTS human_feedback TEXT;"
    ]

    try:
        with engine.connect() as conn:
            for stmt in alter_statements:
                print(f"Executing: {stmt}")
                conn.execute(text(stmt))
            conn.commit()
            print("Migration successful! Added HITL columns to episodic_logs.")
    except Exception as e:
        print(f"Migration failed: {e}")

if __name__ == "__main__":
    run_migration()
