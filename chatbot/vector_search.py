import faiss
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
import os

EMBEDDING_PATH = os.path.join(os.path.dirname(__file__), 'embeddings/index.faiss')
METADATA_PATH = os.path.join(os.path.dirname(__file__), 'embeddings/metadata.pkl')

model = SentenceTransformer("all-MiniLM-L6-v2")

with open(METADATA_PATH, "rb") as f:
    metadata = pickle.load(f)

index = faiss.read_index(EMBEDDING_PATH)

def retrieve_context(user_input, k=5):
    embedding = model.encode([user_input])
    distances, indices = index.search(np.array(embedding).astype("float32"), k)
    return [metadata[i] for i in indices[0]]