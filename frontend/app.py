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
                timeout=120,
            )
            upload.raise_for_status()
            upload_payload = upload.json()

        with st.spinner("Running analysis pipeline..."):
            analyze = requests.post(
                f"{API_BASE}/v1/contracts/analyze",
                json={"contract_path": upload_payload["stored_path"]},
                timeout=300,
            )
            analyze.raise_for_status()
            result = analyze.json()

        st.success("Analysis complete")
        st.subheader("High Risk Clauses")
        for item in result.get("risks", []):
            if item.get("risk_level") == "high":
                st.write(
                    f"Clause {item['clause_index']}: {item['top_category']} (score={item['top_score']:.3f})"
                )

        st.subheader("Internal Contradictions")
        for c in result.get("internal_contradictions", []):
            st.write(
                f"Clause {c['clause_a_index']} vs Clause {c['clause_b_index']} "
                f"(score={c['contradiction_score']:.3f})"
            )

        st.subheader("Explanations")
        for e in result.get("explanations", []):
            st.markdown(f"### Clause {e['clause_index']}")
            st.write(e.get("explanation", ""))
            if e.get("warning"):
                st.warning(e["warning"])
