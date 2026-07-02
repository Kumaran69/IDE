"""
Intelligent Document Extraction System
---------------------------------------
Streamlit UI: upload an invoice / KYC form image, run OCR + field
extraction, and view/download the structured output.

Run with:  streamlit run app.py
"""

import json
import io

import pandas as pd
import streamlit as st
from PIL import Image

from extractor import process_document

st.set_page_config(page_title="Document Extraction System", page_icon="📄", layout="wide")

st.title("📄 Intelligent Document Extraction System")
st.caption(
    "AI/ML pipeline that reads scanned invoices, purchase orders, and KYC forms "
    "and converts them into structured, usable data — automating manual data entry."
)

with st.sidebar:
    st.header("About this project")
    st.write(
        """
        **Pipeline:**
        1. Image preprocessing (denoise + adaptive threshold)
        2. OCR text extraction (Tesseract)
        3. Rule-based / regex field parsing
        4. Structured JSON + CSV output with confidence scores

        **Use case:** Automating document processing for
        healthcare, fintech, and logistics clients — reducing
        manual entry time and errors.
        """
    )
    st.divider()
    st.write("Try the bundled sample documents, or upload your own scanned invoice / KYC form image.")

sample_choice = st.selectbox(
    "Quick test with a sample document",
    ["-- none --", "sample_docs/invoice_1.png", "sample_docs/invoice_2.png", "sample_docs/kyc_form_1.png"],
)

uploaded_file = st.file_uploader("Or upload your own document (PNG/JPG)", type=["png", "jpg", "jpeg"])

image = None
if uploaded_file is not None:
    image = Image.open(uploaded_file)
elif sample_choice != "-- none --":
    image = Image.open(sample_choice)

if image is not None:
    col1, col2 = st.columns([1, 1.2])

    with col1:
        st.subheader("Input Document")
        st.image(image, use_container_width=True)

    with st.spinner("Running OCR and extracting fields..."):
        result = process_document(image)

    with col2:
        st.subheader("Extracted Structured Data")
        st.metric("Document Type", result.document_type)
        st.metric("OCR Confidence", f"{result.ocr_confidence}%")

        table_rows = [
            ("Vendor / Name", result.vendor_or_name, result.field_confidence.get("vendor_or_name")),
            ("Invoice / ID Number", result.id_or_invoice_number, result.field_confidence.get("id_or_invoice_number")),
            ("Date", result.date, result.field_confidence.get("date")),
            ("Due Date", result.due_date, None),
            ("Total Amount", result.total_amount, result.field_confidence.get("total_amount")),
        ]
        df = pd.DataFrame(table_rows, columns=["Field", "Extracted Value", "Confidence"])
        st.dataframe(df, use_container_width=True, hide_index=True)

        json_bytes = json.dumps(result.to_dict(), indent=2).encode("utf-8")
        csv_bytes = df.to_csv(index=False).encode("utf-8")

        dl1, dl2 = st.columns(2)
        with dl1:
            st.download_button("⬇ Download JSON", json_bytes, file_name="extracted_data.json", mime="application/json")
        with dl2:
            st.download_button("⬇ Download CSV", csv_bytes, file_name="extracted_data.csv", mime="text/csv")

    with st.expander("Raw OCR text (for debugging / transparency)"):
        st.text(result.raw_text)
else:
    st.info("Select a sample document above or upload your own to get started.")