import re
import pickle
from collections import defaultdict, Counter
from pathlib import Path
import pandas as pd
import networkx as nx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


BASE_DIR = Path(__file__).resolve().parent.parent
EMBED_PATH = BASE_DIR / "data" / "default" / "embeddings.npy"
CSV_PATH = BASE_DIR / "data" / "default" / "base_contract_clauses.csv"
GRAPH_PATH = BASE_DIR / "data" / "default" / "legal_graph.pkl"


SIMILARITY_THRESH = 0.25


def load_data(csv_path):
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip()
    df["clause_type"] = df["clause_type"].str.strip()
    df["risk_level"] = df["risk_level"].str.strip().str.lower()
    df["clause_text"] = df["clause_text"].fillna("").str.strip()
    return df


def build_graph(df):
    clause_types = df["clause_type"].unique().tolist()

    type_text = (
        df.groupby("clause_type")["clause_text"]
        .apply(lambda x: " ".join(x))
        .to_dict()
    )

    G = nx.Graph()

    # risk nodes
    for r in ["low", "medium", "high"]:
        G.add_node(r, node_type="risk")

    clause_count = df["clause_type"].value_counts().to_dict()

    def dominant_risk(ct):
        risks = df[df["clause_type"] == ct]["risk_level"]
        return risks.mode()[0] if not risks.empty else "medium"

    # clause nodes
    for ct in clause_types:
        G.add_node(
            ct,
            node_type="clause",
            dominant_risk=dominant_risk(ct),
            count=clause_count.get(ct, 1),
            text=type_text.get(ct, ""),
        )

    # risk edges
    for (ct, risk), cnt in Counter(zip(df["clause_type"], df["risk_level"])).items():
        G.add_edge(ct, risk, edge_type="has_risk", weight=cnt)

    # TF-IDF similarity
    vectorizer = TfidfVectorizer(stop_words="english")
    corpus = [type_text[ct] for ct in clause_types]
    tfidf = vectorizer.fit_transform(corpus)
    sim = cosine_similarity(tfidf)

    for i in range(len(clause_types)):
        for j in range(i + 1, len(clause_types)):
            if sim[i][j] >= SIMILARITY_THRESH:
                G.add_edge(
                    clause_types[i],
                    clause_types[j],
                    edge_type="similar_to",
                    weight=float(sim[i][j]),
                )

    # cross-ref edges
    ref_pat = re.compile(
        r"\b(section|clause|article)\s+[\d\.]+", re.IGNORECASE
    )

    ref_map = defaultdict(set)
    for ct, text in type_text.items():
        for ref in ref_pat.findall(text.lower()):
            ref_map[ref].add(ct)

    for types in ref_map.values():
        types = list(types)
        for i in range(len(types)):
            for j in range(i + 1, len(types)):
                G.add_edge(types[i], types[j], edge_type="cross_ref")

    return G, clause_types


if __name__ == "__main__":
    print("Loading data...")
    df = load_data(CSV_PATH)

    print("Building graph...")
    G, clause_types = build_graph(df)

    print("Generating embeddings...")
    # embeddings = model.encode(clause_types)

    print("Saving graph...")
    with open(GRAPH_PATH, "wb") as f:
        pickle.dump((G, clause_types), f)

    print("Saving embeddings...")
    import numpy as np

    # np.save(EMBED_PATH, embeddings)

    print("Done ✅")