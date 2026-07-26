import os
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_community.embeddings import FastEmbedEmbeddings

# Load environment variables
load_dotenv()

# Persistence Directory for ChromaDB
DB_DIR = os.path.join(os.path.dirname(__file__), "chroma_db")

# Lightweight CPU-friendly Embeddings (Zero PyTorch / Low RAM overhead)
embeddings = FastEmbedEmbeddings(model_name="BAAI/bge-small-en-v1.5")

# Initialize Chroma Vector Store
vector_store = Chroma(
    collection_name="agent_memory",
    embedding_function=embeddings,
    persist_directory=DB_DIR
)

def add_to_memory(text: str, metadata: dict = None) -> str:
    """
    Saves a given text snippet into ChromaDB vector store.
    """
    try:
        if metadata is None:
            metadata = {"source": "user_input"}
            
        vector_store.add_texts(texts=[text], metadatas=[metadata])
        return f"Fact successfully stored in long-term memory: '{text}'"
    except Exception as e:
        return f"Error saving to memory: {str(e)}"

def search_memory(query: str, k: int = 3) -> list:
    """
    Searches ChromaDB for relevant memory facts based on query similarity.
    """
    try:
        results = vector_store.similarity_search(query, k=k)
        return [doc.page_content for doc in results]
    except Exception as e:
        print(f"Error reading memory: {e}")
        return []
