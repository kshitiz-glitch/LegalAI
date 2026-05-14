import pdfplumber
import fitz
from io import BytesIO
from typing import Tuple


class PDFParser:
    def extract_text(self, content: bytes) -> Tuple[str, int]:
        text = self._pdfplumber_extract(content)

        if len(text.strip()) < 100:
            text = self._pymupdf_extract(content)

        doc = fitz.open(stream=content, filetype="pdf")
        page_count = len(doc)
        doc.close()

        return text.strip(), page_count

    def _pdfplumber_extract(self, content: bytes) -> str:
        try:
            with pdfplumber.open(BytesIO(content)) as pdf:
                pages = []
                for page in pdf.pages:
                    t = page.extract_text(x_tolerance=3, y_tolerance=3)
                    if t:
                        pages.append(t)
                return "\n\n".join(pages)
        except Exception:
            return ""

    def _pymupdf_extract(self, content: bytes) -> str:
        try:
            doc = fitz.open(stream=content, filetype="pdf")
            pages = [page.get_text() for page in doc]
            doc.close()
            return "\n\n".join(pages)
        except Exception:
            return ""
