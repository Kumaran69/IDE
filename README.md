# Intelligent Document Extraction System (OCR + AI-based Field Parsing)

An end-to-end AI/ML pipeline that reads scanned invoices, purchase orders, and KYC/identity forms — including messy, real-world layouts — and converts them into clean, structured data (JSON/CSV), eliminating manual data entry.

## Problem Statement

Organizations in healthcare, fintech, and logistics process thousands of invoices, purchase orders, and identity documents every month. Manually keying in vendor names, invoice numbers, dates, and totals is slow, expensive, and error-prone. This project automates that pipeline end-to-end: **scanned document in → structured, validated data out.**

This directly mirrors real industry document-processing pipelines used by data/AI service providers working across healthcare, fintech, and logistics clients.

## How It Works

```
Scanned Document (image)
        │
        ▼
1. Preprocessing  → grayscale, denoise, adaptive thresholding (OpenCV)
        │
        ▼
2. OCR             → Tesseract OCR extracts raw text
        │
        ▼
3. Field Parsing    → document classification + regex/rule-based
                       extraction of key fields (vendor, invoice #,
                       dates, totals, or name/DOB/ID for KYC forms)
        │
        ▼
4. Structured Output → JSON / CSV with per-field confidence scores
```

## Tech Stack

- **OpenCV** – image preprocessing for OCR accuracy
- **Tesseract OCR (pytesseract)** – text extraction from scanned images
- **Python (regex-based rule engine)** – structured field parsing and document classification
- **Streamlit** – interactive web UI for upload → extract → download
- **Pandas** – tabular structuring of extracted fields

## Results (on test samples)

| Document | OCR Confidence | Fields Correctly Extracted |
|---|---|---|
| Invoice 1 (Medical Supplies) | 90.9% | 5/5 |
| Invoice 2 (Logistics) | 93.2% | 5/5 |
| KYC Form | 93.7% | 3/3 |

## Running It

```bash
pip install -r requirements.txt
# Tesseract OCR engine must be installed on the system:
#   Ubuntu/Debian: sudo apt-get install tesseract-ocr
#   Mac: brew install tesseract

streamlit run app.py
```

Then open the local URL, pick a sample document (or upload your own invoice/KYC image), and view the extracted structured data with confidence scores. Results can be downloaded as JSON or CSV.

## Business Impact

- **Reduces manual data-entry time** for invoices/forms from minutes to seconds per document
- **Cuts human transcription errors** in financial and identity data
- **Confidence scoring per field** enables a human-in-the-loop review workflow for low-confidence extractions — a production-safe design rather than a black box
- Directly extensible to **healthcare records, purchase orders, and financial KYC pipelines** — the exact document types used across healthcare, fintech, and logistics workflows

## Possible Extensions

- Swap regex parsing for a fine-tuned NER model (spaCy/BERT) or a layout-aware model (LayoutLMv3/Donut) for handling more varied/handwritten layouts
- Add a correction UI so human reviewers can fix low-confidence fields, feeding back into model improvement
- Expose the pipeline as a REST API (FastAPI) so it can plug into existing EHR/ERP systems