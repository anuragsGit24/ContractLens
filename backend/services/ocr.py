import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import os

class PDFtoOCR:
    def __init__(self, tesseract_path=None):
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path

    def pdf_to_images(self, pdf_path, dpi=300):
        images = convert_from_path(
            pdf_path,
            dpi=dpi,
            poppler_path=r"C:\poppler\poppler-25.12.0\Library\bin"
        )
        return images

    def image_to_text(self, image):
        text = pytesseract.image_to_string(image)
        return text

    def pdf_to_text(self, pdf_path):
        images = self.pdf_to_images(pdf_path)
        full_text = ""

        for i, img in enumerate(images):
            text = self.image_to_text(img)
            full_text += f"\n--- Page {i+1} ---\n"
            full_text += text

        return full_text


if __name__ == "__main__":
    pdf_path = input("Enter PDF file path: ")

    ocr = PDFtoOCR(
        tesseract_path=r"C:\Program Files\Tesseract-OCR\tesseract.exe"  # Change if needed
    )

    text = ocr.pdf_to_text(pdf_path)

    output_file = "output.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"OCR extraction complete. Saved to {output_file}")