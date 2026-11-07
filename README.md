# GovernAI

An automated compliance screening tool for AI models and the data they touch, modelled on the "second line of defense" in bank model-risk management. It scans tabular lending data and free-text documents and produces a JSON audit report, a hash-chained audit log, a Streamlit dashboard and a downloadable compliance summary.

> **Scope note.** This is an academic prototype built on public and synthetic data. Its PASS/FAIL outputs are screening rules, not legal certification or regulatory attestation.

## What it checks

| Framework | What GovernAI actually does |
|---|---|
| NIST AI RMF / ISO/IEC 42001 | Trains a credit-style model and audits approval rates by sex, race and age group (demographic parity difference and the four-fifths rule) |
| GDPR / India DPDP Act | Detects PII in text (names, locations, emails, phones, SSNs) as data-minimization findings; generates a plain-language explanation for a rejected applicant using SHAP |
| PCI-DSS v4.0 | Finds card numbers in text (regex, Luhn checksum, issuer prefix, nearby card wording), masks them, and logs a breach |
| RBI Digital Lending Guidelines | Flags prohibited data columns (contact list, call log, SMS, media files, telephony) and excludes them from modelling |
| ISO/IEC 27001 | Writes a hash-chained audit log; any edited or removed entry breaks verification |

DPDP and ISO 42001 are covered indirectly (through the PII scan and the fairness audit); there are no checks specific to those texts.

## How it works

```
Upload / file ──► Router ──► Tabular track: DLG check → model → bias audit → SHAP explanation
                       └───► Text track:    PCI scan → PII scan (BERT NER + regex)
                                   │
                                   ▼
                outputs/audit_report.json  +  outputs/audit_log.jsonl
                                   │
                                   ▼
                  Streamlit dashboard + compliance summary (HTML)
```

## Requirements

- Windows, macOS or Linux
- [uv](https://docs.astral.sh/uv/) (it installs Python 3.12 for you)
- About 2 GB of free disk space (PyTorch plus a ~430 MB BERT model, downloaded on first use)

Git is not required.

## Setup

```powershell
uv sync
```

If you are creating the project from scratch instead:

```powershell
uv init --package --vcs none --python 3.12 governai
cd governai
uv add pandas numpy scikit-learn shap fairlearn streamlit transformers torch datasets faker pytest pyarrow
```

Optional, to silence a uv warning when the cache and project are on different drives:

```powershell
$env:UV_LINK_MODE = "copy"
```

## Data

1. **Download the public datasets** from Hugging Face (no account needed):

   ```powershell
   uv run python scripts\download_data.py
   ```

   This saves:
   - `data/raw/adult.csv`: [Adult Census Income](https://huggingface.co/datasets/scikit-learn/adult-census-income), used as a stand-in for lending decisions
   - `data/raw/pii_gretel.parquet`: first 5,000 rows of [Gretel PII Masking EN v1](https://huggingface.co/datasets/gretelai/gretel-pii-masking-en-v1) (synthetic English documents with labelled PII)

2. **Generate synthetic violations** (fake card numbers in text, a prohibited column in the lending data):

   ```powershell
   uv run python scripts\make_synthetic.py
   ```

   This creates `data/synthetic/loans_dlg.csv` and `data/synthetic/pii_with_cards.parquet`.

The first run of the text track downloads [dslim/bert-base-NER](https://huggingface.co/dslim/bert-base-NER) into your Hugging Face cache. Later runs work offline.

## Run

Always launch from the terminal with `uv run` (the VS Code play button uses the wrong interpreter and breaks Streamlit).

```powershell
# 1. Run the full pipeline and write outputs/audit_report.json
uv run python scripts\run_pipeline.py

# 2. Open the dashboard
uv run streamlit run app\streamlit_app.py
```

In the dashboard you can:

- read the framework status table and per-framework tabs
- re-run the audit from the sidebar
- upload your own CSV or Parquet file (the router picks the track)
- download `audit_report.json` and an HTML compliance summary (use your browser's Print → Save as PDF for a PDF)

### Accepted upload formats

| Route | File must contain |
|---|---|
| Text | a `text` column with free-text documents (an optional `uid` column is used as an ID) |
| Tabular | columns `age`, `sex`, `race`, `income` (Adult-style schema) |

Anything else is rejected as unsupported.

## Tests and evaluation scripts

```powershell
uv run pytest -v
```

Evaluation scripts in `scripts/`:

| Script | What it measures |
|---|---|
| `test_pii.py` | Person-name recall of the NER scan against Gretel's labels |
| `run_track_a.py` | Model accuracy and bias audit on Adult |
| `run_explain.py` | A sample plain-language rejection explanation |
| `check_pci.py` | Recall on planted card numbers |
| `check_pci2.py` | Precision: checks extra card detections against Gretel's labels |
| `check_pci_recall.py` | Recall on all labelled cards and on Luhn-valid cards |

## Project structure

```
governai/
├── app/streamlit_app.py            # dashboard
├── scripts/                        # data download, evaluation, pipeline runner
├── src/governai/
│   ├── ingestion/router.py         # tabular vs text detection
│   ├── filters/
│   │   ├── pci_scanner.py          # card detection and masking
│   │   └── dlg_validator.py        # prohibited-column check
│   ├── models/
│   │   ├── credit_model.py         # RandomForest
│   │   ├── bias_audit.py           # Fairlearn parity metrics
│   │   ├── explain.py              # SHAP and explanation memo
│   │   └── pii_ner.py              # BERT NER + regex PII scan
│   ├── audit/
│   │   ├── logger.py               # hash-chained audit log
│   │   └── certificate.py          # compliance summary
│   └── pipeline.py                 # ties everything together
├── tests/
├── data/                           # raw, synthetic, uploads (not committed)
└── outputs/                        # audit_report.json, audit_log.jsonl
```

## Measured results

These come from the synthetic and public data above; yours may differ slightly.

- **Credit model (Adult, income > 50K as the "approval" outcome):** 84.9% accuracy. Approval rates differ by sex (about 10% women vs 27% men), by race and by age group even though sex and race were not model inputs, so every attribute was flagged.
- **Name detection (BERT NER):** 34 of 42 names found (81%). Misses are mainly hyphenated surnames and an uncommon South Asian name.
- **Card detection:**
  - 9 of 10 planted cards found (the miss used a prefix outside recognised issuer ranges)
  - 12 of 12 additional detections confirmed by Gretel's labels
  - recall on Luhn-valid labelled cards: 14 of 16 (88%)
  - recall on all labelled cards: 25 of 34 (74%); most misses fail the Luhn checksum, which suggests the generated "card numbers" are malformed

## Limitations

- Adult Census (1994 income data) is a **proxy** for credit decisions, not real default data. Disparities partly reflect real differences in that data, and demographic parity does not account for legitimate factors such as age and earnings.
- The tabular track is built around Adult's column names.
- PII detection uses an English news-trained model; it is weaker on non-Western names and does not catch IDs such as Aadhaar or PAN.
- Card detection recognises Visa, Mastercard, Amex, Discover, JCB, Diners and Maestro prefixes. RuPay is not covered. Numbers over 19 digits and 12-digit cards are not matched.
- Gretel's ground-truth labels are themselves synthetic.
- The explanation memo is a template; its legal wording should be reviewed by a qualified person before any real use.
- Fairness thresholds (0.10 parity difference, four-fifths rule) are configurable choices, not regulatory standards.
- The audit log is tamper-evident, not tamper-proof: someone who rewrites the whole file and recomputes every hash would not be detected.

## Privacy

The report and log store masked card numbers, finding types and counts, never raw PII values or full card numbers.
