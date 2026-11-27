import gc
import io
from typing import List, Dict, Any, Tuple, Optional
import fitz  # PyMuPDF
import pdfplumber
import pandas as pd
from app.services.ocr import perform_ocr_on_image
from app.core.logging import logger

def extract_pdf_pages_data(
    doc: fitz.Document,
    raw_bytes: bytes,
    password: Optional[str] = None
) -> Tuple[List[Dict[str, Any]], bool]:
    """
    Extracts text and table rows per page from an opened PyMuPDF Document.
    Falls back to OCR if avg chars per page < 200 or no text extracted.
    Returns: (pages_data, used_ocr)
    Each item in pages_data has {page_no, text, table_rows}
    """
    total_pages = len(doc)
    pages_data = []
    total_chars = 0
    used_ocr = False

    for page_idx in range(total_pages):
        page = doc[page_idx]
        text = page.get_text("text")
        total_chars += len(text.strip())

    avg_chars = total_chars / max(total_pages, 1)

    # If document has almost no extractable text, trigger OCR
    if total_chars < 50 or avg_chars < 150:
        logger.info(f"Scanned PDF detected (avg chars {avg_chars:.1f}). Running OCR...")
        used_ocr = True
        for page_idx in range(total_pages):
            page = doc[page_idx]
            pix = page.get_pixmap(dpi=150)
            img_bytes = pix.tobytes("png")
            del pix
            ocr_text = perform_ocr_on_image(img_bytes)
            del img_bytes
            gc.collect()
            # Reconstruct table rows from OCR line breaks
            lines = [line.strip().split() for line in ocr_text.split("\n") if line.strip()]
            pages_data.append({
                "page_no": page_idx + 1,
                "text": ocr_text,
                "table_rows": lines
            })
        return pages_data, used_ocr

    # Standard digital PDF text & table extraction via pdfplumber
    # Use decrypted bytes from doc so pdfplumber doesn't fail on encrypted PDFs
    try:
        try:
            decrypted_pdf_bytes = doc.tobytes()
        except Exception:
            decrypted_pdf_bytes = raw_bytes

        with pdfplumber.open(io.BytesIO(decrypted_pdf_bytes), password=password) as pdf:
            for page_idx, page in enumerate(pdf.pages):
                tables = page.extract_tables()
                page_text = page.extract_text() or ""
                combined_rows = []
                for table in tables:
                    for row in table:
                        if any(row):
                            cleaned_cells = [
                                str(cell).replace("\n", " ").strip() if cell is not None else ""
                                for cell in row
                            ]
                            combined_rows.append(cleaned_cells)

                # Fallback to PyMuPDF find_tables if pdfplumber found no tables
                if not combined_rows:
                    try:
                        fitz_page = doc[page_idx]
                        fitz_tables = fitz_page.find_tables()
                        if fitz_tables and fitz_tables.tables:
                            for ft in fitz_tables.tables:
                                extracted = ft.extract()
                                for r in extracted:
                                    if any(r):
                                        combined_rows.append([
                                            str(c).replace("\n", " ").strip() if c is not None else ""
                                            for c in r
                                        ])
                    except Exception:
                        pass

                if not combined_rows and page_text:
                    # Fallback line splitting if table borders aren't recognized
                    for line in page_text.split("\n"):
                        parts = [p.strip() for p in line.split("  ") if p.strip()]
                        if len(parts) >= 3:
                            combined_rows.append(parts)

                pages_data.append({
                    "page_no": page_idx + 1,
                    "text": page_text,
                    "table_rows": combined_rows
                })
    except Exception as e:
        logger.warning(f"pdfplumber error, falling back to PyMuPDF text & tables: {e}")
        for page_idx in range(total_pages):
            page = doc[page_idx]
            text = page.get_text("text")
            combined_rows = []
            try:
                fitz_tables = page.find_tables()
                if fitz_tables and fitz_tables.tables:
                    for ft in fitz_tables.tables:
                        for r in ft.extract():
                            if any(r):
                                combined_rows.append([
                                    str(c).replace("\n", " ").strip() if c is not None else ""
                                    for c in r
                                ])
            except Exception:
                pass
            if not combined_rows:
                combined_rows = [[w.strip() for w in line.split("  ") if w.strip()] for line in text.split("\n") if line.strip()]
            pages_data.append({
                "page_no": page_idx + 1,
                "text": text,
                "table_rows": combined_rows
            })

    return pages_data, used_ocr

def extract_excel_or_csv(file_bytes: bytes, file_name: str) -> List[Dict[str, Any]]:
    """
    Extracts tabular data from Excel (.xlsx, .xls) or CSV files.
    """
    ext = file_name.lower().split(".")[-1]
    if ext == "csv":
        df = pd.read_csv(io.BytesIO(file_bytes), dtype=str)
    else:
        df = pd.read_excel(io.BytesIO(file_bytes), dtype=str)

    # Convert to string table rows
    df = df.fillna("")
    headers = [str(col) for col in df.columns]
    rows = [headers] + df.values.tolist()

    return [{
        "page_no": 1,
        "text": " ".join(headers),
        "table_rows": rows
    }]
