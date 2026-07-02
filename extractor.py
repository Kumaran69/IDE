"""
extractor.py
------------
Core pipeline for the Intelligent Document Extraction System.

Steps:
 1. Preprocess image (grayscale, denoise, threshold) to improve OCR accuracy
 2. Run OCR (Tesseract) to get raw text
 3. Parse raw text with rule-based + regex logic to pull structured fields
    (invoice number, date, vendor/company name, total amount, due date,
    name, ID number -- adapts to invoice-type vs KYC-type documents)

This mirrors a real production document-extraction pipeline: preprocessing
-> OCR -> structured field parsing -> confidence scoring -> JSON output.
"""

import re
import io
from dataclasses import dataclass, field
from typing import Optional

import cv2
import numpy as np
import pytesseract
from PIL import Image

# --- Windows only: uncomment and set this to your Tesseract install path ---
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


# ---------------------------------------------------------------------------
# 1. Image preprocessing
# ---------------------------------------------------------------------------
def preprocess_image(pil_image: Image.Image) -> np.ndarray:
    """Convert to grayscale, denoise, and threshold to boost OCR accuracy."""
    img = np.array(pil_image.convert("RGB"))
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    # Slight denoise
    gray = cv2.fastNlMeansDenoising(gray, h=15)

    # Adaptive threshold works well for both printed & scanned/handwritten docs
    thresh = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 11
    )
    return thresh


# ---------------------------------------------------------------------------
# 2. OCR
# ---------------------------------------------------------------------------
def run_ocr(preprocessed_img: np.ndarray) -> str:
    """Run Tesseract OCR on the preprocessed image and return raw text."""
    config = "--oem 3 --psm 6"  # PSM 6 = assume a uniform block of text
    text = pytesseract.image_to_string(preprocessed_img, config=config)
    return text


def get_ocr_confidence(preprocessed_img: np.ndarray) -> float:
    """Average word-level confidence score from Tesseract (0-100)."""
    data = pytesseract.image_to_data(
        preprocessed_img, config="--oem 3 --psm 6", output_type=pytesseract.Output.DICT
    )
    confs = [int(c) for c in data["conf"] if c not in ("-1", -1)]
    return round(sum(confs) / len(confs), 1) if confs else 0.0


# ---------------------------------------------------------------------------
# 3. Field parsing
# ---------------------------------------------------------------------------
@dataclass
class ExtractedFields:
    document_type: str = "unknown"
    vendor_or_name: Optional[str] = None
    id_or_invoice_number: Optional[str] = None
    date: Optional[str] = None
    due_date: Optional[str] = None
    total_amount: Optional[str] = None
    raw_text: str = ""
    ocr_confidence: float = 0.0
    field_confidence: dict = field(default_factory=dict)

    def to_dict(self):
        return {
            "document_type": self.document_type,
            "vendor_or_name": self.vendor_or_name,
            "id_or_invoice_number": self.id_or_invoice_number,
            "date": self.date,
            "due_date": self.due_date,
            "total_amount": self.total_amount,
            "ocr_confidence": self.ocr_confidence,
            "field_confidence": self.field_confidence,
        }


DATE_PATTERN = r"(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})"
AMOUNT_PATTERN = r"(?:Rs\.?\s?|INR\s?|₹\s?)?([\d,]+\.\d{2})"


def classify_document(text: str) -> str:
    lower = text.lower()
    if "kyc" in lower or "identity form" in lower or "date of birth" in lower:
        return "KYC / Identity Form"
    if "invoice" in lower or "bill to" in lower or "gst" in lower:
        return "Invoice"
    return "Unknown"


def extract_field(pattern: str, text: str, flags=re.IGNORECASE):
    match = re.search(pattern, text, flags)
    return match.group(1).strip() if match else None


def parse_fields(raw_text: str, ocr_confidence: float) -> ExtractedFields:
    doc_type = classify_document(raw_text)
    result = ExtractedFields(document_type=doc_type, raw_text=raw_text, ocr_confidence=ocr_confidence)
    conf = {}

    if doc_type == "Invoice":
        # Vendor name -> first non-empty line of the document
        lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
        result.vendor_or_name = lines[0] if lines else None
        conf["vendor_or_name"] = 0.7  # heuristic-based, medium confidence

        inv_num = extract_field(r"invoice\s*(?:no\.?|number)?\s*[:\-]?\s*([A-Za-z0-9/\-]+)", raw_text)
        result.id_or_invoice_number = inv_num
        conf["id_or_invoice_number"] = 0.9 if inv_num else 0.0

        dates = re.findall(DATE_PATTERN, raw_text)
        result.date = dates[0] if len(dates) > 0 else None
        result.due_date = dates[-1] if len(dates) > 1 else None
        conf["date"] = 0.85 if result.date else 0.0

        totals = re.findall(r"total\s*amount\s*[:\-]?\s*" + AMOUNT_PATTERN, raw_text, re.IGNORECASE)
        if not totals:
            totals = re.findall(AMOUNT_PATTERN, raw_text)
        result.total_amount = totals[-1] if totals else None
        conf["total_amount"] = 0.9 if totals else 0.0

    elif doc_type == "KYC / Identity Form":
        name = extract_field(r"(?:full\s*name|name)\s*[:\-]\s*([A-Za-z .]+)", raw_text)
        result.vendor_or_name = name
        conf["vendor_or_name"] = 0.9 if name else 0.0

        id_num = extract_field(r"id\s*number\s*[:\-]?\s*([A-Za-z0-9\-]+)", raw_text)
        result.id_or_invoice_number = id_num
        conf["id_or_invoice_number"] = 0.9 if id_num else 0.0

        dob = extract_field(r"date\s*of\s*birth\s*[:\-]?\s*" + DATE_PATTERN, raw_text)
        result.date = dob
        conf["date"] = 0.85 if dob else 0.0

    else:
        # Fallback generic extraction
        dates = re.findall(DATE_PATTERN, raw_text)
        result.date = dates[0] if dates else None
        amounts = re.findall(AMOUNT_PATTERN, raw_text)
        result.total_amount = amounts[-1] if amounts else None

    result.field_confidence = conf
    return result


# ---------------------------------------------------------------------------
# 4. End-to-end pipeline
# ---------------------------------------------------------------------------
def process_document(pil_image: Image.Image) -> ExtractedFields:
    preprocessed = preprocess_image(pil_image)
    raw_text = run_ocr(preprocessed)
    ocr_conf = get_ocr_confidence(preprocessed)
    fields = parse_fields(raw_text, ocr_conf)
    return fields


if __name__ == "__main__":
    # Quick CLI test against the generated sample docs
    import os
    import json

    sample_dir = "sample_docs"
    for fname in sorted(os.listdir(sample_dir)):
        path = os.path.join(sample_dir, fname)
        img = Image.open(path)
        result = process_document(img)
        print(f"\n=== {fname} ===")
        print(json.dumps(result.to_dict(), indent=2))