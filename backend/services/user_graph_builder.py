from fastapi import FastAPI, UploadFile, File
import pandas as pd
import io
import networkx as nx
from ContractLens.backend.services.dynamic_graph_builder import build_dynamic_graph  
app = FastAPI()


@app.post("/build-graph/")
async def build_graph_endpoint(file: UploadFile = File(...)):
    try:
        content = await file.read()

        df = pd.read_csv(io.BytesIO(content))
        print("COLUMNS:", df.columns) 

        text = "\n".join(df["clause_text"].astype(str))

        G = build_dynamic_graph(text)

        return nx.node_link_data(G)

    except Exception as e:
        return {"error": str(e)}