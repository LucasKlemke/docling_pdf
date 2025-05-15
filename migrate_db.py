import chromadb
from dotenv import load_dotenv
from supabase import create_client
import uuid
import threading
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Get Supabase credentials from environment variables
url = os.environ["SUPABASE_URL"]
key = os.environ["SUPABASE_KEY"]

# Define batch size for concurrent inserts
BATCH_SIZE = 8  # Number of concurrent inserts


# Function to generate random UUIDs for primary keys
def generate_uuid():
    return str(uuid.uuid4())


# Initialize ChromaDB client with persistent storage
db = chromadb.PersistentClient(path="./chroma")
# Get the specific collection we want to migrate
collection = db.get_collection(name="books_rag")

# List all collections (this line isn't used later)
collections = db.list_collections()

# Get the model info (this line isn't used later)
model = collection.get_model()

# Retrieve all data from the ChromaDB collection including embeddings, documents and metadata
results = collection.get(include=["embeddings", "documents", "metadatas"])

# Initialize Supabase client
supabase = create_client(url, key)


# Function to insert a single chunk into Supabase
def insert_chunk(document, meta, id_, embedding):
    # Print debug information about the chunk being inserted
    print(
        f"\nMetadata: {meta}\nDocument: {document}\nID: {id_}\nEmbedding: {embedding}\n"
    )

    # Insert the data into Supabase table
    supabase.table("book_chunks").insert(
        {
            "id": generate_uuid(),  # Generate new UUID for each record
            "document": document,  # The text content
            "page": meta.get("page"),  # Get page number from metadata
            "bookName": meta.get("bookName"),  # Get book name from metadata
            "relatedSubject": meta.get("relatedSubject"),  # Get subject from metadata
            "url": meta.get("url"),
            "embedding": embedding.tolist(),  # Convert numpy array to list
        }
    ).execute()


# Create a list to hold all our threads
threads = []

# Prepare threads for each document in the collection
for documents, meta, id_, embeddings in zip(
    results["documents"],  # All document texts
    results["metadatas"],  # All metadata dictionaries
    results["ids"],  # All ChromaDB IDs
    results["embeddings"],  # All embedding vectors
):
    # Create a thread for each insert operation
    t = threading.Thread(target=insert_chunk, args=(documents, meta, id_, embeddings))
    threads.append(t)

# Process threads in batches to control concurrency
for i in range(0, len(threads), BATCH_SIZE):
    # Get the next batch of threads
    batch = threads[i : i + BATCH_SIZE]

    # Start all threads in the current batch
    for t in batch:
        t.start()

    # Wait for all threads in the current batch to complete
    for t in batch:
        t.join()
