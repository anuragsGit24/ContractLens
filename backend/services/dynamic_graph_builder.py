import re
import pickle
import numpy as np
import networkx as nx
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

BASE_DIR = Path(__file__).resolve().parent.parent.parent
EMBED_PATH = BASE_DIR / "data" / "default" / "embeddings.npy"
GRAPH_PATH = BASE_DIR / "data" / "default" / "legal_graph.pkl"
model = SentenceTransformer("all-MiniLM-L6-v2")


# ─────────────────────────────────────────
# 1. LOAD BASE GRAPH
# ─────────────────────────────────────────
def load_base_graph():
    with open(GRAPH_PATH, "rb") as f:
        base_G, clause_types = pickle.load(f)

    embeddings = np.load(EMBED_PATH)
    return base_G, clause_types, embeddings


# ─────────────────────────────────────────
# 2. SPLIT TEXT → CLAUSES
# ─────────────────────────────────────────
def split_clauses(text):
    clauses = re.split(r'\n+|\.\s+', text)
    return [c.strip() for c in clauses if len(c.strip()) > 20]


# ─────────────────────────────────────────
# 3. BUILD INTERNAL GRAPH
# ─────────────────────────────────────────
def build_internal_graph(clauses):
    G = nx.Graph()

    for i, clause in enumerate(clauses):
        G.add_node(i, text=clause)

    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf = vectorizer.fit_transform(clauses)
    sim = cosine_similarity(tfidf)

    for i in range(len(clauses)):
        for j in range(i + 1, len(clauses)):
            if sim[i][j] > 0:
                G.add_edge(i, j, base_weight=float(sim[i][j]))

    return G


# ─────────────────────────────────────────
# 4. ASSIGN WEIGHTS FROM BASE GRAPH
# ─────────────────────────────────────────
def assign_weights(internal_G, clauses, base_G, clause_types, base_embeddings):
    clause_embeddings = model.encode(clauses)

    # similarity of each clause to base clause types
    sim_matrix = cosine_similarity(clause_embeddings, base_embeddings)

    risk_map = {"low": 1, "medium": 2, "high": 3}

    top_k = 3
    threshold = 0.3

    #ignore noisy generic clause types
    IGNORE_TYPES = {"Agreement Date", "Effective Date", "Definitions"}

    #precompute clause-clause similarity (efficient)
    clause_sim_matrix = cosine_similarity(clause_embeddings)

    SIM_THRESHOLD = 0.5

    for i, j in list(internal_G.edges()):

        # ─────────────────────────────
        # 1. TOP-K base matches
        # ─────────────────────────────
        matches_i = [
            (clause_types[idx], float(sim_matrix[i][idx]))
            for idx in np.argsort(sim_matrix[i])[::-1][:top_k]
            if sim_matrix[i][idx] > threshold
        ]

        matches_j = [
            (clause_types[idx], float(sim_matrix[j][idx]))
            for idx in np.argsort(sim_matrix[j])[::-1][:top_k]
            if sim_matrix[j][idx] > threshold
        ]

        # fallback
        if not matches_i:
            idx = np.argmax(sim_matrix[i])
            matches_i = [(clause_types[idx], float(sim_matrix[i][idx]))]

        if not matches_j:
            idx = np.argmax(sim_matrix[j])
            matches_j = [(clause_types[idx], float(sim_matrix[j][idx]))]

        # ─────────────────────────────
        # 2. REMOVE noisy types
        # ─────────────────────────────
        matches_i = [(ct, s) for ct, s in matches_i if ct not in IGNORE_TYPES]
        matches_j = [(ct, s) for ct, s in matches_j if ct not in IGNORE_TYPES]

        if not matches_i or not matches_j:
            continue

        # ─────────────────────────────
        # 3. compute node risks
        # ─────────────────────────────
        def get_avg_risk(matches):
            return sum(
                risk_map[base_G.nodes[ct].get("dominant_risk", "medium")]
                for ct, _ in matches
            ) / len(matches)

        risk_i = get_avg_risk(matches_i)
        risk_j = get_avg_risk(matches_j)

        # ─────────────────────────────
        # 4. clause-to-clause similarity
        # ─────────────────────────────
        clause_sim = clause_sim_matrix[i][j]

        if clause_sim < SIM_THRESHOLD:
            internal_G.remove_edge(i, j)
            continue

        # ─────────────────────────────
        # 5. FINAL risk (clean formula)
        # ─────────────────────────────
        edge_risk = clause_sim * min(risk_i, risk_j)
        # normalize to 1–3 range
        edge_risk = max(1.0, min(3.0, edge_risk * 3))

        # ─────────────────────────────
        # 6. difference score
        # ─────────────────────────────
        all_scores = [s for _, s in matches_i + matches_j]
        avg_sim = sum(all_scores) / len(all_scores) if all_scores else 0
        diff_score = 1 - avg_sim

        # ─────────────────────────────
        # 7. assign attributes
        # ─────────────────────────────
        internal_G[i][j]["risk"] = float(round(edge_risk, 3))
        internal_G[i][j]["difference"] = float(round(diff_score, 3))

        internal_G[i][j]["base_nodes"] = {
            "node_i": matches_i,
            "node_j": matches_j
        }

    return internal_G


# ─────────────────────────────────────────
# 5. FULL PIPELINE
# ─────────────────────────────────────────
def build_dynamic_graph(text):
    base_G, clause_types, base_embeddings = load_base_graph()

    clauses = split_clauses(text)
    internal_G = build_internal_graph(clauses)

    final_G = assign_weights(
        internal_G,
        clauses,
        base_G,
        clause_types,
        base_embeddings
    )

    return final_G