"""Generate three small SYNTHETIC sample PDFs so the app can be tried immediately.

These are invented example policies for a fictional company ("Northwind Finance
Ltd."), written for this project. Replace or supplement them with real public
documents (RBI, SEBI, World Bank, IIA) — see data/raw/documents/README.md.

Usage:  python scripts/make_sample_docs.py
"""

import sys
from pathlib import Path

import pymupdf

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.utils import config  # noqa: E402

COMPANY = "Northwind Finance Ltd."

DOCS = {
    "sample_internal_audit_policy.pdf": (
        "Internal Audit Policy",
        [
            ("1. Purpose and Scope",
             "This policy defines the purpose, authority and responsibilities of the Internal Audit function of "
             f"{COMPANY}. It applies to all business units, subsidiaries, outsourced processes and information systems. "
             "Internal audit is an independent, objective assurance and consulting activity designed to add value and "
             "improve the organisation's operations. It helps the organisation accomplish its objectives by bringing a "
             "systematic, disciplined approach to evaluating and improving the effectiveness of governance, risk "
             "management and control processes."),
            ("2. Independence and Reporting",
             "The Chief Audit Executive (CAE) reports functionally to the Audit Committee of the Board and "
             "administratively to the Managing Director. The Audit Committee approves the internal audit charter, the "
             "annual audit plan, the budget and the appointment or removal of the CAE. Internal auditors shall have no "
             "direct operational responsibility or authority over any of the activities they audit. An auditor who "
             "worked in a business area may not audit that area for a cooling-off period of at least twelve months."),
            ("3. Responsibilities of Internal Auditors",
             "Internal auditors are responsible for: (a) evaluating the design and operating effectiveness of internal "
             "controls; (b) identifying and assessing operational, financial and compliance risks; (c) reviewing "
             "compliance with laws, regulations and internal policies; (d) assessing the reliability and integrity of "
             "financial and operational information; (e) evaluating the safeguarding of assets; (f) reporting audit "
             "observations to management and the Audit Committee; and (g) recommending practical improvements to "
             "business processes and following up on their implementation. Internal auditors must exercise due "
             "professional care, maintain confidentiality of information obtained during audits, and avoid conflicts "
             "of interest."),
            ("4. Annual Audit Plan",
             "The CAE prepares a risk-based annual audit plan at the start of each financial year. Auditable units are "
             "rated High, Medium or Low risk based on financial materiality, regulatory exposure, past audit findings "
             "and changes in systems or management. High-risk units are audited every year, Medium-risk units at least "
             "once every two years, and Low-risk units at least once every three years. The plan is presented to the "
             "Audit Committee for approval before 30 April each year."),
            ("5. Audit Reporting and Rating of Observations",
             "A draft audit report is issued to the auditee within 10 working days of completing fieldwork. Management "
             "must provide written responses and agreed action plans within 15 working days. Observations are rated "
             "Critical, High, Medium or Low. Critical observations are reported to the Audit Committee chair within 48 "
             "hours. The final report is issued to the Managing Director and summarised for the Audit Committee every "
             "quarter."),
            ("6. Follow-up of Audit Observations",
             "Internal Audit tracks all open observations in the audit issue register. Critical and High observations "
             "must be remediated within 60 days and Medium observations within 90 days. Internal Audit verifies "
             "closure by testing evidence; management self-certification alone is not sufficient. Overdue observations "
             "are escalated to the Audit Committee every quarter."),
            ("7. Quality Assurance",
             "The internal audit function maintains a quality assurance and improvement programme. An internal "
             "self-assessment is performed annually and an external quality assessment is carried out at least once "
             "every five years by a qualified independent reviewer."),
        ],
    ),
    "sample_risk_management_guidelines.pdf": (
        "Enterprise Risk Management Guidelines",
        [
            ("1. Objective",
             f"These guidelines set out how {COMPANY} identifies, assesses, responds to, monitors and reports risks. "
             "The objective of enterprise risk management (ERM) is to support the achievement of strategic objectives, "
             "protect the company's capital and reputation, and ensure that risks are taken knowingly and within the "
             "approved risk appetite."),
            ("2. Three Lines Model",
             "Risk management responsibilities follow the three lines model. The first line consists of business and "
             "operational management who own and manage risks day to day. The second line consists of the risk "
             "management and compliance functions, which set frameworks, monitor risks and challenge the first line. "
             "The third line is internal audit, which provides independent assurance to the Board on the effectiveness "
             "of governance, risk management and internal control."),
            ("3. Risk Appetite",
             "The Board approves a risk appetite statement annually. The company has a low appetite for compliance and "
             "regulatory risk, a low appetite for fraud, a moderate appetite for credit risk within approved sector "
             "limits, and a moderate appetite for operational risk where the cost of control exceeds the expected loss. "
             "Any breach of a risk appetite limit must be reported to the Chief Risk Officer within one working day."),
            ("4. Risk Identification and Assessment",
             "Each department maintains a risk register, reviewed at least quarterly. Every risk is scored on "
             "likelihood (1 to 5) and impact (1 to 5). The risk score is likelihood multiplied by impact. Scores of 15 "
             "or above are High risks, scores from 8 to 14 are Medium risks, and scores of 7 or below are Low risks. "
             "Each risk must have a named risk owner, existing controls, and a residual rating after considering "
             "those controls."),
            ("5. Risk Response",
             "Risk owners choose one of four responses: avoid the activity, reduce the risk through additional "
             "controls, transfer the risk through insurance or contracts, or accept the risk. High residual risks may "
             "only be accepted with written approval from the Risk Management Committee."),
            ("6. Key Risk Indicators and Reporting",
             "Key risk indicators (KRIs) with green, amber and red thresholds are defined for all High risks. The Chief "
             "Risk Officer presents a consolidated risk report to the Risk Management Committee every quarter, "
             "including the top ten risks, KRI breaches, new and emerging risks, and the status of risk mitigation "
             "actions."),
            ("7. Fraud Risk",
             "Fraud risk assessments are performed annually for all key processes. Suspected fraud must be reported "
             "through the whistle-blower channel or directly to the Chief Risk Officer. Investigations are led by an "
             "independent team and the outcome is reported to the Audit Committee."),
        ],
    ),
    "sample_compliance_guidelines.pdf": (
        "Regulatory Compliance Guidelines",
        [
            ("1. Compliance Function",
             f"The Compliance function of {COMPANY} is headed by the Chief Compliance Officer (CCO), who is appointed "
             "by the Board and has direct access to the Audit Committee. The function is independent of business "
             "units and is responsible for identifying applicable regulations, advising management, monitoring "
             "adherence and reporting breaches."),
            ("2. Compliance Calendar",
             "The Compliance team maintains a compliance calendar listing every regulatory filing, return and "
             "disclosure, with its due date and owner. Owners must confirm completion of each filing in the compliance "
             "tool on or before the due date. Missed or delayed filings are reported to the CCO on the same day."),
            ("3. Know Your Customer and Anti-Money Laundering",
             "Customer due diligence must be completed before an account is opened. Customers are classified as "
             "Low, Medium or High risk. Records of High-risk customers are updated every two years, Medium-risk "
             "customers every eight years, and Low-risk customers every ten years. Suspicious transactions must be "
             "reported to the Principal Officer immediately and filed with the authorities within the regulatory "
             "timeline."),
            ("4. Compliance Testing",
             "The Compliance team performs risk-based compliance testing every quarter. Test results are rated "
             "Compliant, Partially Compliant or Non-Compliant. Non-Compliant results require a corrective action plan "
             "within 30 days."),
            ("5. Breach Reporting",
             "Any regulatory breach, whether identified by business units, compliance testing or internal audit, must "
             "be logged in the breach register within two working days. Material breaches are reported to the Board "
             "and, where required, to the regulator."),
            ("6. Training",
             "All employees complete compliance and code-of-conduct training on joining and refresher training every "
             "year. Employees in high-risk roles, such as treasury, payments and customer onboarding, complete "
             "additional role-specific training every six months."),
            ("7. Record Retention",
             "Compliance records, audit evidence and customer due diligence documents are retained for at least eight "
             "years, or longer where a regulation requires it."),
        ],
    ),
}

PAGE_W, PAGE_H = 595, 842  # A4 points
MARGIN = 60


def build_pdf(path: Path, title: str, sections: list[tuple[str, str]]) -> None:
    doc = pymupdf.open()
    # two sections per page -> several pages, so page citations are meaningful
    for page_no, start in enumerate(range(0, len(sections), 2), start=1):
        page = doc.new_page(width=PAGE_W, height=PAGE_H)
        page.insert_text((MARGIN, 35), f"{COMPANY} | {title} | SAMPLE DOCUMENT", fontsize=8, color=(0.4, 0.4, 0.4))
        page.insert_text((PAGE_W / 2 - 20, PAGE_H - 30), f"Page {page_no}", fontsize=8, color=(0.4, 0.4, 0.4))
        y = MARGIN
        if page_no == 1:
            page.insert_text((MARGIN, y + 10), title, fontsize=18)
            page.insert_text((MARGIN, y + 30), f"{COMPANY} - Version 1.0", fontsize=10)
            y += 60
        for heading, body in sections[start : start + 2]:
            page.insert_text((MARGIN, y + 12), heading, fontsize=12)
            y += 24
            rect = pymupdf.Rect(MARGIN, y, PAGE_W - MARGIN, PAGE_H - 70)
            spare = page.insert_textbox(rect, body, fontsize=10.5, lineheight=1.35)
            used = rect.height - spare if spare >= 0 else rect.height
            y += used + 20
    doc.save(path)
    doc.close()


def main() -> None:
    config.RAW_DOCS_DIR.mkdir(parents=True, exist_ok=True)
    for filename, (title, sections) in DOCS.items():
        out = config.RAW_DOCS_DIR / filename
        build_pdf(out, title, sections)
        print(f"  ✓ {out.relative_to(config.PROJECT_ROOT)}")
    print("\nNext: python scripts/ingest.py")


if __name__ == "__main__":
    main()
