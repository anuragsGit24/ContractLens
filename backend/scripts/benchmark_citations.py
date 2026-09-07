"""Task 4 benchmark: citation verification and generative hallucination audit."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pandas as pd
from tqdm import tqdm

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.schemas.contracts import (  # noqa: E402
    CitationVerification,
    Clause,
    ClauseExplanation,
    ClauseLawCheck,
    ClauseRisk,
    InternalContradiction,
    LawMatch,
)
from backend.services.law_checker import check_against_law  # noqa: E402
from backend.services.llm_explainer import explain_clause  # noqa: E402


SAMPLE_CLAUSES = [
    {"id": 1, "cat": "Liability", "text": "The Selected Bidder hereby indemnifies and holds harmless at all times the Share Seller against all losses, damages, charges, and expenses which the Share Seller may sustain or incur towards contractual obligations with respect to the contracts awarded by the Share Seller or any other liability arising with regard to any action/activity undertaken by the Share Seller."},
    {"id": 2, "cat": "Liability", "text": "Any and all claims, demands, losses, damages, defense costs, or liability of any kind or nature which COMMISSION may sustain or incur or which may be imposed upon it for injury to or death of persons, or damage to property which arise out of, pertain to, or relate to CONSULTANT’S negligence, recklessness, or willful misconduct under the terms of this Agreement."},
    {"id": 3, "cat": "Liability", "text": "The SPD shall indemnify, defend and hold SECI harmless against: any and all third party claims against SECI for any loss of or damage to property of such third party, or death or injury to such third party, arising out of a breach by the SPD of any of its obligations under this Agreement or due to the SPD’s willful misconduct, gross negligence or fraudulent behaviour."},
    {"id": 4, "cat": "Liability", "text": "Except as expressly provided in this Agreement, neither the SPD nor SECI nor Buying Entity(ies) shall be liable or responsible to the other Party for incidental, indirect or consequential damages, connected with or resulting from performance or non-performance of this Agreement, including claims in the nature of lost revenues, income or profits."},
    {"id": 5, "cat": "Defect Liability", "text": "It is agreed that in case any structural defect or any other defect in workmanship, quality or provision of services... is brought to the notice of the Promoter within a period of 5 (five) years by the Allottee from the date of handing over possession, it shall be the duty of the Promoter to rectify such defects without further charge, within 30 (thirty) days."},
    {"id": 6, "cat": "Warranty", "text": "The Shares Seller and the Nominees are the legal and beneficial owners of the Sale Shares, free and clear of any Encumbrance and the delivery to the Selected Bidder of the Sale Shares pursuant to the provisions of this Agreement will transfer to the Selected Bidder a good title to the Sale Shares."},
    {"id": 7, "cat": "Warranty", "text": "If a license of any kind is required of CONSULTANT, its employees, agents, or sub CONSULTANTs by Federal or State law, CONSULTANT warrants that such license has been obtained, is valid and in good standing, and that CONSULTANT shall keep it in effect at all times during the terms of this Agreement."},
    {"id": 8, "cat": "Warranty", "text": "There are no litigations pending before any Court of law or Authority with respect to the said Land, Project or the [Apartment/Plot]."},
    {"id": 9, "cat": "Termination", "text": "COMMISSION may terminate this Agreement for its convenience any time, in whole or part, by giving CONSULTANT thirty-day (30-day) written notice thereof. Within thirty days of the COMMISSION's receipt of CONSULTANT's final billing, COMMISSION shall pay CONSULTANT its allowable costs incurred to date of termination."},
    {"id": 10, "cat": "Termination", "text": "COMMISSION may terminate this Agreement for CONSULTANT's default if CONSULTANT breaches any term(s) or violates any provision(s) of this Agreement and does not cure such breach or violation within ten (10) days after written notice thereof by COMMISSION. CONSULTANT shall be liable for any and all reasonable costs incurred by COMMISSION."},
    {"id": 11, "cat": "Termination", "text": "If (i) the Closing does not occur on the Closing Date for any reason whatsoever, or (ii) the Letter of Intent is withdrawn or terminated for any reason, or (iii) due to termination of the TSA by Central Transmission Utility of India Limited, PFCCL shall have a right to terminate this Agreement forthwith by giving a written notice."},
    {"id": 12, "cat": "Termination", "text": "Provided that where the allottee proposes to cancel/withdraw from the project without any fault of the promoter, the promoter herein is entitled to forfeit the booking amount paid for the allotment. The balance amount of money paid by the allottee shall be returned by the promoter to the allottee within 45 days of such cancellation."},
    {"id": 13, "cat": "IP", "text": "All material, data, information, and written, graphic or other work produced under this Agreement is subject to the unqualified and unconditional right of the COMMISSION to use, reproduce, publish, display, and make derivative use of all such work, or any part of it, free of charge and in any manner and for any purpose."},
    {"id": 14, "cat": "IP", "text": "If any of the work is subject to copyright, trademark, service mark, or patent, CONSULTANT now grants to the COMMISSION a perpetual, royalty-free, nonexclusive and irrevocable license to use, reproduce, publish, use in the creation of derivative works, and display and perform the work."},
    {"id": 15, "cat": "IP", "text": "Upon completion of all work under this contract, ownership and title to all custom letters, reports, documents, plans, specifications, and estimates and other products produced as part of this Agreement will automatically be vested in the COMMISSION... Such deliverables shall be deemed works made for hire."},
    {"id": 16, "cat": "Pricing", "text": "The Total Price is escalation-free, save and except increases which the Allottee hereby agrees to pay, due to increase on account of development charges payable to the competent authority and/or any other increase in charges which may be levied or imposed by the competent authority from time to time."},
    {"id": 17, "cat": "Pricing", "text": "Subsequent to commencement of power supply by the SPD on the terms contained in this Agreement, the SPD shall be entitled to receive the Tariff of Rs. ............../ kWh fixed for the entire term of this Agreement."},
    {"id": 18, "cat": "Pricing", "text": "On the occurrence of a change in law, the monthly tariff or charges shall be adjusted and be recovered in accordance with the Electricity (Timely Recovery of Costs due to Change in Law) Rules, 2021 to compensate the affected party so as to restore such affected party to the same economic position."},
    {"id": 19, "cat": "Payment", "text": "In the event of delay in payment of a Monthly Bill by SECI beyond the Due Date, a Late Payment Surcharge shall be payable by SECI to the SPD on the outstanding payment, at the base rate of Late Payment Surcharge applicable for the period for the first month of default."},
    {"id": 20, "cat": "Payment", "text": "Total payment is not to exceed $ for time and materials at the rates and conditions set forth in Exhibit B: Fee Schedule. In no event, will the CONSULTANT be reimbursed for overhead costs at a rate that exceeds the overhead rate set forth in the Fee Schedule."},
    {"id": 21, "cat": "Dispute Resolution", "text": "All or any disputes arising out or touching upon or in relation to the terms and conditions of this Agreement, including the interpretation and validity of the terms thereof, shall be settled amicably by mutual discussion, failing which the same shall be settled through the adjudicating officer appointed under the Act."},
    {"id": 22, "cat": "Dispute Resolution", "text": "In the event the Dispute is not settled amicably, any Party shall be entitled to serve a notice invoking this Clause and making a reference to a sole arbitrator. The place of the arbitration shall be New Delhi. The Arbitration proceedings shall be governed by the Arbitration and Conciliation Act, 1996."},
    {"id": 23, "cat": "Dispute Resolution", "text": "This Agreement shall be governed by and construed in accordance with the Laws of India. Any legal proceedings in respect of any matters, claims or disputes under this Agreement shall be under the jurisdiction of appropriate courts in Delhi."},
    {"id": 24, "cat": "Dispute Resolution", "text": "In the event CERC is the Appropriate Commission, any dispute that arises claiming any change in or regarding determination of the tariff or any tariff related matters shall be adjudicated by the CERC. All other disputes shall be resolved by arbitration under the Indian Arbitration and Conciliation Act, 1996."},
    {"id": 25, "cat": "Force Majeure", "text": "The Promoter assures to hand over possession of the [Apartment/Plot] on or before the specified date, UNLESS there is delay or failure due to war, flood, drought, fire, cyclone, earthquake or any other calamity caused by nature affecting the regular development of the real estate project (“Force Majeure”)."},
    {"id": 26, "cat": "Force Majeure", "text": "‘Force Majeure’ means Act of God, including, but not limited to lightning, drought, fire and explosion (to the extent originating from a source external to the site), earthquake, volcanic eruption, landslide, flood, cyclone, typhoon or tornado if and only if it is declared / notified by the competent authority."},
    {"id": 27, "cat": "Force Majeure", "text": "Force Majeure shall not include: a. Unavailability, late delivery, or changes in cost of the plant, machinery, equipment; b. Delay in the performance of any contractor, sub-contractor; c. Insufficiency of finances or funds or the agreement becoming onerous to perform."},
    {"id": 28, "cat": "Negative Covenant", "text": "After the Promoter executes this Agreement he shall not mortgage or create a charge on the [Apartment/Plot/Building] and if any such mortgage or charge is made or created, such mortgage or charge shall not affect the right and interest of the Allottee."},
    {"id": 29, "cat": "Compliance", "text": "CONSULTANT and COMMISSION agree that CONSULTANT is an independent CONSULTANT and not an employee of COMMISSION. CONSULTANT is responsible for all insurance (workers compensation, unemployment, etc.) and all payroll related taxes. CONSULTANT is not entitled to any employee benefits."},
    {"id": 30, "cat": "Confidentiality", "text": "The Parties undertake to hold in confidence and not to disclose the terms and conditions of the transaction contemplated hereby to third parties, except to their professional advisors, officers, employees, agents or disclosures required under Law."},
]


def _as_strings(values: list[str] | None) -> list[str]:
    return [str(value) for value in (values or [])]


def _law_summary(matches: list[LawMatch]) -> str:
    return " | ".join(
        f"{match.act} Section {match.section_number}: {match.title}"
        for match in matches
    )


def run_benchmark() -> dict[str, float | int]:
    clauses = [
        Clause(index=item["id"], label=item["cat"], text=item["text"])
        for item in SAMPLE_CLAUSES
    ]

    print("Loading law matches for 30 clauses...")
    law_checks = check_against_law(clauses=clauses, top_k_raw=10, top_k_final=3)
    checks_by_clause: dict[int, ClauseLawCheck] = {
        check.clause_index: check for check in law_checks
    }

    rows: list[dict[str, Any]] = []
    total_citations = 0
    supported_citations = 0
    ghost_citations = 0
    passed_outputs = 0

    print("Generating explanations and auditing citations...")
    for clause in tqdm(clauses, desc="Auditing citations"):
        law_check = checks_by_clause.get(
            clause.index,
            ClauseLawCheck(clause_index=clause.index, law_matches=[]),
        )
        law_matches = law_check.law_matches
        risk = ClauseRisk(
            clause_index=clause.index,
            top_category=clause.label,
            top_score=0.85,
            category_scores={clause.label: 0.85},
            risk_level="High",
            risk_level_relative="High",
        )

        explanation_obj: ClauseExplanation | None = None
        error = ""
        verification = CitationVerification(
            extracted_citations=[],
            supported_citations=[],
            unsupported_citations=[],
            passed=False,
        )
        try:
            explanation_obj = explain_clause(
                clause=clause,
                risk=risk,
                contradictions=[],
                law_matches=law_matches,
            )
            verification = explanation_obj.citation_verification
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
            print(f"Clause {clause.index} failed: {error}")

        extracted = _as_strings(verification.extracted_citations)
        supported = _as_strings(verification.supported_citations)
        unsupported = _as_strings(verification.unsupported_citations)
        total_citations += len(extracted)
        supported_citations += len(supported)
        ghost_citations += len(unsupported)
        passed_outputs += int(verification.passed and not error)

        rows.append(
            {
                "clause_id": clause.index,
                "category": clause.label,
                "clause_text": clause.text,
                "retrieved_laws": _law_summary(law_matches),
                "law_match_count": len(law_matches),
                "llm_explanation": explanation_obj.explanation if explanation_obj else "",
                "explanation_snippet": (explanation_obj.explanation[:500] if explanation_obj else ""),
                "extracted_citations": " | ".join(extracted),
                "supported_citations": " | ".join(supported),
                "ghost_citations": " | ".join(unsupported),
                "citation_passed": verification.passed if not error else False,
                "warning": explanation_obj.warning if explanation_obj else "",
                "error": error,
            }
        )

    total_outputs = len(clauses)
    precision = supported_citations / total_citations if total_citations else 0.0
    ghost_rate = ghost_citations / total_citations if total_citations else 0.0
    trust_score = passed_outputs / total_outputs if total_outputs else 0.0

    print("\n| Citation Metric | ContractLens | Dahl et al. (2024) |")
    print("|---|---:|---:|")
    print(f"| Citation Precision | {precision:.2%} | Not reported |")
    print(f"| Ghost Citation Rate | {ghost_rate:.2%} | 17% - 34% hallucination rate |")
    print(f"| Trust Score | {trust_score:.2%} | Not reported |")
    print(f"| Total citations | {total_citations} | - |")
    print(f"| Supported citations | {supported_citations} | - |")
    print(f"| Ghost citations | {ghost_citations} | - |")
    print(f"| Passed outputs | {passed_outputs}/{total_outputs} | - |")

    output_path = ROOT_DIR / "data" / "task4_citation_evaluation_results.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(output_path, index=False)
    print(f"\nDetailed citation audit saved to: {output_path}")

    return {
        "total_outputs": total_outputs,
        "total_citations": total_citations,
        "supported_citations": supported_citations,
        "ghost_citations": ghost_citations,
        "passed_outputs": passed_outputs,
        "citation_precision": precision,
        "ghost_citation_rate": ghost_rate,
        "trust_score": trust_score,
    }


if __name__ == "__main__":
    run_benchmark()
