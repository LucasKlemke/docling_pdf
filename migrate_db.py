import chromadb
from dotenv import load_dotenv
from supabase import create_client
import uuid
import threading
from dotenv import load_dotenv
import os

load_dotenv()

url = os.environ["SUPABASE_URL"]
key = os.environ["SUPABASE_KEY"]


def generate_uuid():
    return str(uuid.uuid4())


db = chromadb.PersistentClient(path="./chroma")
collection = db.get_collection(name="docling_rag")

collections = db.list_collections()
# [Collection(name=docling_rag)]


model = collection.get_model()
# id=UUID('ab51b9d4-fd07-409a-a058-6e88c071bd3d') name='docling_rag' configuration_json={'hnsw': {'space': 'l2', 'ef_construction': 100, 'ef_search': 100, 'max_neighbors': 16, 'resize_factor': 1.2, 'sync_threshold': 1000}, 'spann': None, 'embedding_function': {'name': 'default', 'type': 'known', 'config': {}}} metadata=None dimension=1536 tenant='default_tenant' database='default_database' version=0 log_position=0

results = collection.get(include=["embeddings", "documents", "metadatas"])


supabase = create_client(url, key)


def insert_chunk(document, meta, id_, embedding):
    print(
        f"\nMetadata: {meta}\nDocument: {document}\nID: {id_}\nEmbedding: {embedding}\n"
    )
    supabase.table("guyton_chunks").insert(
        {
            "id": generate_uuid(),
            "document": document,
            "page": meta.get("page"),
            "embedding": embedding.tolist(),
        }
    ).execute()


threads = []
for documents, meta, id_, embeddings in zip(
    results["documents"],
    results["metadatas"],
    results["ids"],
    results["embeddings"],
):
    t = threading.Thread(target=insert_chunk, args=(documents, meta, id_, embeddings))
    threads.append(t)

# Start threads in batches of 8
for i in range(0, len(threads), 8):
    batch = threads[i : i + 8]
    for t in batch:
        t.start()
    for t in batch:
        t.join()
