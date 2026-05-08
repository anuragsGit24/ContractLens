from __future__ import annotations

import html
import random
import re
import tempfile
from datetime import datetime
from typing import Any

import requests
import streamlit as st
from streamlit.components.v1 import html as st_html

try:
	from pyvis.network import Network
except ImportError:
	Network = None


def _get_api_base() -> str:
	try:
		return str(st.secrets["api_base"])
	except Exception:
		return "http://127.0.0.1:8000"


API_BASE = _get_api_base()
NAV_ITEMS = ["Dashboard", "Analyse Contract", "Law Library", "Settings"]

LEGAL_TIPS = [
	"Section 27 of the Indian Contract Act renders most non-compete clauses void and unenforceable.",
	"A broad indemnity clause without caps can create uncapped downstream liability for small businesses.",
	"Always verify dispute resolution seat and governing law clauses align with your business jurisdiction.",
	"Penalty-style liquidated damages often fail unless they are a genuine pre-estimate of loss.",
	"Force majeure language should clearly define notice timelines and mitigation obligations.",
]

STATUTE_LIBRARY = [
	{
		"title": "Indian Contract Act 1872",
		"sections_indexed": 266,
		"categories": ["Unlawful Terms", "Breach & Remedies", "Restraint of Trade", "Void Agreements"],
		"relevant_sections": [
			"S.23 Unlawful Consideration",
			"S.27 Restraint of Trade",
			"S.73 Compensation for Loss",
			"S.74 Penalty Clauses",
		],
	},
	{
		"title": "Indian Penal Code 1860",
		"sections_indexed": 511,
		"categories": ["Cheating", "Criminal Breach", "Fraud Signals", "Misrepresentation"],
		"relevant_sections": [
			"S.405 Criminal Breach of Trust",
			"S.415 Cheating",
			"S.420 Cheating and Dishonestly Inducing Delivery",
			"S.463 Forgery",
		],
	},
	{
		"title": "Constitution of India 1950",
		"sections_indexed": 361,
		"categories": ["Fundamental Rights", "Public Policy", "Equality", "Due Process"],
		"relevant_sections": [
			"Article 14 Equality Before Law",
			"Article 19(1)(g) Freedom of Trade",
			"Article 21 Life and Personal Liberty",
			"Article 300A Right to Property",
		],
	},
]

st.set_page_config(page_title="ContractLens — Legal Risk Intelligence", layout="wide")


def _init_state() -> None:
	defaults = {
		"analysis_result": None,
		"analysis_history": [],
		"nav_page": "Dashboard",
		"settings_fast_mode": True,
		"high_threshold": 0.72,
		"medium_threshold": 0.58,
	}
	for key, value in defaults.items():
		if key not in st.session_state:
			st.session_state[key] = value

	if "legal_tip" not in st.session_state:
		st.session_state.legal_tip = random.choice(LEGAL_TIPS)


def _inject_styles() -> None:
	st.markdown(
		"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
	--bg: #F7F8FA;
	--card: #FFFFFF;
	--border: #E5E7EB;
	--text: #111827;
	--muted: #6B7280;
	--accent: #6366F1;
	--high-bg: #FEECEC;
	--high-text: #991B1B;
	--med-bg: #FFF4DB;
	--med-text: #92400E;
	--low-bg: #EAF8EE;
	--low-text: #166534;
	--info-bg: #EAF1FF;
	--info-text: #1E3A8A;
	--sidebar-bg: #1A1D23;
	--sidebar-text: #D1D5DB;
}

.stApp, .stApp * {
	font-family: 'Inter', 'Segoe UI', sans-serif;
}

.stApp {
	background: var(--bg);
	color: var(--text);
}

[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stSidebarCollapseButton"],
[data-testid="collapsedControl"] {
	display: none !important;
}

[data-testid="stMain"] {
	padding-top: 0.7rem;
}

[data-testid="stSidebar"] {
	background: var(--sidebar-bg);
	border-right: 1px solid #2A2E36;
}

[data-testid="stSidebar"] * {
	color: var(--sidebar-text);
}

[data-testid="stSidebar"] div.stButton > button {
	width: 100%;
	justify-content: flex-start;
	text-align: left;
	border-radius: 10px;
	border: 1px solid transparent;
	border-left: 3px solid transparent;
	background: transparent;
	color: var(--sidebar-text);
	min-height: 2.2rem;
	box-shadow: none;
	font-weight: 500;
}

[data-testid="stSidebar"] div.stButton > button[kind="primary"] {
	background: rgba(99, 102, 241, 0.16);
	color: #EEF2FF;
	border-color: #30364A;
	border-left-color: var(--accent);
}

[data-testid="stSidebar"] div.stButton > button:hover {
	border-color: #384055;
	color: #F3F4F6;
}

.sidebar-brand {
	color: var(--accent) !important;
	font-size: 1.35rem;
	font-weight: 700;
	margin-top: 0.5rem;
	margin-bottom: 0.25rem;
}

.sidebar-subtitle {
	color: #9CA3AF !important;
	font-size: 0.84rem;
	margin-bottom: 1rem;
}

.sidebar-nav-heading {
	color: #9CA3AF !important;
	text-transform: uppercase;
	letter-spacing: 0.11em;
	font-size: 0.68rem;
	margin-bottom: 0.5rem;
}

.sidebar-divider {
	border-bottom: 1px solid #2A2E36;
	margin: 0.9rem 0 0.9rem 0;
}

.status-heading {
	text-transform: uppercase;
	letter-spacing: 0.12em;
	font-size: 0.68rem;
	color: #9CA3AF !important;
	margin-bottom: 0.55rem;
}

.status-row {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 0.7rem;
	padding: 0.34rem 0;
	font-size: 0.82rem;
}

.status-dot {
	width: 8px;
	height: 8px;
	border-radius: 50%;
	display: inline-block;
}

.dot-up { background: #10B981; }
.dot-warn { background: #F59E0B; }
.dot-down { background: #EF4444; }

.tip-box {
	margin-top: 0.85rem;
	background: #232833;
	border: 1px solid #31384A;
	border-radius: 12px;
	padding: 0.65rem 0.72rem;
	color: #D1D5DB;
	font-size: 0.8rem;
	line-height: 1.45;
}

.tip-title {
	color: #A5B4FC;
	font-size: 0.72rem;
	text-transform: uppercase;
	letter-spacing: 0.1em;
	margin-bottom: 0.3rem;
	font-weight: 600;
}

.app-header {
	margin: 0.1rem 0 0.95rem 0;
}

.app-title {
	font-size: 1.58rem;
	font-weight: 700;
	color: var(--text);
	margin: 0;
}

.app-subtitle {
	color: var(--muted);
	margin-top: 0.18rem;
	margin-bottom: 0;
	font-size: 0.92rem;
}

.section-title {
	text-transform: uppercase;
	letter-spacing: 0.14em;
	font-size: 0.74rem;
	font-variant: small-caps;
	color: var(--muted);
	border-bottom: 1px solid var(--border);
	margin-top: 1.3rem;
	margin-bottom: 0.75rem;
	padding-bottom: 0.45rem;
	font-weight: 600;
}

.card {
	background: var(--card);
	border: 1px solid var(--border);
	box-shadow: 0 1px 4px rgba(15, 23, 42, 0.06);
	border-radius: 14px;
}

.notice {
	border-radius: 12px;
	border: 1px solid var(--border);
	padding: 0.72rem 0.86rem;
	font-size: 0.9rem;
	margin-bottom: 0.6rem;
}

.notice-info {
	background: var(--info-bg);
	color: var(--info-text);
	border-color: #D7E3FF;
}

.notice-high {
	background: var(--high-bg);
	color: var(--high-text);
	border-color: #F9D1D1;
}

.notice-med {
	background: var(--med-bg);
	color: var(--med-text);
	border-color: #F9DFA7;
}

.welcome-card {
	padding: 1rem 1.05rem;
	border-radius: 14px;
	border: 1px solid #E3E7EF;
	background: #FFFFFF;
	box-shadow: 0 1px 4px rgba(15, 23, 42, 0.05);
	color: #1F2937;
	font-size: 1rem;
}

.feature-card {
	background: #FFFFFF;
	border: 1px solid #E5E7EB;
	border-radius: 12px;
	padding: 0.9rem;
	box-shadow: 0 1px 3px rgba(15, 23, 42, 0.05);
	min-height: 132px;
}

.feature-icon {
	font-size: 1.1rem;
}

.feature-title {
	font-size: 0.9rem;
	color: #111827;
	font-weight: 600;
	margin-top: 0.34rem;
	margin-bottom: 0.24rem;
}

.feature-desc {
	color: #4B5563;
	font-size: 0.82rem;
	line-height: 1.5;
}

.quick-stat-row {
	display: flex;
	gap: 0.5rem;
	flex-wrap: wrap;
	margin-top: 0.2rem;
}

.quick-stat-pill {
	border-radius: 999px;
	border: 1px solid #D6DFFF;
	background: #EEF2FF;
	color: #3730A3;
	font-size: 0.79rem;
	padding: 0.22rem 0.6rem;
}

.recent-empty {
	border: 1px dashed #C7CDD7;
	border-radius: 12px;
	padding: 1rem;
	background: #F9FAFB;
	color: #6B7280;
	font-size: 0.88rem;
}

.recent-row {
	background: #FFFFFF;
	border: 1px solid #E5E7EB;
	border-radius: 12px;
	padding: 0.68rem 0.78rem;
	margin-bottom: 0.5rem;
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 0.6rem;
}

.recent-left {
	font-size: 0.84rem;
	color: #111827;
	font-weight: 500;
}

.recent-meta {
	color: #6B7280;
	font-size: 0.76rem;
}

.upload-hero {
	text-align: center;
	padding: 0.6rem 0 0.3rem 0;
}

.upload-title {
	font-size: 2rem;
	font-weight: 700;
	color: var(--text);
	margin-bottom: 0.25rem;
}

.upload-subtitle {
	color: var(--muted);
	font-size: 0.98rem;
	margin-bottom: 0.8rem;
}

.trust-badges {
	display: flex;
	flex-wrap: wrap;
	justify-content: center;
	gap: 0.45rem;
	margin-bottom: 0.9rem;
}

.trust-pill {
	border: 1px solid #E5E7EB;
	border-radius: 999px;
	background: #FFFFFF;
	color: #374151;
	font-size: 0.78rem;
	padding: 0.18rem 0.58rem;
}

.how-row {
	display: grid;
	grid-template-columns: repeat(3, minmax(0, 1fr));
	gap: 0.45rem;
	margin-top: 0.6rem;
}

.how-step {
	border: 1px solid #E5E7EB;
	border-radius: 10px;
	background: #FFFFFF;
	font-size: 0.82rem;
	color: #374151;
	text-align: center;
	padding: 0.48rem 0.55rem;
}

[data-testid="stFileUploader"] {
	border: 2px dashed var(--accent);
	border-radius: 16px;
	background: #EEF2FF;
	padding: 1.28rem;
}

[data-testid="stFileUploader"] small {
	color: #4B5563;
}

[data-testid="stAppViewContainer"] .main div.stButton > button {
	width: 100%;
	border: 1px solid #5458E8;
	border-radius: 10px;
	background: var(--accent);
	color: white;
	font-weight: 600;
	min-height: 2.8rem;
}

[data-testid="stAppViewContainer"] .main div.stButton > button:hover {
	background: #5558D9;
	border-color: #474BC5;
}

[data-testid="stAppViewContainer"] .main div.stButton > button[kind="secondary"] {
	background: #FEECEC;
	color: #991B1B;
	border: 1px solid #F8CACA;
}

[data-testid="stAppViewContainer"] .main div.stButton > button[kind="secondary"]:hover {
	background: #FDE2E2;
	border-color: #F1B9B9;
}

div[data-testid="stToggle"] [role="switch"] {
	background: #D1D5DB;
	border: 1px solid #CBD5E1;
}

div[data-testid="stToggle"] [role="switch"][aria-checked="true"] {
	background: var(--accent);
	border-color: #4F46E5;
}

.pill {
	font-size: 0.75rem;
	border-radius: 999px;
	padding: 0.18rem 0.52rem;
	border: 1px solid transparent;
	display: inline-block;
}

.pill-high { background: var(--high-bg); color: var(--high-text); border-color: #F9D1D1; }
.pill-med { background: var(--med-bg); color: var(--med-text); border-color: #F9DFA7; }
.pill-low { background: var(--low-bg); color: var(--low-text); border-color: #C9EED4; }
.pill-info { background: var(--info-bg); color: var(--info-text); border-color: #D7E3FF; }
.pill-meta { background: #F3F4F6; color: #4B5563; border-color: #E5E7EB; }

.badge {
	font-size: 0.68rem;
	font-weight: 600;
	border-radius: 999px;
	padding: 0.16rem 0.5rem;
	letter-spacing: 0.03em;
	border: 1px solid transparent;
}

.badge-high { background: var(--high-bg); color: var(--high-text); border-color: #F9D1D1; }
.badge-med { background: var(--med-bg); color: var(--med-text); border-color: #F9DFA7; }
.badge-low { background: var(--low-bg); color: var(--low-text); border-color: #C9EED4; }
.badge-info { background: var(--info-bg); color: var(--info-text); border-color: #D7E3FF; }

.stat-card {
	padding: 0.7rem 0.82rem;
	border-radius: 14px;
	background: var(--card);
	border: 1px solid var(--border);
	box-shadow: 0 1px 4px rgba(15, 23, 42, 0.06);
	min-height: 74px;
}

.stat-label {
	color: var(--muted);
	font-size: 0.7rem;
	text-transform: uppercase;
	letter-spacing: 0.09em;
}

.stat-main {
	margin-top: 0.28rem;
	display: flex;
	align-items: center;
	gap: 0.35rem;
}

.stat-icon {
	font-size: 0.95rem;
}

.stat-value {
	font-size: 1.1rem;
	font-weight: 700;
	color: var(--text);
}

.stat-subtitle {
	margin-top: 0.3rem;
	color: #6B7280;
	font-size: 0.73rem;
	line-height: 1.35;
}

.overall-pill {
	border-radius: 999px;
	padding: 0.17rem 0.58rem;
	color: #FFFFFF;
	font-size: 0.75rem;
	font-weight: 700;
	letter-spacing: 0.04em;
}

.overall-high { background: #B91C1C; }
.overall-med { background: #B45309; }
.overall-low { background: #166534; }

.value-high { color: var(--high-text); }
.value-med { color: var(--med-text); }
.value-low { color: var(--low-text); }

.risk-alert {
	border-radius: 10px;
	padding: 0.46rem 0.72rem;
	margin-bottom: 0.72rem;
	border: 1px solid transparent;
	font-size: 0.84rem;
}

.risk-alert-high {
	background: #FEECEC;
	color: #991B1B;
	border-color: #F9D1D1;
}

.risk-alert-med {
	background: #FFF4DB;
	color: #92400E;
	border-color: #F9DFA7;
}

.risk-alert-low {
	background: #EAF8EE;
	color: #166534;
	border-color: #C9EED4;
}

.risk-meter-card {
	border: 1px solid #E5E7EB;
	border-radius: 12px;
	background: #FFFFFF;
	padding: 0.72rem;
	margin-top: 0.55rem;
	margin-bottom: 0.95rem;
}

.risk-meter-track {
	width: 100%;
	height: 9px;
	border-radius: 999px;
	overflow: hidden;
	background: #E5E7EB;
	display: flex;
}

.risk-seg-high { background: #EF4444; }
.risk-seg-med { background: #F59E0B; }
.risk-seg-low { background: #22C55E; }

.risk-meter-legend {
	margin-top: 0.48rem;
	display: flex;
	gap: 0.35rem;
	flex-wrap: wrap;
	font-size: 0.75rem;
	color: #4B5563;
}

.panel-card {
	padding: 0.7rem;
}

.panel-header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	margin-bottom: 0.48rem;
}

.panel-title {
	color: #374151;
	font-size: 0.75rem;
	font-weight: 600;
	text-transform: uppercase;
	letter-spacing: 0.09em;
	line-height: 1;
}

.panel-count {
	background: #EEF2FF;
	color: #3730A3;
	border: 1px solid #D6DFFF;
	border-radius: 999px;
	font-size: 0.72rem;
	padding: 0.14rem 0.45rem;
	font-weight: 600;
}

.item-row {
	display: grid;
	grid-template-columns: 1.05fr 1fr auto;
	gap: 0.45rem;
	align-items: center;
	border: 1px solid var(--border);
	border-radius: 10px;
	padding: 0.56rem 0.6rem;
	margin-bottom: 0.45rem;
	background: #FCFCFD;
}

.item-left {
	color: #111827;
	font-weight: 500;
	font-size: 0.86rem;
}

.item-middle {
	color: #4B5563;
	font-size: 0.82rem;
}

.item-right {
	display: flex;
	align-items: center;
	justify-content: flex-end;
	gap: 0.34rem;
}

.empty-success {
	border: 1px solid #D1D5DB;
	background: #F9FAFB;
	color: #1F2937;
	border-radius: 10px;
	padding: 0.68rem;
	font-size: 0.84rem;
}

.graph-pill-row {
	display: flex;
	flex-wrap: wrap;
	gap: 0.5rem;
	margin-bottom: 0.65rem;
}

.graph-density-wrap {
	margin-top: 0.4rem;
}

.graph-density-track {
	width: 100%;
	border-radius: 999px;
	height: 10px;
	background: #E5E7EB;
	overflow: hidden;
}

.graph-density-fill {
	height: 100%;
	background: linear-gradient(90deg, #A5B4FC 0%, #6366F1 100%);
}

.graph-density-label {
	color: #4B5563;
	font-size: 0.79rem;
	margin-top: 0.4rem;
}

.contradiction-card {
	padding: 0.75rem;
	margin-bottom: 0.62rem;
}

.contradiction-grid {
	display: grid;
	grid-template-columns: 1fr auto 1fr;
	gap: 0.65rem;
	align-items: center;
}

.contr-side {
	border: 1px solid var(--border);
	border-radius: 10px;
	background: #FCFCFD;
	padding: 0.55rem;
}

.contr-clause {
	color: #111827;
	font-weight: 600;
	font-size: 0.84rem;
	margin-bottom: 0.25rem;
}

.contr-text {
	color: #4B5563;
	font-size: 0.82rem;
	line-height: 1.38;
}

.vs-tag {
	color: #92400E;
	background: #FFF4DB;
	border: 1px solid #F9DFA7;
	border-radius: 999px;
	padding: 0.2rem 0.54rem;
	font-size: 0.78rem;
	font-weight: 600;
	white-space: nowrap;
}

.contr-meta {
	margin-top: 0.45rem;
	display: flex;
	gap: 0.4rem;
}

.explanation-card {
	border-left: 4px solid var(--accent);
	padding: 0.85rem 0.95rem;
	margin-bottom: 0.8rem;
}

.explanation-title {
	color: #111827;
	font-size: 0.95rem;
	font-weight: 600;
	margin-bottom: 0.3rem;
}

.explanation-block-title {
	color: #374151;
	font-size: 0.78rem;
	text-transform: uppercase;
	letter-spacing: 0.08em;
	font-weight: 600;
	margin-top: 0.62rem;
	margin-bottom: 0.2rem;
}

.explanation-body {
	color: #1F2937;
	font-size: 0.93rem;
	line-height: 1.58;
}

.inline-statute {
	display: inline-block;
	background: #DBEAFE;
	color: #1E3A8A;
	border: 1px solid #BFDBFE;
	border-radius: 6px;
	padding: 0.02rem 0.3rem;
	font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
	font-size: 0.8rem;
}

.citation-row {
	display: flex;
	flex-wrap: wrap;
	gap: 0.35rem;
	margin-top: 0.52rem;
}

.citation-pill {
	display: inline-block;
	background: #DBEAFE;
	color: #1E3A8A;
	border: 1px solid #BFDBFE;
	border-radius: 999px;
	padding: 0.17rem 0.52rem;
	font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
	font-size: 0.74rem;
}

.library-header {
	background: #FFFFFF;
	border: 1px solid #E5E7EB;
	border-radius: 12px;
	padding: 0.88rem;
	color: #111827;
	font-size: 1.03rem;
	font-weight: 600;
}

.library-meta {
	color: #6B7280;
	font-size: 0.8rem;
	margin-top: 0.26rem;
}

.library-small {
	color: #6B7280;
	font-size: 0.79rem;
}

.statute-card {
	background: #FFFFFF;
	border: 1px solid #E5E7EB;
	border-radius: 12px;
	padding: 0.72rem 0.82rem;
	margin-bottom: 0.55rem;
}

.statute-title {
	font-size: 0.92rem;
	font-weight: 600;
	color: #111827;
	margin-bottom: 0.28rem;
}

.model-card {
	background: #FFFFFF;
	border: 1px solid #E5E7EB;
	border-radius: 12px;
	padding: 0.82rem;
	box-shadow: 0 1px 3px rgba(15, 23, 42, 0.05);
}

.model-row {
	display: flex;
	justify-content: space-between;
	align-items: center;
	border-bottom: 1px solid #F0F2F5;
	padding: 0.38rem 0;
	color: #374151;
	font-size: 0.83rem;
}

.model-row:last-child {
	border-bottom: none;
}

.settings-note {
	color: #6B7280;
	font-size: 0.82rem;
	margin-top: -0.1rem;
	margin-bottom: 0.42rem;
}

@media (max-width: 900px) {
	.item-row {
		grid-template-columns: 1fr;
	}
	.item-right {
		justify-content: flex-start;
	}
	.contradiction-grid {
		grid-template-columns: 1fr;
	}
	.vs-tag {
		width: fit-content;
		margin: 0 auto;
	}
	.how-row {
		grid-template-columns: 1fr;
	}
}
</style>
		""",
		unsafe_allow_html=True,
	)


def _escape(value: Any) -> str:
	return html.escape(str(value))


def _to_float(value: Any, default: float = 0.0) -> float:
	try:
		return float(value)
	except (TypeError, ValueError):
		return default


def _risk_tone(risk_level: str) -> str:
	normalized = (risk_level or "").strip().lower()
	if normalized == "high":
		return "high"
	if normalized == "medium":
		return "med"
	if normalized in {"low", "safe"}:
		return "low"
	return "info"


def _risk_level_from_score(score: float, high_threshold: float, medium_threshold: float) -> str:
	if score >= high_threshold:
		return "HIGH"
	if score >= medium_threshold:
		return "MEDIUM"
	return "LOW"


def _confidence_label(score: float) -> str:
	return "HIGH" if score >= 0.7 else "MEDIUM"


def _truncate(text: str, limit: int = 80) -> str:
	value = (text or "").strip().replace("\n", " ")
	if len(value) <= limit:
		return value
	return f"{value[:limit].rstrip()}..."


def _section_title(title: str) -> None:
	st.markdown(f'<div class="section-title">{_escape(title)}</div>', unsafe_allow_html=True)


def _notice(message: str, tone: str = "info") -> None:
	tone_class = "notice-info"
	if tone == "high":
		tone_class = "notice-high"
	elif tone == "med":
		tone_class = "notice-med"
	st.markdown(
		f'<div class="notice {tone_class}">{_escape(message)}</div>',
		unsafe_allow_html=True,
	)


def _metric_pill(label: str, value: Any, tone: str = "info") -> str:
	return f'<span class="pill pill-{tone}">{_escape(label)}: {_escape(value)}</span>'


def _act_short_name(act: str) -> str:
	normalized = (act or "").strip().lower()
	if "contract" in normalized and "act" in normalized:
		return "ICA"
	if "penal" in normalized or normalized == "ipc" or "indian penal code" in normalized:
		return "IPC"
	if "constitution" in normalized:
		return "CONST"

	tokens = [token for token in re.split(r"[^A-Za-z0-9]+", act or "") if token]
	if not tokens:
		return "LAW"
	if len(tokens) == 1:
		return tokens[0][:4].upper()
	return "".join(token[0].upper() for token in tokens[:4])


_STATUTE_TOKEN_RE = re.compile(
	r"\b(?:Section|Article)\s+\d+[A-Za-z]?\b|\bS\.\s*\d+[A-Za-z]?\b",
	re.IGNORECASE,
)


def _highlight_statutes(text: str) -> str:
	escaped = _escape(text).replace("\n", "<br>")
	return _STATUTE_TOKEN_RE.sub(
		lambda m: f'<span class="inline-statute">{m.group(0)}</span>',
		escaped,
	)


_SECTION_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
	(
		"risk_summary",
		re.compile(r"^(?:\d[\)\.:\-]\s*)?risk\s*summary\s*[:\-]?\s*(?P<rest>.*)$", re.IGNORECASE),
	),
	(
		"why_risky",
		re.compile(
			r"^(?:\d[\)\.:\-]\s*)?why\s*risky(?:\s*under\s*indian\s*law)?\s*[:\-]?\s*(?P<rest>.*)$",
			re.IGNORECASE,
		),
	),
	(
		"practical_impact",
		re.compile(
			r"^(?:\d[\)\.:\-]\s*)?practical\s*impact(?:\s*on\s*business)?\s*[:\-]?\s*(?P<rest>.*)$",
			re.IGNORECASE,
		),
	),
	(
		"rewrite",
		re.compile(
			r"^(?:\d[\)\.:\-]\s*)?safer\s*rewrite\s*suggestion\s*[:\-]?\s*(?P<rest>.*)$",
			re.IGNORECASE,
		),
	),
	(
		"citations",
		re.compile(r"^(?:\d[\)\.:\-]\s*)?citations?\s*[:\-]?\s*(?P<rest>.*)$", re.IGNORECASE),
	),
]


def _parse_explanation_sections(raw_text: str) -> dict[str, str]:
	sections: dict[str, list[str]] = {
		"risk_summary": [],
		"why_risky": [],
		"practical_impact": [],
		"rewrite": [],
		"citations": [],
	}

	current = "risk_summary"
	for line in (raw_text or "").splitlines():
		cleaned = re.sub(r"[`*_]", "", line).strip()
		if not cleaned:
			continue

		switched = False
		for key, pattern in _SECTION_PATTERNS:
			match = pattern.match(cleaned)
			if match:
				current = key
				rest = (match.group("rest") or "").strip()
				if rest:
					sections[current].append(rest)
				switched = True
				break

		if not switched:
			sections[current].append(cleaned)

	normalized = {key: "\n".join(value).strip() for key, value in sections.items()}
	if not any(normalized.values()) and raw_text:
		normalized["risk_summary"] = raw_text.strip()
	return normalized


def _extract_inline_citations(text: str) -> list[str]:
	found = _STATUTE_TOKEN_RE.findall(text or "")
	seen: set[str] = set()
	ordered: list[str] = []
	for token in found:
		normalized = re.sub(r"\s+", " ", token.strip())
		key = normalized.lower()
		if key in seen:
			continue
		seen.add(key)
		ordered.append(normalized)
	return ordered


def _build_citation_badges(explanation_item: dict[str, Any], law_matches: list[dict[str, Any]], why_text: str) -> list[str]:
	badges: list[str] = []
	seen: set[str] = set()

	def add_badge(value: str) -> None:
		label = (value or "").strip()
		if not label:
			return
		key = label.lower()
		if key in seen:
			return
		seen.add(key)
		badges.append(label)

	for match in law_matches[:5]:
		section = str(match.get("section_number") or "").strip()
		if not section:
			continue
		add_badge(f"{_act_short_name(str(match.get('act') or 'Law'))} S.{section}")

	citation_verification = explanation_item.get("citation_verification") or {}
	for section in citation_verification.get("supported_citations", []):
		add_badge(f"S.{str(section).strip()}")

	for token in _extract_inline_citations(why_text):
		add_badge(token)

	return badges[:8]


def _recent_entry_badge(level: str) -> str:
	tone = _risk_tone(level)
	return f'<span class="badge badge-{tone}">{_escape(level)}</span>'


def _overall_risk_label_from_scores(risks: list[dict[str, Any]], high_threshold: float, medium_threshold: float) -> str:
	if not risks:
		return "LOW"

	high = 0
	medium = 0
	for item in risks:
		score = _to_float(item.get("top_score"))
		level = _risk_level_from_score(score, high_threshold, medium_threshold)
		if level == "HIGH":
			high += 1
		elif level == "MEDIUM":
			medium += 1

	if high > 0:
		return "HIGH"
	if medium > 0:
		return "MEDIUM"
	return "LOW"


@st.cache_data(ttl=20, show_spinner=False)
def _runtime_status(api_base: str) -> dict[str, bool]:
	status = {
		"inlegalbert": False,
		"qdrant": False,
		"phi3": False,  # llama3:latest status (displayed as 'Local LLM')
	}

	try:
		health = requests.get(f"{api_base}/v1/health", timeout=2)
		status["inlegalbert"] = bool(health.ok)
	except requests.RequestException:
		status["inlegalbert"] = False

	try:
		metadata = requests.get(f"{api_base}/v1/metadata", timeout=2)
		status["qdrant"] = bool(metadata.ok)
	except requests.RequestException:
		status["qdrant"] = False

	try:
		tags = requests.get("http://127.0.0.1:11434/api/tags", timeout=2)
		if tags.ok:
			models = [str(model.get("name") or "").lower() for model in tags.json().get("models", [])]
			status["phi3"] = any("llama3" in model or "llama-3" in model for model in models)
	except requests.RequestException:
		status["phi3"] = False

	return status


def _render_stat_tile(label: str, icon: str, value: str, subtitle: str, value_class: str = "", pill_class: str = "") -> None:
	value_markup = f'<div class="stat-value {value_class}">{_escape(value)}</div>'
	if pill_class:
		value_markup = f'<span class="overall-pill {pill_class}">{_escape(value)}</span>'

	st.markdown(
		(
			'<div class="stat-card">'
			f'<div class="stat-label">{_escape(label)}</div>'
			'<div class="stat-main">'
			f'<span class="stat-icon">{_escape(icon)}</span>'
			f'{value_markup}'
			"</div>"
			f'<div class="stat-subtitle">{_escape(subtitle)}</div>'
			"</div>"
		),
		unsafe_allow_html=True,
	)


def _render_feature_card(icon: str, title: str, desc: str) -> None:
	st.markdown(
		(
			'<div class="feature-card">'
			f'<div class="feature-icon">{_escape(icon)}</div>'
			f'<div class="feature-title">{_escape(title)}</div>'
			f'<div class="feature-desc">{_escape(desc)}</div>'
			"</div>"
		),
		unsafe_allow_html=True,
	)


def _render_dashboard_home() -> None:
	st.markdown(
		(
			'<div class="welcome-card">'
			"Welcome to ContractLens — Upload a contract to begin your legal risk analysis"
			"</div>"
		),
		unsafe_allow_html=True,
	)

	_section_title("Feature Highlights")
	f1, f2, f3 = st.columns(3, gap="small")
	with f1:
		_render_feature_card(
			"🔎",
			"Risk Detection",
			"Identify high-impact contractual terms that may expose your business to legal or financial risk. "
			"Prioritize review with clause-level confidence scoring.",
		)
	with f2:
		_render_feature_card(
			"⚖️",
			"Contradiction Analysis",
			"Detect conflicting obligations across clauses before execution. "
			"Reduce ambiguity that can lead to disputes and delayed enforcement.",
		)
	with f3:
		_render_feature_card(
			"📜",
			"Statute Verification",
			"Ground every legal signal against indexed Indian statutes. "
			"Surface the most relevant sections for advocate-grade review.",
		)

	_section_title("Quick Stats")
	st.markdown(
		(
			'<div class="quick-stat-row">'
			'<span class="quick-stat-pill">Statutes Indexed: 1,138</span>'
			'<span class="quick-stat-pill">Acts Covered: 3</span>'
			'<span class="quick-stat-pill">Risk Categories: 8</span>'
			"</div>"
		),
		unsafe_allow_html=True,
	)

	_section_title("Recent Analyses")
	history = st.session_state.analysis_history
	if not history:
		st.markdown(
			(
				'<div class="recent-empty">'
				"No contracts analysed yet. Upload your first contract to get started."
				"</div>"
			),
			unsafe_allow_html=True,
		)
		return

	for item in history[:6]:
		st.markdown(
			(
				'<div class="recent-row">'
				'<div>'
				f'<div class="recent-left">{_escape(item.get("file_name", "Contract"))}</div>'
				f'<div class="recent-meta">{_escape(item.get("timestamp", ""))}</div>'
				"</div>"
				f'{_recent_entry_badge(str(item.get("overall_risk", "LOW")))}'
				"</div>"
			),
			unsafe_allow_html=True,
		)


def _render_law_library_page() -> None:
	st.markdown(
		(
			'<div class="library-header">Indian Statutory Knowledge Base'
			'<div class="library-meta">Core statutes used by ContractLens for legal risk intelligence.</div>'
			"</div>"
		),
		unsafe_allow_html=True,
	)

	_section_title("Indexed Statutes")
	for statute in STATUTE_LIBRARY:
		categories = "".join(
			f'<span class="pill pill-info" style="margin-right:0.3rem;">{_escape(category)}</span>'
			for category in statute["categories"]
		)
		section_items = "".join(
			f"<li>{_escape(section)}</li>" for section in statute["relevant_sections"]
		)
		st.markdown(
			(
				'<div class="statute-card">'
				f'<div class="statute-title">{_escape(statute["title"])}</div>'
				f'<div class="library-small"><strong>Sections indexed:</strong> {statute["sections_indexed"]}</div>'
				f'<div class="library-small" style="margin-top:0.35rem;"><strong>Key risk categories covered:</strong> {categories}</div>'
				'<div class="library-small" style="margin-top:0.35rem;"><strong>Most relevant sections for contract analysis:</strong>'
				f'<ul style="margin:0.35rem 0 0.1rem 1.05rem;">{section_items}</ul></div>'
				"</div>"
			),
			unsafe_allow_html=True,
		)

	st.markdown(
		'<div class="settings-note" style="margin-top:0.7rem;">All statutes sourced from indiacode.nic.in</div>',
		unsafe_allow_html=True,
	)


def _render_settings_page() -> None:
	_section_title("Analysis Settings")

	fast_mode_value = st.toggle(
		"Fast Mode",
		value=bool(st.session_state.settings_fast_mode),
		help="Enable concise analysis limits for faster turnaround.",
	)
	st.session_state.settings_fast_mode = bool(fast_mode_value)

	st.markdown(
		'<div class="settings-note">Limits law checking to 8 clauses and explanations to 3 clauses for faster results.</div>',
		unsafe_allow_html=True,
	)

	high_threshold = st.slider(
		"High Risk Threshold",
		min_value=0.50,
		max_value=0.95,
		value=float(st.session_state.high_threshold),
		step=0.01,
	)
	medium_threshold = st.slider(
		"Medium Risk Threshold",
		min_value=0.30,
		max_value=0.90,
		value=float(st.session_state.medium_threshold),
		step=0.01,
	)

	if medium_threshold >= high_threshold:
		medium_threshold = max(0.30, round(high_threshold - 0.01, 2))
		_notice("Medium threshold was adjusted to remain below the High threshold.", tone="med")

	st.session_state.high_threshold = float(high_threshold)
	st.session_state.medium_threshold = float(medium_threshold)

	_section_title("Model Configuration")
	st.markdown(
		(
			'<div class="model-card">'
			'<div class="model-row"><span>Model</span><strong>InLegalBERT</strong></div>'
			'<div class="model-row"><span>Dimensions</span><strong>768</strong></div>'
			'<div class="model-row"><span>Vector DB</span><strong>Qdrant Cloud</strong></div>'
			'<div class="model-row"><span>Local LLM</span><strong>llama3:latest (Ollama)</strong></div>'
			"</div>"
		),
		unsafe_allow_html=True,
	)

	_section_title("Session")
	if st.button("Clear Session", type="secondary", use_container_width=True):
		st.session_state.analysis_result = None
		st.session_state.analysis_history = []
		_notice("Session data cleared successfully.", tone="med")


def _render_upload_landing() -> tuple[Any, bool]:
	st.markdown(
		(
			'<div class="upload-hero">'
			'<div class="upload-title">Instant Legal Risk Analysis</div>'
			'<div class="upload-subtitle">Upload any Indian business contract and get statute-backed risk assessment in under 20 seconds</div>'
			'<div class="trust-badges">'
			'<span class="trust-pill">🔒 Private &amp; Secure</span>'
			'<span class="trust-pill">⚡ Under 20 Seconds</span>'
			'<span class="trust-pill">📜 Grounded in Indian Law</span>'
			"</div>"
			"</div>"
		),
		unsafe_allow_html=True,
	)

	left, center, right = st.columns([1, 1.6, 1], gap="small")
	with center:
		pdf = st.file_uploader("", type=["pdf"], label_visibility="collapsed")
		if st.session_state.settings_fast_mode:
			st.markdown('<span class="pill pill-info">Fast Mode enabled</span>', unsafe_allow_html=True)
		analyze_clicked = st.button("Analyse Contract", type="primary")

		st.markdown(
			(
				'<div class="how-row">'
				'<div class="how-step">1. Upload PDF</div>'
				'<div class="how-step">2. AI analyses clauses</div>'
				'<div class="how-step">3. Get statute-backed report</div>'
				"</div>"
			),
			unsafe_allow_html=True,
		)

	return pdf, analyze_clicked


def _run_analysis(pdf: Any) -> None:
	if not pdf:
		_notice("Please upload a PDF contract before starting analysis.", tone="high")
		return

	fast_mode = bool(st.session_state.settings_fast_mode)
	explain_max = 3 if fast_mode else 6
	law_max = 8 if fast_mode else 14

	try:
		with st.spinner("Segmenting contract clauses..."):
			upload = requests.post(
				f"{API_BASE}/v1/contracts/upload",
				files={"file": (pdf.name, pdf.getvalue(), "application/pdf")},
				timeout=180,
			)
			upload.raise_for_status()
			upload_payload = upload.json()

		contract_path = upload_payload.get("json_path") or upload_payload.get("stored_path")
		if not contract_path:
			raise ValueError("Upload response did not include a contract path.")

		with st.spinner(
			"Building knowledge graph... Scoring against Indian Contract Act... "
			"Retrieving relevant statutes from Qdrant... Generating verified explanations..."
		):
			analyze = requests.post(
				f"{API_BASE}/v1/contracts/analyze",
				json={
					"contract_path": contract_path,
					"explain_top_risks_only": False,
					"explain_max_clauses": explain_max,
					"law_check_max_clauses": law_max,
					"explain_risk_threshold": float(st.session_state.high_threshold),
				},
				timeout=360,
			)
			analyze.raise_for_status()
			result_payload = analyze.json()

		st.session_state.analysis_result = result_payload

		overall_level = _overall_risk_label_from_scores(
			result_payload.get("risks", []),
			high_threshold=float(st.session_state.high_threshold),
			medium_threshold=float(st.session_state.medium_threshold),
		)
		history_entry = {
			"file_name": str(pdf.name),
			"timestamp": datetime.now().strftime("%d %b %Y, %I:%M %p"),
			"overall_risk": overall_level,
		}
		history = list(st.session_state.analysis_history)
		history.insert(0, history_entry)
		st.session_state.analysis_history = history[:20]
	except requests.RequestException as exc:
		_notice(
			(
				"Analysis request could not be completed. "
				f"Please verify backend and Ollama connectivity. Details: {exc}"
			),
			tone="high",
		)
	except ValueError as exc:
		_notice(str(exc), tone="high")


def _render_risk_banner(overall_level: str) -> None:
	if overall_level == "HIGH":
		st.markdown(
			'<div class="risk-alert risk-alert-high">⚠ High risk contract detected — review flagged clauses before signing</div>',
			unsafe_allow_html=True,
		)
	elif overall_level == "MEDIUM":
		st.markdown(
			'<div class="risk-alert risk-alert-med">⚠ Medium risk contract detected — validate obligations before execution</div>',
			unsafe_allow_html=True,
		)
	else:
		st.markdown(
			'<div class="risk-alert risk-alert-low">✅ Low risk contract profile — continue final legal review before signing</div>',
			unsafe_allow_html=True,
		)


def _render_risk_meter(high_count: int, medium_count: int, low_count: int, total: int) -> None:
	denominator = total if total > 0 else 1
	high_pct = max(0.0, min(100.0, (high_count / denominator) * 100.0))
	med_pct = max(0.0, min(100.0, (medium_count / denominator) * 100.0))
	low_pct = max(0.0, 100.0 - high_pct - med_pct)

	st.markdown(
		(
			'<div class="risk-meter-card">'
			'<div class="risk-meter-track">'
			f'<div class="risk-seg-high" style="width:{high_pct:.1f}%;"></div>'
			f'<div class="risk-seg-med" style="width:{med_pct:.1f}%;"></div>'
			f'<div class="risk-seg-low" style="width:{low_pct:.1f}%;"></div>'
			"</div>"
			'<div class="risk-meter-legend">'
			f'<span>High: {high_count}</span>'
			f'<span>Medium: {medium_count}</span>'
			f'<span>Low: {low_count}</span>'
			"</div>"
			"</div>"
		),
		unsafe_allow_html=True,
	)


def _build_panel_rows_html(rows: list[dict[str, Any]]) -> str:
	html_rows: list[str] = []
	for row in rows:
		level = str(row.get("level") or "LOW").upper()
		tone = _risk_tone(level)
		score = _to_float(row.get("score"))
		html_rows.append(
			(
				'<div class="item-row">'
				f'<div class="item-left">{_escape(row.get("left") or "")}</div>'
				f'<div class="item-middle">{_escape(row.get("middle") or "")}</div>'
				'<div class="item-right">'
				f'<span class="pill pill-{tone}">{score:.3f}</span>'
				f'<span class="badge badge-{tone}">{_escape(level)}</span>'
				"</div>"
				"</div>"
			)
		)
	return "".join(html_rows)


def _format_clause_tooltip(text: str, line_width: int = 88) -> str:
	clean = (text or "").strip()
	if not clean:
		return "No clause text available"
	wrapped: list[str] = []
	for i in range(0, len(clean), line_width):
		wrapped.append(clean[i:i + line_width])
	return "<br>".join(html.escape(part) for part in wrapped)

def _render_knowledge_graph(clauses, graph_edges, risks=None, contradictions=None):
    if Network is None:
        _notice("Pyvis not installed", tone="high")
        return

    if not clauses:
        _notice("No clauses found", tone="info")
        return

    import json
    from collections import defaultdict

    net = Network(
        height="650px",
        width="100%",
        directed=False,
        bgcolor="#FFFFFF",
        font_color="#1F2937",
        notebook=False,
    )

    net.force_atlas_2based()

    # -------------------------
    # Risk mapping
    # -------------------------
    risk_map = {}
    if risks:
        for r in risks:
            risk_map[int(r.get("clause_index"))] = r.get("_ui_level", "LOW")

    def get_color(level):
        if level == "HIGH":
            return "#ef4444"
        elif level == "MEDIUM":
            return "#f59e0b"
        return "#22c55e"

    # -------------------------
    # Add nodes
    # -------------------------
    for clause in clauses:
        idx = clause.get("index")
        if idx is None:
            continue

        level = risk_map.get(int(idx), "LOW")
        color = get_color(level)

        tooltip = f"""
        <b>Clause {idx}</b><br>
        Risk: {level}<br><br>
        {_format_clause_tooltip(clause.get("text", ""))}
        """

        net.add_node(
            int(idx),
            label=f"{idx}",
            title=tooltip,
            color=color,
            size=20 if level == "HIGH" else 15,
        )

    # -------------------------
    # Contradiction pairs
    # -------------------------
    contradiction_pairs = set()
    if contradictions:
        for c in contradictions:
            a = c.get("clause_a_index")
            b = c.get("clause_b_index")
            if a and b:
                contradiction_pairs.add((int(a), int(b)))

    # -------------------------
    # Edge filtering
    # -------------------------
    SIM_THRESHOLD = 0.75
    MAX_EDGES_PER_NODE = 3
    edge_count = defaultdict(int)

    sorted_edges = sorted(
        graph_edges,
        key=lambda e: float(e.get("similarity", 0)),
        reverse=True,
    )

    for edge in sorted_edges:
        s = edge.get("source_index")
        t = edge.get("target_index")

        if s is None or t is None or s == t:
            continue

        s, t = int(s), int(t)
        sim = float(edge.get("similarity", 0))

        if sim < SIM_THRESHOLD:
            continue

        if edge_count[s] >= MAX_EDGES_PER_NODE or edge_count[t] >= MAX_EDGES_PER_NODE:
            continue

        # Highlight contradictions
        is_contradiction = (s, t) in contradiction_pairs or (t, s) in contradiction_pairs

        net.add_edge(
            s,
            t,
            value=sim * 10,
            color="red" if is_contradiction else "#CBD5F5",
            width=3 if is_contradiction else 1,
            title=f"Similarity: {sim:.2f}",
        )

        edge_count[s] += 1
        edge_count[t] += 1

    # -------------------------
    # Static + clean layout
    # -------------------------
    net.set_options(json.dumps({
        "physics": {
            "enabled": False
        },
        "interaction": {
            "hover": True,
            "tooltipDelay": 200,
            "navigationButtons": True,
            "keyboard": True
        },
        "nodes": {
            "font": {
                "size": 14
            }
        }
    }))

    # -------------------------
    # Render
    # -------------------------
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as f:
        net.save_graph(f.name)
        html_data = open(f.name, "r", encoding="utf-8").read()

    st.components.v1.html(html_data, height=650, scrolling=True)

def _render_results_dashboard(result: dict[str, Any]) -> None:
	clauses = result.get("clauses", [])
	risks = result.get("risks", [])
	contradictions = result.get("internal_contradictions", [])
	law_checks = result.get("law_checks", [])
	explanations = result.get("explanations", [])
	edges = result.get("graph_edges", [])

	high_threshold = float(st.session_state.high_threshold)
	medium_threshold = float(st.session_state.medium_threshold)

	classified_risks: list[dict[str, Any]] = []
	for item in risks:
		score = _to_float(item.get("top_score"))
		level = _risk_level_from_score(score, high_threshold, medium_threshold)
		enriched = dict(item)
		enriched["_ui_level"] = level
		enriched["_ui_score"] = score
		classified_risks.append(enriched)

	clause_text_by_index = {
		int(item.get("index")): str(item.get("text") or "")
		for item in clauses
		if item.get("index") is not None
	}

	high_risks = [item for item in classified_risks if item.get("_ui_level") == "HIGH"]
	medium_risks = [item for item in classified_risks if item.get("_ui_level") == "MEDIUM"]
	low_risks = [item for item in classified_risks if item.get("_ui_level") == "LOW"]
	overall_level = _overall_risk_label_from_scores(classified_risks, high_threshold, medium_threshold)

	_render_risk_banner(overall_level)

	_section_title("Analysis Summary")
	c1, c2, c3, c4 = st.columns(4, gap="small")
	with c1:
		_render_stat_tile(
			"Total Clauses Analysed",
			"📄",
			str(len(clauses)),
			"contract clauses extracted for review",
		)
	with c2:
		_render_stat_tile(
			"High Risk Clauses",
			"🔴",
			str(len(high_risks)),
			f"clauses flagged above {high_threshold:.2f} threshold",
			value_class="value-high",
		)
	with c3:
		_render_stat_tile(
			"Internal Contradictions Found",
			"⚠️",
			str(len(contradictions)),
			"potential conflicts across contractual obligations",
			value_class="value-med",
		)
	with c4:
		pill_class = "overall-high" if overall_level == "HIGH" else "overall-med" if overall_level == "MEDIUM" else "overall-low"
		_render_stat_tile(
			"Overall Risk Level",
			"🏛",
			overall_level,
			"based on current risk-score distribution",
			pill_class=pill_class,
		)

	_render_risk_meter(
		high_count=len(high_risks),
		medium_count=len(medium_risks),
		low_count=len(low_risks),
		total=len(classified_risks),
	)

	_section_title("Risk, Contradictions, and Law Violations")
	left_col, mid_col, right_col = st.columns(3, gap="medium")

	risk_rows = [
		{
			"left": f"Clause {item.get('clause_index')}",
			"middle": str(item.get("top_category") or "Risk Signal"),
			"score": item.get("_ui_score"),
			"level": item.get("_ui_level"),
		}
		for item in sorted(high_risks, key=lambda r: _to_float(r.get("_ui_score")), reverse=True)[:12]
	]

	contradiction_rows = []
	for item in sorted(contradictions, key=lambda c: _to_float(c.get("contradiction_score")), reverse=True)[:12]:
		score = _to_float(item.get("contradiction_score"))
		contradiction_rows.append(
			{
				"left": f"⚡ Clause {item.get('clause_a_index')} vs Clause {item.get('clause_b_index')}",
				"middle": "Opposing legal obligations detected between these clauses",
				"score": score,
				"level": _confidence_label(score),
			}
		)

	law_rows: list[dict[str, Any]] = []
	for check in law_checks:
		clause_idx = check.get("clause_index")
		matches = check.get("law_matches") or []
		if not matches:
			continue
		top_match = max(matches, key=lambda m: _to_float(m.get("contradiction_score")))
		score = _to_float(top_match.get("contradiction_score"))
		law_rows.append(
			{
				"left": f"Clause {clause_idx}",
				"middle": f"{_act_short_name(str(top_match.get('act') or 'Law'))} S.{top_match.get('section_number')}",
				"score": score,
				"level": _confidence_label(score),
			}
		)

	law_rows = sorted(law_rows, key=lambda row: _to_float(row.get("score")), reverse=True)[:12]

	with left_col:
		risk_rows_html = _build_panel_rows_html(risk_rows)
		if not risk_rows_html:
			risk_rows_html = '<div class="notice notice-info">No high-risk clauses under current thresholds.</div>'
		st.markdown(
			(
				'<div class="card panel-card">'
				'<div class="panel-header">'
				'<div class="panel-title">High Risk Clauses</div>'
				f'<div class="panel-count">{len(risk_rows)}</div>'
				"</div>"
				f"{risk_rows_html}"
				"</div>"
			),
			unsafe_allow_html=True,
		)

	with mid_col:
		contradiction_rows_html = _build_panel_rows_html(contradiction_rows)
		if not contradiction_rows_html:
			contradiction_rows_html = '<div class="notice notice-info">No contradiction pairs met the configured threshold.</div>'
		st.markdown(
			(
				'<div class="card panel-card">'
				'<div class="panel-header">'
				'<div class="panel-title">Internal Contradictions</div>'
				f'<div class="panel-count">{len(contradiction_rows)}</div>'
				"</div>"
				f"{contradiction_rows_html}"
				"</div>"
			),
			unsafe_allow_html=True,
		)

	with right_col:
		if law_rows:
			law_rows_html = _build_panel_rows_html(law_rows)
		else:
			law_rows_html = (
				'<div class="empty-success">'
				"✅ No statutory violations detected for this contract"
				"</div>"
			)
		st.markdown(
			(
				'<div class="card panel-card">'
				'<div class="panel-header">'
				'<div class="panel-title">Law Violations</div>'
				f'<div class="panel-count">{len(law_rows)}</div>'
				"</div>"
				f"{law_rows_html}"
				"</div>"
			),
			unsafe_allow_html=True,
		)

	_section_title("Document Knowledge Graph")
	node_count = len(clauses)
	edge_count = len(edges)
	contradiction_count = len(contradictions)

	kg_tab, = st.tabs(["Knowledge Graph"])
	with kg_tab:
		st.markdown(
			(
				'<div class="card" style="padding:0.9rem; margin-bottom:0.75rem;">'
				'<div class="graph-pill-row">'
				f'{_metric_pill("Total Nodes", node_count, "info")}'
				f'{_metric_pill("Total Edges", edge_count, "info")}'
				f'{_metric_pill("Contradiction Pairs Found", contradiction_count, "med")}'
				"</div>"
				"</div>"
			),
			unsafe_allow_html=True,
		)

		# if st.button("View Knowledge Graph", key="view_kg", use_container_width=False):
		# 	_render_knowledge_graph(clauses=clauses, graph_edges=edges)
		if st.button("View Knowledge Graph", key="view_kg", use_container_width=False):
			_render_knowledge_graph(clauses=clauses, graph_edges=edges, risks=classified_risks, contradictions=contradictions)

	_section_title("Contradictions")
	if contradictions:
		for item in sorted(contradictions, key=lambda c: _to_float(c.get("contradiction_score")), reverse=True):
			clause_a = int(item.get("clause_a_index") or 0)
			clause_b = int(item.get("clause_b_index") or 0)
			text_a = _truncate(clause_text_by_index.get(clause_a, "Clause text unavailable."), 80)
			text_b = _truncate(clause_text_by_index.get(clause_b, "Clause text unavailable."), 80)
			score = _to_float(item.get("contradiction_score"))
			confidence = _confidence_label(score)
			tone = _risk_tone(confidence)
			st.markdown(
				(
					'<div class="card contradiction-card">'
					'<div class="contradiction-grid">'
					'<div class="contr-side">'
					f'<div class="contr-clause">Clause {clause_a}</div>'
					f'<div class="contr-text">{_escape(text_a)}</div>'
					"</div>"
					'<div class="vs-tag">⚠ vs</div>'
					'<div class="contr-side">'
					f'<div class="contr-clause">Clause {clause_b}</div>'
					f'<div class="contr-text">{_escape(text_b)}</div>'
					"</div>"
					"</div>"
					'<div class="contr-meta">'
					f'<span class="pill pill-{tone}">{score:.3f}</span>'
					f'<span class="badge badge-{tone}">{confidence}</span>'
					"</div>"
					"</div>"
				),
				unsafe_allow_html=True,
			)
	else:
		_notice("No contradiction cards to display for this run.", tone="info")

	_section_title("Explanations")
	law_by_clause = {
		int(item.get("clause_index")): item.get("law_matches") or []
		for item in law_checks
		if item.get("clause_index") is not None
	}

	if not explanations:
		_notice("No explanations were returned by the backend for this run.", tone="info")

	for explanation_item in explanations:
		clause_index = int(explanation_item.get("clause_index") or 0)
		explanation_text = str(explanation_item.get("explanation") or "").strip()
		sections = _parse_explanation_sections(explanation_text)
		why_text = sections.get("why_risky") or ""
		citations = _build_citation_badges(
			explanation_item=explanation_item,
			law_matches=law_by_clause.get(clause_index, []),
			why_text=why_text,
		)
		citation_html = "".join(
			f'<span class="citation-pill">{_escape(citation)}</span>' for citation in citations
		) or '<span class="pill pill-meta">No citation detected</span>'

		st.markdown(
			(
				'<div class="card explanation-card">'
				f'<div class="explanation-title">Clause {clause_index}</div>'
				'<div class="explanation-block-title">Risk Summary</div>'
				f'<div class="explanation-body">{_escape(sections.get("risk_summary") or "Not provided.").replace("\\n", "<br>")}</div>'
				'<div class="explanation-block-title">Why Risky Under Indian Law</div>'
				f'<div class="explanation-body">{_highlight_statutes(why_text or "Not provided.")}</div>'
				'<div class="explanation-block-title">Practical Impact on Business</div>'
				f'<div class="explanation-body">{_escape(sections.get("practical_impact") or "Not provided.").replace("\\n", "<br>")}</div>'
				'<div class="explanation-block-title">Safer Rewrite Suggestion</div>'
				f'<div class="explanation-body">{_escape(sections.get("rewrite") or "Not provided.").replace("\\n", "<br>")}</div>'
				'<div class="explanation-block-title">Citations</div>'
				f'<div class="citation-row">{citation_html}</div>'
				"</div>"
			),
			unsafe_allow_html=True,
		)

		warning_text = str(explanation_item.get("warning") or "").strip()
		if warning_text:
			_notice(warning_text, tone="med")


def _render_sidebar(status: dict[str, bool]) -> str:
	with st.sidebar:
		st.markdown('<div class="sidebar-brand">⚖ ContractLens</div>', unsafe_allow_html=True)
		st.markdown('<div class="sidebar-subtitle">Indian Legal Risk Intelligence</div>', unsafe_allow_html=True)
		st.markdown('<div class="sidebar-nav-heading">Navigation</div>', unsafe_allow_html=True)

		for item in NAV_ITEMS:
			active = st.session_state.nav_page == item
			key = f"nav_{item.replace(' ', '_').lower()}"
			if st.button(item, key=key, type="primary" if active else "secondary", use_container_width=True):
				st.session_state.nav_page = item

		st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
		st.markdown('<div class="status-heading">Model Status</div>', unsafe_allow_html=True)

		inlegal_dot = "dot-up" if status["inlegalbert"] else "dot-down"
		qdrant_dot = "dot-up" if status["qdrant"] else "dot-down"
		phi3_dot = "dot-up" if status["phi3"] else "dot-warn"

		st.markdown(
			(
				'<div class="status-row"><span>InLegalBERT loaded</span>'
				f'<span class="status-dot {inlegal_dot}"></span></div>'
				'<div class="status-row"><span>Qdrant connected</span>'
				f'<span class="status-dot {qdrant_dot}"></span></div>'
				'<div class="status-row"><span>llama3:latest (Ollama)</span>'
				f'<span class="status-dot {phi3_dot}"></span></div>'
			),
			unsafe_allow_html=True,
		)

		st.markdown(
			(
				'<div class="tip-box">'
				'<div class="tip-title">Daily Legal Tip</div>'
				f'💡 Tip: {_escape(st.session_state.legal_tip)}'
				"</div>"
			),
			unsafe_allow_html=True,
		)

	return str(st.session_state.nav_page)


_init_state()
_inject_styles()
status = _runtime_status(API_BASE)
nav = _render_sidebar(status)

st.markdown(
	(
		'<div class="app-header">'
		'<p class="app-title">Contract Analysis Workspace</p>'
		'<p class="app-subtitle">Calm, reliable legal intelligence for advocates and business teams.</p>'
		"</div>"
	),
	unsafe_allow_html=True,
)

if nav == "Dashboard":
	_render_dashboard_home()
elif nav == "Law Library":
	_render_law_library_page()
elif nav == "Settings":
	_render_settings_page()
else:
	pdf, analyze_clicked = _render_upload_landing()
	if analyze_clicked:
		_run_analysis(pdf)

	if st.session_state.analysis_result:
		_render_results_dashboard(st.session_state.analysis_result)
