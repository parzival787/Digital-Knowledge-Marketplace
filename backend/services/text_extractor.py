import io
import pdfplumber


def extract_text(file_bytes: bytes, filename: str) -> str:
    name = filename.lower()

    if name.endswith(".pdf"):
        return _extract_from_pdf(file_bytes)

    elif name.endswith(".csv"):
        return _extract_from_csv(file_bytes)

    elif name.endswith((".txt", ".md", ".json", ".xml")):
        return _extract_from_text(file_bytes)

    else:
        # Best effort for unknown file types
        return file_bytes.decode("utf-8", errors="ignore")[:4000]


def _extract_from_pdf(data: bytes) -> str:
    """
    Read up to the first 5 pages of a PDF.
    """
    text = ""

    try:
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            for page in pdf.pages[:5]:
                page_text = page.extract_text()

                if page_text:
                    text += page_text + "\n"

                if len(text) >= 4000:
                    break

    except Exception:
        # Never assess extraction errors as if they were document content.
        return ""

    return text[:4000]


def _extract_from_csv(data: bytes) -> str:
    """
    Return the header row plus the first 50 data rows.
    """
    try:
        lines = data.decode("utf-8", errors="ignore").split("\n")
        sample = "\n".join(lines[:51])
        return sample[:4000]

    except Exception:
        return data.decode("utf-8", errors="ignore")[:4000]


def _extract_from_text(data: bytes) -> str:
    """
    Read plain text files.
    """
    return data.decode("utf-8", errors="ignore")[:4000]
