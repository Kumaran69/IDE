"""
Generates a few synthetic invoice images so the extraction pipeline
can be demoed end-to-end without needing an external dataset.
"""
from PIL import Image, ImageDraw, ImageFont
import os

OUT_DIR = "sample_docs"
os.makedirs(OUT_DIR, exist_ok=True)

def get_font(size=22):
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    for p in paths:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

INVOICES = [
    {
        "filename": "invoice_1.png",
        "lines": [
            ("ACME MEDICAL SUPPLIES PVT LTD", 26, True),
            ("123 Anna Salai, Chennai, Tamil Nadu - 600002", 18, False),
            ("", 10, False),
            ("Invoice Number: INV-20458", 20, False),
            ("Invoice Date: 15-06-2026", 20, False),
            ("Bill To: Apollo Hospitals, Madurai", 20, False),
            ("", 10, False),
            ("Description                Qty      Rate       Amount", 18, False),
            ("Surgical Gloves (Box)       10       450.00     4500.00", 18, False),
            ("N95 Masks (Pack of 50)      5        1200.00    6000.00", 18, False),
            ("Digital Thermometer         20       650.00    13000.00", 18, False),
            ("", 10, False),
            ("Subtotal:                                     23500.00", 18, False),
            ("GST (18%):                                     4230.00", 18, False),
            ("Total Amount: Rs. 27730.00", 22, True),
            ("", 10, False),
            ("Payment Due Date: 30-06-2026", 18, False),
        ],
    },
    {
        "filename": "invoice_2.png",
        "lines": [
            ("GREENLINE LOGISTICS PVT LTD", 26, True),
            ("45 Industrial Estate, Coimbatore - 641021", 18, False),
            ("", 10, False),
            ("Invoice No: GL/2026/0872", 20, False),
            ("Date: 22-06-2026", 20, False),
            ("Customer: Sri Textiles Pvt Ltd", 20, False),
            ("", 10, False),
            ("Description               Qty     Rate      Amount", 18, False),
            ("Freight Charges           1       15000.00  15000.00", 18, False),
            ("Warehouse Handling        1        2500.00   2500.00", 18, False),
            ("Insurance                 1        1000.00   1000.00", 18, False),
            ("", 10, False),
            ("Subtotal:                                   18500.00", 18, False),
            ("GST (18%):                                   3330.00", 18, False),
            ("Total Amount: Rs. 21830.00", 22, True),
            ("", 10, False),
            ("Due Date: 06-07-2026", 18, False),
        ],
    },
    {
        "filename": "kyc_form_1.png",
        "lines": [
            ("CUSTOMER KYC / IDENTITY FORM", 26, True),
            ("", 10, False),
            ("Full Name: Priya Ramaswamy", 20, False),
            ("Date of Birth: 04-11-1994", 20, False),
            ("ID Number: KYC-778812", 20, False),
            ("Address: 12 Lake View Road, Madurai - 625002", 18, False),
            ("Phone: 9876543210", 18, False),
            ("", 10, False),
            ("Account Type: Savings", 18, False),
            ("Branch: Madurai Main", 18, False),
            ("Date of Application: 01-07-2026", 20, False),
        ],
    },
]

for doc in INVOICES:
    width, height = 750, 40 + 40 * len(doc["lines"])
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    y = 20
    for text, size, bold in doc["lines"]:
        font = get_font(size)
        draw.text((30, y), text, fill="black", font=font)
        y += size + 16
    path = os.path.join(OUT_DIR, doc["filename"])
    img.save(path)
    print(f"Saved {path}")

print("Done generating sample documents.")