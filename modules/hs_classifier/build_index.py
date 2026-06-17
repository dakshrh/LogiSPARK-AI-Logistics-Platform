import os
import pandas as pd
import faiss
import pickle
from sentence_transformers import SentenceTransformer

DIR = os.path.dirname(os.path.abspath(__file__))

def build_faiss_index():
    print("Loading data...")
    csv_path = os.path.join(DIR, "hs_level6.csv")
    df = pd.read_csv(csv_path)

    # Keep detailed rows only
    df = df[df["level"] >= 4]

    # Clean text
    df["text"] = (
        df["description"]
        .fillna("")
        .str.lower()
    )

    descriptions = df["text"].tolist()

    print("Loading model...")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    print("Generating embeddings...")
    embeddings = model.encode(descriptions, show_progress_bar=True)

    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)

    faiss.write_index(index, os.path.join(DIR, "hs_index.faiss"))

    with open(os.path.join(DIR, "metadata.pkl"), "wb") as f:
        pickle.dump(df, f)

    print("Index created.")

if __name__ == "__main__":
    build_faiss_index()