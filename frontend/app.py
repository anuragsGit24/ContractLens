from __future__ import annotations

import requests
import streamlit as st


def _get_api_base() -> str:
    try:
        return str(st.secrets["api_base"])
    except Exception:
        return "http://127.0.0.1:8000"


API_BASE = _get_api_base()

st.set_page_config(page_title="ContractLens", layout="wide")
st.title("ContractLens")
st.caption("Indian legal contract risk and contradiction analyzer")

pdf = st.file_uploader("Upload business contract PDF", type=["pdf"])

if st.button("Analyze"):
    if not pdf:
        st.error("Please upload a PDF first")
    else:
        with st.spinner("Uploading contract..."):
            upload = requests.post(
                f"{API_BASE}/v1/contracts/upload",
                files={"file": (pdf.name, pdf.getvalue(), "application/pdf")},
                timeout=180,
            )
            upload.raise_for_status()
            upload_payload = upload.json()

        with st.spinner("Running analysis pipeline..."):
            analyze = requests.post(
                f"{API_BASE}/v1/contracts/analyze",
                json={
                    "contract_path": upload_payload.get("json_path") or upload_payload["stored_path"],
                    "explain_max_clauses": 0,
                    "law_check_max_clauses": 8,
                },
                timeout=180,
            )
            analyze.raise_for_status()
            result = analyze.json()

        st.success("Analysis complete")

        st.subheader("Graph Nodes")
        nodes = [
            {"id": c.get("index"), "text": c.get("text", "")}
            for c in result.get("clauses", [])
        ]
        if nodes:
            st.write(nodes)
        else:
            st.info("No graph nodes were generated for this document.")

        st.subheader("Graph Edges")
        edges = [
            {
                "source": e.get("source_index"),
                "target": e.get("target_index"),
                "similarity": e.get("similarity"),
            }
            for e in result.get("graph_edges", [])
        ]
        if edges:
            st.write(edges)
        else:
            st.info("No graph edges were generated for this document.")

        st.subheader("High Risk Clauses")
        high_risk_count = 0
        for item in result.get("risks", []):
            if item.get("risk_level") == "high":
                high_risk_count += 1
                st.write(
                    f"Clause {item['clause_index']}: {item['top_category']} (score={item['top_score']:.3f})"
                )
        if high_risk_count == 0:
            st.info("No high-risk clauses found under current thresholds.")

        medium_risk_count = sum(1 for item in result.get("risks", []) if item.get("risk_level") == "medium")
        st.caption(f"Risk summary: high={high_risk_count}, medium={medium_risk_count}, total={len(result.get('risks', []))}")

        st.subheader("Internal Contradictions")
        contradiction_count = 0
        for c in result.get("internal_contradictions", []):
            contradiction_count += 1
            st.write(
                f"Clause {c['clause_a_index']} vs Clause {c['clause_b_index']} "
                f"(score={c['contradiction_score']:.3f})"
            )
        if contradiction_count == 0:
            st.info("No contradiction/tension pairs met the current conflict thresholds.")

        st.subheader("Explanations")
        for e in result.get("explanations", []):
            st.markdown(f"### Clause {e['clause_index']}")
            st.write(e.get("explanation", ""))
            if e.get("warning"):
                st.warning(e["warning"])
