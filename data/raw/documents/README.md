# Source documents

Currently included: RBI Master Directions on Fraud Risk Management in NBFCs (2024), SEBI LODR Master Circular, CAG Compliance Audit Report No. 5 of 2026, DoT Internal Audit Manual (3rd ed.), and World Bank Financial Management training slides.

Put your PDF documents here, then run `python scripts/ingest.py` (or upload them in the app).

## Included samples

`scripts/make_sample_docs.py` creates three **synthetic** policies for a fictional company,
Northwind Finance Ltd., written for this project so the app works immediately:

- `sample_internal_audit_policy.pdf`
- `sample_risk_management_guidelines.pdf`
- `sample_compliance_guidelines.pdf`

`evaluation/test_questions.json` has 24 test questions with the expected file and page for these.

## Real public documents to add (target: 5-10 PDFs, 100-300 pages)

| Category | Where to look |
|---|---|
| Banking regulation, KYC, risk | RBI Master Directions — https://www.rbi.org.in/Scripts/BS_ViewMasDirections.aspx |
| Listing & disclosure compliance | SEBI regulations / circulars — https://www.sebi.gov.in/legal.html |
| Financial management & audit | World Bank documents — https://documents.worldbank.org/ |
| Internal audit standards | The Institute of Internal Auditors — https://www.theiia.org/ (some material needs membership) |

Tips:
- Use **text-based** PDFs (you can select text in them). Scanned PDFs need OCR, which is not built in yet — ingestion warns you about them.
- Check each document's usage terms before publishing the project with the files included.
- Original files here are never modified; processed text goes to `data/processed/`.
