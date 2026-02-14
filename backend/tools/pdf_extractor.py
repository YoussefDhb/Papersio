"""
PDF Extraction Tool
Downloads and extracts text and tables from ArXiv PDFs
"""

import os
import requests
import pdfplumber
from typing import Dict, List, Optional
import tempfile


def download_pdf(pdf_url: str, timeout: int = 30) -> Optional[str]:
    """
    Download a PDF from a URL to a temporary file

    Args:
        pdf_url: URL of the PDF
        timeout: Request timeout in seconds

    Returns:
        Path to downloaded PDF file, or None if failed
    """
    try:
        response = requests.get(pdf_url, timeout=timeout, stream=True)
        response.raise_for_status()

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        temp_file.write(response.content)
        temp_file.close()

        return temp_file.name

    except Exception as e:
        print(f"Error downloading PDF from {pdf_url}: {e}")
        return None


def extract_text_from_pdf(pdf_path: str, max_pages: Optional[int] = None) -> Dict:
    """
    Extract text from all pages of a PDF

    Args:
        pdf_path: Path to PDF file
        max_pages: Maximum number of pages to extract (None = all)

    Returns:
        Dict with:
        - full_text: All text concatenated
        - pages: List of text per page
        - num_pages: Total number of pages
        - success: Whether extraction succeeded
    """
    try:
        full_text = []
        pages_text = []

        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            pages_to_extract = min(total_pages, max_pages) if max_pages else total_pages

            for i, page in enumerate(pdf.pages[:pages_to_extract]):
                text = page.extract_text()
                if text:
                    pages_text.append(text)
                    full_text.append(text)

            return {
                "success": True,
                "full_text": "\n\n".join(full_text),
                "pages": pages_text,
                "num_pages": total_pages,
                "extracted_pages": pages_to_extract,
            }

    except Exception as e:
        print(f"Error extracting text from PDF {pdf_path}: {e}")
        return {"success": False, "error": str(e), "full_text": "", "pages": [], "num_pages": 0}


def extract_tables_from_pdf(pdf_path: str, max_pages: Optional[int] = None) -> Dict:
    """
    Extract tables from a PDF

    Args:
        pdf_path: Path to PDF file
        max_pages: Maximum number of pages to process

    Returns:
        Dict with:
        - tables: List of extracted tables (each table is a list of rows)
        - num_tables: Number of tables found
        - success: Whether extraction succeeded
    """
    try:
        all_tables = []

        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            pages_to_extract = min(total_pages, max_pages) if max_pages else total_pages

            for i, page in enumerate(pdf.pages[:pages_to_extract]):
                tables = page.extract_tables()

                for table in tables:
                    if table and len(table) > 0:
                        formatted_table = {"page": i + 1, "data": table, "markdown": _format_table_as_markdown(table)}
                        all_tables.append(formatted_table)

            return {"success": True, "tables": all_tables, "num_tables": len(all_tables)}

    except Exception as e:
        print(f"Error extracting tables from PDF {pdf_path}: {e}")
        return {"success": False, "error": str(e), "tables": [], "num_tables": 0}


def _format_table_as_markdown(table: List[List[str]]) -> str:
    """
    Format a table as markdown

    Args:
        table: List of rows, each row is a list of cells

    Returns:
        Markdown formatted table string
    """
    if not table or len(table) == 0:
        return ""

    md_lines = []

    header = table[0]
    md_lines.append("| " + " | ".join(str(cell) if cell else "" for cell in header) + " |")

    md_lines.append("| " + " | ".join("---" for _ in header) + " |")

    for row in table[1:]:
        md_lines.append("| " + " | ".join(str(cell) if cell else "" for cell in row) + " |")

    return "\n".join(md_lines)


def extract_paper_content(pdf_url: str, max_pages: int = 50) -> Dict:
    """
    Complete extraction: download PDF and extract text + tables

    Args:
        pdf_url: URL to the PDF
        max_pages: Maximum pages to process (to avoid huge papers)

    Returns:
        Dict with all extracted content
    """
    print(f"Downloading PDF: {pdf_url}")

    pdf_path = download_pdf(pdf_url)
    if not pdf_path:
        return {"success": False, "error": "Failed to download PDF"}

    try:
        print(f"Extracting text...")
        text_result = extract_text_from_pdf(pdf_path, max_pages=max_pages)

        print(f"Extracting tables...")
        tables_result = extract_tables_from_pdf(pdf_path, max_pages=max_pages)

        os.unlink(pdf_path)

        return {
            "success": text_result["success"] and tables_result["success"],
            "full_text": text_result.get("full_text", ""),
            "pages": text_result.get("pages", []),
            "num_pages": text_result.get("num_pages", 0),
            "tables": tables_result.get("tables", []),
            "num_tables": tables_result.get("num_tables", 0),
        }

    except Exception as e:
        if os.path.exists(pdf_path):
            os.unlink(pdf_path)

        return {"success": False, "error": str(e)}


def format_paper_for_ai(text: str, tables: List[Dict], max_text_length: int = 10000) -> str:
    """
    Format extracted paper content for AI consumption

    Args:
        text: Full text from paper
        tables: List of extracted tables
        max_text_length: Maximum length of text to include

    Returns:
        Formatted string for AI
    """
    if len(text) > max_text_length:
        text = text[:max_text_length] + "\n\n[... text truncated due to length ...]"

    formatted = f"PAPER CONTENT:\n\n{text}\n\n"

    if tables and len(tables) > 0:
        formatted += "TABLES:\n\n"
        for i, table in enumerate(tables, 1):
            formatted += f"Table {i} (Page {table['page']}):\n"
            formatted += table["markdown"]
            formatted += "\n\n"

    return formatted
