# explainer_app/utils/vector_store.py
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")
client = chromadb.PersistentClient(path="./chroma_db")

# ✅ Always use get_or_create_collection to avoid errors
collection = client.get_or_create_collection(name="code_chunks")

def embed_text(text):
    return model.encode(text).tolist()

def store_code_chunks(chunks):
    for chunk in chunks:
        embedding = embed_text(chunk['content'])
        collection.add(
            documents=[chunk['content']],
            metadatas=[{"filename": chunk['filename']}],
            ids=[chunk['id']],
            embeddings=[embedding]
        )

# ✅ Only return chunks relevant to BOTH the question and the filename
def retrieve_relevant_chunks(question, filename, top_k=5):
    embedding = embed_text(question)

    results = collection.query(
        query_embeddings=[embedding],
        n_results=top_k,
        include=["documents", "metadatas"],
        where={"filename": filename}  # ✅ filter by file
    )

    chunks = [
        doc for doc in results["documents"][0]
    ]

    return "\n\n".join(chunks)

