import os
import re
import pytesseract
from pdf2image import convert_from_path


class PDFtoOCR:
    def __init__(self, tesseract_path=None, poppler_path=None):
        self.poppler_path = poppler_path or os.getenv("POPLLER_PATH")
        resolved_tesseract = tesseract_path or os.getenv("TESSERACT_CMD")
        if resolved_tesseract:
            pytesseract.pytesseract.tesseract_cmd = resolved_tesseract

        # Performance knobs (same flow, configurable via backend/.env)
        self.dpi = int(os.getenv("OCR_DPI", "220"))
        self.thread_count = int(os.getenv("OCR_THREADS", str(max(1, (os.cpu_count() or 2) - 1))))
        self.lang = os.getenv("OCR_LANG", "eng")
        self.psm = int(os.getenv("OCR_PSM", "6"))
        self.oem = int(os.getenv("OCR_OEM", "1"))

    def pdf_to_images(self, pdf_path, dpi=None):
        use_dpi = int(dpi or self.dpi)
        return convert_from_path(
            pdf_path,
            dpi=use_dpi,
            poppler_path=self.poppler_path,
            thread_count=self.thread_count,
            grayscale=True,
        )

    def image_to_text(self, image):
        # PSM 6 is a good default for dense legal text blocks.
        config = f"--oem {self.oem} --psm {self.psm}"
        return pytesseract.image_to_string(image, lang=self.lang, config=config)

    def pdf_to_text(self, pdf_path):
        images = self.pdf_to_images(pdf_path)
        chunks = []

        for i, img in enumerate(images):
            text = self.image_to_text(img)
            chunks.append(f"\n--- Page {i+1} ---\n{text}\n")

        return "".join(chunks)

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