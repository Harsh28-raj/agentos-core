from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import os

# Database ko save karne ka path (Yeh folder apne aap ban jayega)
DB_DIR = os.path.join(os.getcwd(), "chroma_db")

# HuggingFace ka free aur fast embedding model
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# ChromaDB Initialize karein
vector_db = Chroma(
    collection_name="agent_os_memory",
    embedding_function=embeddings,
    persist_directory=DB_DIR
)

def add_to_memory(text: str, metadata: dict = None):
    """Text ko vector database mein hamesha ke liye save karein"""
    vector_db.add_texts(texts=[text], metadatas=[metadata] if metadata else None)
    return "Memory saved successfully!"

def search_memory(query: str, k: int = 2):
    """Database se purani yaadasht dhoondh kar layein"""
    results = vector_db.similarity_search(query, k=k)
    return [doc.page_content for doc in results]