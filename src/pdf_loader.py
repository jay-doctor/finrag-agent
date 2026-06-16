import os
import json
import pdfplumber
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
from pdf2image import convert_from_path
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

def extract_pdf_text(pdf_path):
    """Extract text with fallback to OCR for scanned pages."""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = "\n".join([page.extract_text() or "" for page in pdf.pages])
        if text.strip():
            return text
    except:
        pass
    # OCR fallback
    images = convert_from_path(pdf_path, dpi=200)
    text = ""
    for img in images:
        text += pytesseract.image_to_string(img, lang='deu+eng') + "\n"
    return text

def detect_company_from_text(text, filename):
    text_lower = text[:2000].lower()
    if "bmw" in text_lower or "BMW" in filename:
        return "BMW"
    elif "mercedes" in text_lower or "daimler" in text_lower or "Mercedes" in filename:
        return "Mercedes"
    elif "volkswagen" in text_lower or "vw" in text_lower or "VW" in filename:
        return "Volkswagen"
    return "Unknown"

def load_pdfs(folder):
    docs = []
    for file in os.listdir(folder):
        if not file.endswith(".pdf"):
            continue
        path = os.path.join(folder, file)
        raw_text = extract_pdf_text(path)
        company = detect_company_from_text(raw_text, file)
        report_type = "Full Year 2025" if "FY" in file or "annual" in file.lower() else "Quarterly 2025"
        
        # 🔥 UPDATED: Smaller chunks for focused retrieval
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=3000,      # reduced from 5000
            chunk_overlap=300,    # reduced from 500
            separators=["\n\n", "\n", " "]
        )
        chunks = splitter.split_text(raw_text)
        
        for chunk in chunks:
            doc = Document(page_content=chunk, metadata={
                "company": company,
                "report_type": report_type,
                "source": file
            })
            docs.append(doc)
    return docs