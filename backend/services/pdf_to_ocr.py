import re
import pytesseract
from pdf2image import convert_from_path

pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"
class PDFtoOCR:
    def __init__(self, tesseract_path=None):
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

    def pdf_to_images(self, pdf_path, dpi=300):
        return convert_from_path(pdf_path, dpi=dpi)

    def image_to_text(self, image):
        return pytesseract.image_to_string(image)

    def pdf_to_text(self, pdf_path):
        images = self.pdf_to_images(pdf_path)
        full_text = ""

        for i, img in enumerate(images):
            text = self.image_to_text(img)
            full_text += f"\n--- Page {i+1} ---\n{text}\n"

        return full_text

    # NEW: text → clauses JSON
    def text_to_json(self, text):
        # split into clauses (basic but effective)
        raw_clauses = re.split(r"\n{2,}", text)

        clauses = []
        for i, c in enumerate(raw_clauses):
            c = c.strip()
            if len(c) < 30:  # ignore noise
                continue

            clauses.append({
                "clause_id": i,
                "clause_text": c
            })

        return clauses

    # FINAL: PDF → JSON
    def pdf_to_json(self, pdf_path):
        text = self.pdf_to_text(pdf_path)
        return self.text_to_json(text)