"""
HS Classifier - Hybrid AI Classification Engine
================================================
Combines semantic embeddings with keyword matching, domain rules, and
confidence calibration for accurate HS code classification.
"""
import os
import pickle
import faiss
import re
from sentence_transformers import SentenceTransformer
from modules.hs_classifier.build_index import build_faiss_index

DIR = os.path.dirname(os.path.abspath(__file__))
FAISS_PATH = os.path.join(DIR, "hs_index.faiss")
METADATA_PATH = os.path.join(DIR, "metadata.pkl")

# Global variables for caching model/index
_model = None
_index = None
_df = None

# ── Domain Keyword Maps ──────────────────────────────────────────────────────
# Maps product keywords to HS chapter prefixes to boost
DOMAIN_RULES = {
    # Chapter 42 – Articles of leather
    "42": ["leather", "handbag", "purse", "wallet", "satchel", "clutch", "bag", "luggage", "suitcase", "briefcase", "tote"],
    # Chapter 61/62 – Textiles / Apparel
    "61": ["shirt", "t-shirt", "tshirt", "blouse", "jersey", "sweater", "apparel", "garment", "clothing", "cotton", "knit"],
    "62": ["trouser", "pants", "skirt", "jacket", "coat", "suit", "dress", "woven", "apparel"],
    # Chapter 85 – Electrical machinery
    "85": ["battery", "lithium", "charger", "solar panel", "electronics", "circuit", "semiconductor", "phone", "laptop", "computer", "electrical"],
    # Chapter 87 – Vehicles
    "87": ["car", "vehicle", "automobile", "truck", "motorcycle", "bicycle"],
    # Chapter 08 – Edible fruits
    "08": ["mango", "apple", "banana", "fruit", "orange", "grape", "fresh fruit"],
    # Chapter 30 – Pharmaceuticals
    "30": ["tablet", "medicine", "pharmaceutical", "drug", "capsule", "syrup", "injection", "medical"],
    # Chapter 84 – Machinery
    "84": ["machine", "machinery", "cnc", "industrial", "engine", "pump", "compressor", "turbine"],
    # Chapter 27 – Petroleum
    "27": ["crude oil", "petroleum", "diesel", "fuel", "gasoline", "kerosene"],
    # Chapter 15 – Edible fats and oils
    "15": ["palm oil", "cooking oil", "vegetable oil", "sunflower oil"],
    # Chapter 71 – Gems, jewellery
    "71": ["diamond", "gold", "silver", "jewellery", "jewelry", "gem", "gemstone"],
    # Chapter 94 – Furniture
    "94": ["furniture", "sofa", "chair", "table", "bed", "cabinet", "wardrobe"],
}

# Penalty chapters for query types (query_keyword -> [bad_chapters])
PENALTY_RULES = {
    ("leather", "bag", "purse", "handbag", "wallet"): ["24", "02", "22", "04", "10", "11"],
    ("fruit", "mango", "apple", "banana"): ["24", "22", "85", "87"],
    ("shirt", "t-shirt", "blouse", "apparel"): ["24", "02", "22", "84"],
    ("battery", "lithium", "electronic"): ["02", "22", "24", "08"],
}

# Query expansion map
QUERY_EXPANSION = {
    "leather handbag": "leather handbag purse bag fashion accessory ladies bag carry bag leather goods",
    "handbag": "handbag purse bag women bag leather bag fashion accessory",
    "purse": "purse handbag wallet leather bag pouch carry bag",
    "wallet": "wallet purse coin purse leather billfold card holder",
    "leather bag": "leather bag purse handbag travel bag briefcase",
    "t-shirt": "t-shirt shirt tshirt men apparel clothing cotton garment textile",
    "tshirt": "t-shirt shirt tshirt men apparel clothing cotton garment textile",
    "battery": "battery lithium ion battery cell power storage rechargeable electrical",
    "solar panel": "solar panel photovoltaic cell solar module renewable energy electrical",
    "mango": "fresh mango tropical fruit edible fruit",
    "pharmaceutical": "pharmaceutical medicine tablet capsule drug medicament",
    "cnc machine": "cnc machine industrial machine tool machining center metal working",
    "crude palm oil": "palm oil vegetable oil edible oil fatty acid",
}


def get_mode():
    return "Hybrid AI (Semantic + Keyword + Rules)"


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


def normalize_query(query: str) -> str:
    """Lowercase, remove extra spaces, strip punctuation."""
    q = query.lower().strip()
    q = re.sub(r"[^\w\s-]", " ", q)
    q = re.sub(r"\s+", " ", q)
    return q


def expand_query(query: str) -> str:
    """Expand short product descriptions into richer context for better embedding."""
    q_lower = query.lower().strip()
    # Direct match in expansion map
    for key, expansion in QUERY_EXPANSION.items():
        if key in q_lower:
            return expansion
    return query


def get_domain_boost(query_lower: str, hscode: str) -> float:
    """Return boost score if hscode chapter matches query domain keywords."""
    boost = 0.0
    for chapter_prefix, keywords in DOMAIN_RULES.items():
        if hscode.startswith(chapter_prefix):
            for kw in keywords:
                if kw in query_lower:
                    boost += 0.35
                    break  # One match per chapter is enough
    return min(boost, 0.5)  # Cap boost


def get_penalty(query_lower: str, hscode: str) -> float:
    """Return penalty if hscode chapter is clearly unrelated to query domain."""
    for query_keywords, bad_chapters in PENALTY_RULES.items():
        if any(kw in query_lower for kw in query_keywords):
            if any(hscode.startswith(ch) for ch in bad_chapters):
                return 0.6
    return 0.0


def get_keyword_match_score(query: str, description: str) -> float:
    """Jaccard-style keyword overlap between query and HS description."""
    q_words = set(re.sub(r"[^\w\s]", " ", query.lower()).split())
    d_words = set(re.sub(r"[^\w\s]", " ", description.lower()).split())
    # Remove very short stop words
    stopwords = {"of", "the", "a", "an", "in", "for", "and", "or", "to", "is", "are", "not"}
    q_words -= stopwords
    d_words -= stopwords
    if not q_words:
        return 0.0
    common = q_words.intersection(d_words)
    return float(len(common)) / float(len(q_words))


def calibrate_confidence(final_score: float) -> float:
    """Map hybrid final score to a meaningful confidence percentage."""
    if final_score >= 0.70:
        conf = 90.0 + ((final_score - 0.70) / 0.30) * 9.0  # 90–99%
    elif final_score >= 0.50:
        conf = 75.0 + ((final_score - 0.50) / 0.20) * 15.0  # 75–90%
    elif final_score >= 0.30:
        conf = 50.0 + ((final_score - 0.30) / 0.20) * 25.0  # 50–75%
    else:
        conf = max(10.0, final_score * 100.0)
    return float(min(99.9, conf))


def detect_product_category(query_lower: str) -> str:
    """Simple rule-based product category detection for XAI display."""
    if any(k in query_lower for k in ["leather", "handbag", "wallet", "purse", "bag"]):
        return "Articles of Leather / Travel Goods"
    if any(k in query_lower for k in ["shirt", "t-shirt", "blouse", "apparel", "garment", "cotton"]):
        return "Textiles & Apparel"
    if any(k in query_lower for k in ["battery", "lithium", "solar", "electrical", "electronics"]):
        return "Electrical Equipment & Electronics"
    if any(k in query_lower for k in ["machine", "cnc", "industrial", "pump", "motor"]):
        return "Industrial Machinery"
    if any(k in query_lower for k in ["fruit", "mango", "apple", "banana", "vegetable"]):
        return "Edible Fruits & Vegetables"
    if any(k in query_lower for k in ["tablet", "medicine", "pharmaceutical", "capsule"]):
        return "Pharmaceuticals"
    if any(k in query_lower for k in ["oil", "petroleum", "fuel", "crude"]):
        return "Oils & Petroleum Products"
    if any(k in query_lower for k in ["diamond", "gold", "silver", "jewellery", "gem"]):
        return "Precious Metals & Jewellery"
    return "General Merchandise"


def classify(query: str, top_k: int = 20):
    """
    Hybrid AI Classification:
    1. Normalize & expand query
    2. Generate embedding
    3. FAISS similarity search (broad candidate set)
    4. Keyword match scoring
    5. Domain rule boost/penalty
    6. Hybrid re-ranking (60% semantic + 30% keyword + 10% rules)
    7. Confidence calibration
    8. Return top 5 with XAI explanation
    """
    load_resources()

    normalized_query = normalize_query(query)
    expanded_query = expand_query(normalized_query)
    q_lower = normalized_query

    # Generate embedding from expanded query
    embedding = _model.encode([expanded_query])
    embedding = embedding.astype("float32")

    # Broad FAISS search
    distances, ids = _index.search(embedding, top_k)

    candidates = []

    for rank, i in enumerate(ids[0]):
        if i < 0:  # FAISS may return -1 for unfound
            continue
        row = _df.iloc[i]

        raw_distance = float(distances[0][rank])  # Force Python float

        # L2 distance → similarity: lower distance = higher similarity
        sem_sim = float(1.0 / (1.0 + raw_distance))

        hscode = str(row.get("hscode", "")).strip()
        desc = str(row.get("description", "")).strip()
        level = int(row.get("level", 0))

        # Keyword match score
        kw_score = float(get_keyword_match_score(q_lower, desc))

        # Domain boost
        domain_boost = float(get_domain_boost(q_lower, hscode))

        # Penalty for clearly unrelated categories
        penalty = float(get_penalty(q_lower, hscode))

        # Hybrid final score: 60% semantic + 30% keyword + 10% rules - penalty
        final_score = float(
            (0.60 * sem_sim) + (0.30 * kw_score) + (0.10 * domain_boost) - penalty
        )

        # Calibrated confidence
        conf = calibrate_confidence(final_score)

        # Matched keywords for XAI
        q_words = set(q_lower.split())
        d_words = set(re.sub(r"[^\w\s]", " ", desc.lower()).split())
        matched_kws = sorted(list(q_words.intersection(d_words)))

        candidates.append({
            "hscode": hscode,
            "description": desc,
            "level": level,
            "confidence": round(conf, 1),
            "final_score": round(final_score, 6),
            "sem_similarity": round(sem_sim, 4),
            "keyword_score": round(kw_score, 4),
            "domain_boost": round(domain_boost, 4),
            "matched_keywords": matched_kws,
            "domain_boost_applied": bool(domain_boost > 0),
        })

    # Sort by hybrid final_score descending
    candidates.sort(key=lambda x: x["final_score"], reverse=True)

    # Take top 5
    results = []
    for idx, c in enumerate(candidates[:5]):
        c["rank"] = idx + 1
        # Remove intermediate score (not needed in response but keep for debugging if needed)
        results.append(c)

    top_match = results[0] if results else None

    # Build classification path
    if top_match:
        hs = top_match["hscode"]
        chapter_num = hs[:2] if len(hs) >= 2 else ""
        heading_num = hs[:4] if len(hs) >= 4 else ""
        subheading_num = hs[:6] if len(hs) >= 6 else ""

        path_parts = []
        if chapter_num:
            path_parts.append(f"Chapter {chapter_num}")
        if heading_num:
            path_parts.append(f"Heading {heading_num}")
        if subheading_num and subheading_num != heading_num:
            path_parts.append(f"Subheading {subheading_num}")
        path_parts.append(f"Final Code {hs}")
        classification_path = " → ".join(path_parts)

        detected_category = detect_product_category(q_lower)
        rules_applied = []
        if top_match["domain_boost_applied"]:
            rules_applied.append(f"Domain boost applied for Chapter {top_match['hscode'][:2]}")
        if get_penalty(q_lower, top_match["hscode"]) == 0 and any(
            get_penalty(q_lower, c["hscode"]) > 0 for c in candidates[5:]
        ):
            rules_applied.append("Penalty rules excluded unrelated categories")
    else:
        classification_path = ""
        detected_category = "Unknown"
        rules_applied = []

    explainable_ai = {
        "matched_keywords": top_match["matched_keywords"] if top_match else [],
        "domain_boost_applied": bool(top_match["domain_boost_applied"]) if top_match else False,
        "expanded_query": expanded_query,
        "detected_category": detected_category,
        "rules_applied": rules_applied,
        "semantic_similarity": top_match["sem_similarity"] if top_match else 0.0,
        "keyword_score": top_match["keyword_score"] if top_match else 0.0,
    }

    return {
        "query": query,
        "mode": "Hybrid AI (Semantic + Keyword + Rules)",
        "top_match": top_match,
        "classification_path": classification_path,
        "explainable_ai": explainable_ai,
        "results": results,
    }


if __name__ == "__main__":
    import sys
    q = sys.argv[1] if len(sys.argv) > 1 else "Cotton T-shirt"
    import json
    print(json.dumps(classify(q), indent=2))
