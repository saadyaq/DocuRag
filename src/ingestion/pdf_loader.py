import logging
from typing import Dict

import fitz
from pathlib import Path

logger= logging.getLogger(__name__)

class PDFLoader:
    def __init__(self, file_path: Path):
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found at {self.file_path}")
        if self.file_path.suffix.lower() != ".pdf":
            raise ValueError(f"Not a PDF file: {self.file_path}")


    def load(self) -> list[Dict]:

        pages = []
        try:
            doc = fitz.open(self.file_path)
        except Exception as e :
            logger.error(f"Error opening file: {self.file_path}")
            raise ValueError(f"Error opening file: {self.file_path}")

        for page_num in range(len(doc)):
            page=doc[page_num]
            text=page.get_text()

            if text.strip():
                pages.append({

                    "text":text,
                    "page_number": page_num,
                    "source": str(self.file_path.resolve())
                })
        doc.close()

        if not pages :
            logger.warning(f"No pages found in {self.file_path}")
        logger.info(f"Found {len(pages)} pages in {self.file_path}")
        return pages