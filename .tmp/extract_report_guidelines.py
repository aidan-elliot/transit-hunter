from pathlib import Path
from pypdf import PdfReader

paths = [
    Path(r"C:\Users\aidan\Downloads\PHY 4000_Learners Manual - Summer 2026 V0.pdf"),
    Path(r"C:\Users\aidan\OneDrive\Documents\ChatGPT\Final Project - PHY4000\Proposal_Assignment-1.pdf"),
]

terms = (
    "final project", "submission", "submit", "format", "page number",
    "reference", "source", "written work", "identifying", "filename",
    "proofread", "brightspace", "explanatory statement", "artificial intelligence",
    "generative ai", "chatgpt", "plagiarism",
)

for path in paths:
    print(f"\n===== {path.name} =====")
    reader = PdfReader(str(path))
    for number, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").replace("\u00a0", " ")
        lowered = text.lower()
        if any(term in lowered for term in terms):
            print(f"\n--- PDF page {number} ---")
            print(text)
