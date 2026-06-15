import os
import chromadb
from chromadb.utils import embedding_functions

CHROMA_DB_PATH = os.path.join(os.path.expanduser("~"), ".support_triage_chroma")
KNOWLEDGE_BASE_DIR = "data/knowledge_base"

# Lightweight default embedding function (ONNX-based, no torch required)
embedding_function = embedding_functions.DefaultEmbeddingFunction()

client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

def build_knowledge_base():
    collection = client.get_or_create_collection(
        name="support_docs",
        embedding_function=embedding_function
    )

    # Clear existing entries to avoid duplicates on re-run
    existing = collection.get()
    if existing["ids"]:
        collection.delete(ids=existing["ids"])

    documents = []
    ids = []
    metadatas = []

    for filename in os.listdir(KNOWLEDGE_BASE_DIR):
        if filename.endswith(".txt"):
            filepath = os.path.join(KNOWLEDGE_BASE_DIR, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            documents.append(content)
            ids.append(filename)
            metadatas.append({"source": filename})

    collection.add(documents=documents, ids=ids, metadatas=metadatas)
    print(f"Added {len(documents)} documents to knowledge base.")
    return collection

def get_collection():
    return client.get_or_create_collection(
        name="support_docs",
        embedding_function=embedding_function
    )

def retrieve_context(query, n_results=2):
    collection = get_collection()
    results = collection.query(query_texts=[query], n_results=n_results)
    retrieved_docs = results["documents"][0]
    sources = [meta["source"] for meta in results["metadatas"][0]]
    return retrieved_docs, sources

if __name__ == "__main__":
    build_knowledge_base()
    # Quick test
    docs, sources = retrieve_context("Customer reports a data breach due to weak encryption")
    print("\nTest retrieval for a data breach query:")
    for doc, src in zip(docs, sources):
        print(f"\nFrom {src}:\n{doc[:200]}...")