import os
from dotenv import load_dotenv
from langchain_postgres import PGVector
from langchain_community.embeddings import FastEmbedEmbeddings

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("NEON_DATABASE_URL", "")
# langchain_postgres requires psycopg3 sync or async URL. For simplicity, we use sync.
# Convert postgresql+asyncpg:// to postgresql+psycopg:// if needed, or just standard postgresql://
if "asyncpg" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("+asyncpg", "+psycopg")
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://")

# Remove query params for cleaner connection in PGVector if necessary, though sslmode=require might be needed.
if "?" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.split("?")[0]

# Append sslmode for Neon DB
if "sslmode=require" not in DATABASE_URL:
    DATABASE_URL += "?sslmode=require"

# Lightweight CPU-friendly Embeddings (Zero PyTorch / Low RAM overhead)
embeddings = FastEmbedEmbeddings(model_name="BAAI/bge-small-en-v1.5")

# Initialize PGVector Vector Store
if DATABASE_URL:
    try:
        vector_store = PGVector(
            embeddings=embeddings,
            collection_name="agent_memory",
            connection=DATABASE_URL,
            use_jsonb=True
        )
        vector_store.create_tables_if_not_exists()
    except Exception as e:
        print(f"Failed to initialize PGVector: {e}")
        vector_store = None
else:
    vector_store = None


def add_to_memory(text: str, metadata: dict = None) -> str:
    """
    Saves a given text snippet into PGVector store.
    """
    if not vector_store:
        return "Error: PGVector store is not initialized."
    try:
        if metadata is None:
            metadata = {"source": "user_input"}
            
        vector_store.add_texts(texts=[text], metadatas=[metadata])
        return f"Fact successfully stored in long-term memory: '{text}'"
    except Exception as e:
        return f"Error saving to memory: {str(e)}"

def search_memory(query: str, k: int = 3) -> list:
    """
    Searches PGVector for relevant memory facts based on query similarity.
    """
    if not vector_store:
        return []
    try:
        results = vector_store.similarity_search(query, k=k)
        return [doc.page_content for doc in results]
    except Exception as e:
        print(f"Error reading memory: {e}")
        return []
