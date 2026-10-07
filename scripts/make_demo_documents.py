"""Generate transparent text/PDF/CSV fixtures using the current demo window."""

import csv
from pathlib import Path
from datetime import timedelta
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from data.seed.network import tomorrow

ROOT = Path(__file__).resolve().parent.parent


def text_pdf(lines):
    content = "BT /F1 12 Tf 50 780 Td 18 TL\n"
    for line in lines:
        safe = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        content += f"({safe}) Tj T*\n"
    content += "ET"
    stream = content.encode("ascii")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length "
        + str(len(stream)).encode()
        + b" >>\nstream\n"
        + stream
        + b"\nendstream",
    ]
    output = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, 1):
        offsets.append(len(output))
        output.extend(f"{index} 0 obj\n".encode() + obj + b"\nendobj\n")
    xref = len(output)
    output.extend(f"xref\n0 {len(offsets)}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode())
    output.extend(
        f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    )
    return bytes(output)


def generate():
    target = ROOT / "data/demo"
    target.mkdir(parents=True, exist_ok=True)
    start = tomorrow()
    lines = [
        "JALAYATRA AI - SYNTHETIC PURCHASE ORDER",
        "Not a commercial or government document.",
        "Cargo: 80 tonnes cement, bagged, volume 60 m3.",
        "From Kalamassery to Alappuzha.",
        f"Ready {start.strftime('%Y-%m-%d %H:%M')}; deliver by {(start + timedelta(hours=14)).strftime('%Y-%m-%d %H:%M')}.",
        "Non-hazardous. Operator/shipper must review every field.",
    ]
    (target / "sample_purchase_order.pdf").write_bytes(text_pdf(lines))
    (target / "sample_purchase_order.txt").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    from PIL import Image, ImageDraw, ImageFont
    from intelligence.document_intake.spreadsheets import template_bytes
    import textwrap

    image = Image.new("RGB", (1800, 1700), "white")
    try:
        font = ImageFont.truetype("arial.ttf", 36)
    except OSError:
        font = ImageFont.truetype("DejaVuSans.ttf", 36)
    draw = ImageDraw.Draw(image)
    scan_lines = [
        *lines[:2],
        "Company: Kerala Demo Builders",
        "Reference: PO-SCAN-001",
        *lines[2:],
    ]
    wrapped = [part for line in scan_lines for part in textwrap.wrap(line, width=78)]
    for index, line in enumerate(wrapped):
        draw.text((65, 65 + index * 90), line, fill="black", font=font)
    image.save(target / "scanned_purchase_order.png")
    image.save(target / "scanned_purchase_order.pdf", "PDF", resolution=150)
    (target / "cargo_bulk.xlsx").write_bytes(template_bytes())
    with (target / "cargo_bulk.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = [
            "cargo_type",
            "weight_tonnes",
            "volume_m3",
            "packaging",
            "origin",
            "destination",
            "ready_time",
            "delivery_deadline",
            "first_mile_required",
            "last_mile_required",
            "consolidation_allowed",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for category, weight, volume, packaging, origin, first in [
            ("cement", 80, 60, "bagged", "Kalamassery", True),
            ("steel", 58, 48, "bundled", "Maradu", False),
        ]:
            writer.writerow(
                dict(
                    cargo_type=category,
                    weight_tonnes=weight,
                    volume_m3=volume,
                    packaging=packaging,
                    origin=origin,
                    destination="Alappuzha",
                    ready_time=start.isoformat(),
                    delivery_deadline=(start + timedelta(hours=14)).isoformat(),
                    first_mile_required=first,
                    last_mile_required=False,
                    consolidation_allowed=True,
                )
            )
    print(
        "Synthetic text PDF, scanned PDF/PNG, TXT, CSV and XLSX examples generated in data/demo."
    )


if __name__ == "__main__":
    generate()
