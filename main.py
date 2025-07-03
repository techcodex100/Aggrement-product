import os
from io import BytesIO
from fastapi import FastAPI, Response
from pydantic import BaseModel
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import threading

app = FastAPI()
lock = threading.Lock()
COUNTER_FILE = "counter.txt"

# ✅ Input Model
class SalesContractData(BaseModel):
    contract_no: str
    date: str
    company_name: str
    tagline: str
    website: str
    email: str
    address: str
    gst_number: str
    seller: list[str]
    consignee: list[str]
    notify_party: list[str] = []
    product_name: str
    quantity: str
    price: str
    amount: str
    packing: str
    loading_port: str
    destination_port: str
    shipment: str
    sellers_bank: str
    account_no: str
    documents: str
    payment_terms: str

# ✅ Counter Logic
def get_next_counter():
    with lock:
        if not os.path.exists(COUNTER_FILE):
            with open(COUNTER_FILE, "w") as f:
                f.write("1")
            return 1
        with open(COUNTER_FILE, "r+") as f:
            count = int(f.read())
            f.seek(0)
            f.write(str(count + 1))
            f.truncate()
            return count

# ✅ PDF Generation
@app.post("/generate-pdf/")
async def generate_pdf(data: SalesContractData):
    pdf_number = get_next_counter()
    filename = f"Sales_Contract_{pdf_number}.pdf"
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    styles = getSampleStyleSheet()
    normal_style = styles["Normal"]

    # Margins
    left_margin = 50
    right_margin = width - 50
    top_margin = height - 40

    # 🔷 Header
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(colors.grey)
    c.drawString(left_margin, top_margin, f"Website: {data.website}")
    c.setFont("Helvetica-Bold", 16)
    c.setFillColor(colors.black)
    c.drawCentredString(width / 2, top_margin, data.company_name.upper())
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(colors.grey)
    c.drawRightString(right_margin, top_margin, f"Email: {data.email}")

    c.setFont("Helvetica", 11)
    c.setFillColor(colors.black)
    c.drawCentredString(width / 2, top_margin - 20, data.tagline)

    c.setFont("Helvetica", 10)
    c.drawString(left_margin, top_margin - 40, f"Address: {data.address}")
    c.drawRightString(right_margin, top_margin - 40, f"GST: {data.gst_number}")

    # 🔷 Title & Contract Info
    start_y = top_margin - 80
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width / 2, start_y, "SALES CONTRACT")
    c.setFont("Helvetica", 11)
    c.drawString(left_margin, start_y - 20, f"Contract No: {data.contract_no}")
    c.drawRightString(right_margin, start_y - 20, f"Date: {data.date}")

    # 🔷 Seller / Consignee / Notify Party (Columns)
    y = start_y - 60
    block_width = (width - 100) / 3
    x_positions = [50, 50 + block_width + 10, 50 + 2 * (block_width + 10)]

    titles = ["SELLER",  "CONSIGNEE | NOTIFY PARTY 1",   "NOTIFY PARTY 2"]
    blocks = [
        "\n".join(data.seller),
        "\n".join(data.consignee),
        "\n".join(data.notify_party) if data.notify_party else "TO ORDER"
    ]

    c.setFont("Helvetica-Bold", 10)
    for i in range(3):
        c.drawString(x_positions[i], y, titles[i])
        c.setFont("Helvetica-Bold", 10)
        text_obj = c.beginText(x_positions[i], y - 14)
        for line in blocks[i].split("\n"):
            text_obj.textLine(line.strip())
        c.drawText(text_obj)

    y = y - 100  # Space below notify party

    # 🔷 Product Table with wrapped text
    from reportlab.platypus import SimpleDocTemplate, Table
    from reportlab.platypus import Frame

    # Prepare wrapped cells using Paragraph
    table_data = [
        ["Product", "Quantity", "Price (CIF), Colombo", "Amount(CIF)"],
        [
            Paragraph(data.product_name, normal_style),
            Paragraph(data.quantity, normal_style),
            Paragraph(data.price, normal_style),
            Paragraph(data.amount, normal_style)
        ]
    ]

    table = Table(table_data, colWidths=[130, 130, 130, 100])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ]))

    frame = Frame(left_margin, y - 100, width - 2 * left_margin, 100, showBoundary=0)
    frame.addFromList([table], c)
    y = y - 90

    # 🔷 Dynamic Fields
    dynamic_details = [
        ("Packing", data.packing),
        ("Loading Port", data.loading_port),
        ("Destination Port", data.destination_port),
        ("Shipment", data.shipment),
        ("Seller’s Bank", data.sellers_bank),
        ("Account No.", data.account_no),
        ("Documents", data.documents),
        ("Payment Terms", data.payment_terms)
    ]
    for label, value in dynamic_details:
        c.setFont("Helvetica-Bold", 10)
        c.drawString(left_margin, y, f"{label}:")
        c.setFont("Helvetica", 10)
        for line in str(value).split("\n"):
            c.drawString(left_margin + 120, y, line.strip())
            y -= 18
        y -= 8

    # 🔷 Static Details
    static_details = [
        ("Arbitration", [
            "In the event of any dispute between the parties arising out of this contract,",
            "all disputes shall be settled by the way of arbitration through a sole arbitration",
            "to be appointed by M/S Shraddha Impex. The place of arbitration shall be in Indore, M.P.",
            "and the laws of India with regards to arbitration shall be applicable to this Arbitration Clause."
        ]),
        ("Terms & Conditions", [
            "1) In case of port congestion/skippance of vessel or any other port related disturbances,",
            "supplier or exporter will not be liable for any claim.",
            "2) Quality approved at load port by independent surveyors is finaland to be acceptable by both,",
            " the parties and the seller will not be liable for any claim at destination port."
        ])
    ]
    for label, lines in static_details:
        c.setFont("Helvetica-Bold", 10)
        c.drawString(left_margin, y, f"{label}:")
        c.setFont("Helvetica", 10)
        for line in lines:
            c.drawString(left_margin + 120, y, line.strip())
            y -= 14
        y -= 8

    # 🔷 Acceptance Block
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(width / 2, y, "Accepted")
    y -= 20
    c.setFont("Helvetica", 10)
    c.drawString(50, y, "For, Seller")
    c.drawString(230, y, "For, Consignee")
    c.drawString(400, y, "For, Notify Party")
    y -= 50
    c.drawString(50, y, data.seller[0] if data.seller else "")
    c.drawString(230, y, data.consignee[0] if data.consignee else "")
    c.drawString(400, y, (data.notify_party[0] if data.notify_party else "TO ORDER"))

    # ✅ Save
    c.save()
    buffer.seek(0)
    return Response(content=buffer.read(), media_type="application/pdf", headers={
        "Content-Disposition": f"attachment; filename={filename}"
    })

@app.get("/")
def home():
    return {"message": "Your Render App is Working!"}
