import pickle
import faiss
import numpy as np

with open("modules/hs_classifier/metadata.pkl", "rb") as f:
    df = pickle.load(f)

index = faiss.read_index("modules/hs_classifier/hs_index.faiss")

print("DF length:", len(df))
print("Index length:", index.ntotal)

# Let's check row 0
print("\nRow 0 text:", df.iloc[0]["description"])
vec = index.reconstruct(0)
print("Row 0 vector sum:", np.sum(vec))

# Let's find Cocoa shells
cocoa_idx = df[df["hscode"].astype(str).str.contains("1802")].index
if not cocoa_idx.empty:
    iloc_idx = df.index.get_loc(cocoa_idx[0])
    print(f"\nCocoa shells iloc: {iloc_idx}")
    print("Cocoa shells text:", df.iloc[iloc_idx]["description"])
    
leather_idx = df[df["description"].str.contains("leather", case=False, na=False)].index
if not leather_idx.empty:
    iloc_idx = df.index.get_loc(leather_idx[0])
    print(f"\nLeather iloc: {iloc_idx}")
    print("Leather text:", df.iloc[iloc_idx]["description"])
