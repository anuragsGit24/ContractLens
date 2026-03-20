import re
import pickle
import numpy as np
import networkx as nx
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

BASE_DIR = Path(__file__).resolve().parent.parent
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

    for i, j in internal_G.edges():

        # TOP-K matches instead of argmax
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

        # fallback (if nothing passes threshold)
        if not matches_i:
            idx = np.argmax(sim_matrix[i])
            matches_i = [(clause_types[idx], float(sim_matrix[i][idx]))]

        if not matches_j:
            idx = np.argmax(sim_matrix[j])
            matches_j = [(clause_types[idx], float(sim_matrix[j][idx]))]

        # compute risk from ALL matches (avg)
        def get_avg_risk(matches):
            risks = []
            for ct, _ in matches:
                r = base_G.nodes[ct].get("dominant_risk", "medium")
                risks.append(risk_map[r])
            return sum(risks) / len(risks)

        risk_i = get_avg_risk(matches_i)
        risk_j = get_avg_risk(matches_j)

        edge_risk_score = (risk_i + risk_j) / 2

        # better difference score
        all_scores = [s for _, s in matches_i + matches_j]
        avg_sim = sum(all_scores) / len(all_scores) if all_scores else 0
        diff_score = 1 - avg_sim

        # assign attributes
        internal_G[i][j]["risk"] = float(edge_risk_score)
        internal_G[i][j]["difference"] = float(diff_score)

        # richer base node info
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