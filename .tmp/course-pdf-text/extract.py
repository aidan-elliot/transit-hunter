from pathlib import Path

from pypdf import PdfReader


FILES = [
    Path(r"C:\Users\aidan\Downloads\PHY 4000_Learners Manual - Summer 2026 V0.pdf"),
    Path(r"C:\Users\aidan\Downloads\04_ Week 4_Light and Matter-Reading Messages from the Cosmos.pdf"),
    Path(r"C:\Users\aidan\Downloads\10_ Week 10_Exo Planets EXTRA.pdf"),
    Path(r"C:\Users\aidan\Downloads\06_ Week 6_Telescopes - Portals of Discovery.pdf"),
    Path(r"C:\Users\aidan\Downloads\13_ Week 13_Life in the Universe.pdf"),
]

output_dir = Path(r"C:\Github\transit-hunter\.tmp\course-pdf-text")

for source in FILES:
    reader = PdfReader(source)
    output = [f"SOURCE: {source}", f"PAGES: {len(reader.pages)}", ""]
    nonempty = 0
    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if text.strip():
            nonempty += 1
        output.extend([f"===== PAGE {page_number} =====", text, ""])
    destination = output_dir / f"{source.stem}.txt"
    destination.write_text("\n".join(output), encoding="utf-8")
    print(f"{source.name}: {len(reader.pages)} pages, {nonempty} pages with extracted text")
