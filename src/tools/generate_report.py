from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch


def generate_report(path: str = "report.pdf"):
    c = canvas.Canvas(path, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 16)
    c.drawString(1 * inch, height - 1 * inch, "PrimeTrade Bot Report")

    c.setFont("Helvetica", 12)
    lines = [
        "This report summarizes the CLI Binance USDT-M Futures bot.",
        "",
        "Contents:",
        "- Screenshots of successful MARKET and LIMIT orders (add later).",
        "- Log excerpts showing requests and responses.",
        "- Validation strategy using exchangeInfo filters.",
        "- TWAP demonstration and parameters.",
        "- Future work: Grid and OCO order strategies.",
        "",
        "Refer to README.md for setup, usage, and design notes.",
    ]

    y = height - 1.4 * inch
    for line in lines:
        c.drawString(1 * inch, y, line)
        y -= 0.25 * inch

    c.showPage()
    c.save()


if __name__ == "__main__":
    generate_report()