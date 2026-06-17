import os
import pickle
import faiss
from sentence_transformers import SentenceTransformer
from modules.hs_classifier.build_index import build_faiss_index

DIR = os.path.dirname(os.path.abspath(__file__))
FAISS_PATH = os.path.join(DIR, "hs_index.faiss")
METADATA_PATH = os.path.join(DIR, "metadata.pkl")

# Global variables for caching model/index
_model = None
_index = None
_df = None

def get_mode():
    return "FAISS + SentenceTransformers"

def load_resources():
    global _model, _index, _df
    
    if not os.path.exists(FAISS_PATH) or not os.path.exists(METADATA_PATH):
        print("Index not found. Building index automatically...")
        build_faiss_index()
        
    if _model is None:
        print("Loading model...")
        _model = SentenceTransformer("all-MiniLM-L6-v2")

    if _index is None:
        print("Loading index...")
        _index = faiss.read_index(FAISS_PATH)

    if _df is None:
        print("Loading metadata...")
        with open(METADATA_PATH, "rb") as f:
            _df = pickle.load(f)

def build_index_if_needed():
    if not os.path.exists(FAISS_PATH) or not os.path.exists(METADATA_PATH):
        print("Index not found. Building index automatically...")
        build_faiss_index()
        
def classify(query: str, top_k: int = 5):
    load_resources()
    
    embedding = _model.encode([query])
    distances, ids = _index.search(embedding, top_k)
    
    results = []
    top_match = None
    
    for rank, i in enumerate(ids[0]):
        row = _df.iloc[i]
        distance = distances[0][rank]
        confidence = (1 / (1 + distance)) * 100
        
        result_item = {
            "rank": rank + 1,
            "hscode": str(row.get("hscode", "")),
            "description": str(row.get("description", "")),
            "level": int(row.get("level", 0)),
            "confidence": float(confidence)
        }
        
        results.append(result_item)
        
        if rank == 0:
            top_match = {
                "hscode": result_item["hscode"],
                "description": result_item["description"],
                "confidence": result_item["confidence"]
            }
            
    hs = top_match["hscode"]
    path_parts = []
    if len(hs) >= 2:
        path_parts.append(f"Chapter {hs[:2]}")
    if len(hs) >= 4:
        path_parts.append(f"Heading {hs[:4]}")
    if len(hs) >= 6:
        path_parts.append(f"Subheading {hs[:6]}")
    path_parts.append(f"Full Code {hs}")
    classification_path = " → ".join(path_parts)
    
    return {
        "query": query,
        "mode": "FAISS",
        "top_match": top_match,
        "classification_path": classification_path,
        "results": results
    }

if __name__ == "__main__":
    import sys
    q = sys.argv[1] if len(sys.argv) > 1 else "Cotton T-shirt"
    print(classify(q))
