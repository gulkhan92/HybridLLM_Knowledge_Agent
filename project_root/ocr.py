# ocr.py
import os
from pathlib import Path
from pdf2image import convert_from_path
import pytesseract
from tqdm import tqdm
from config import OCR_CHUNKS_FOLDER, SUPPORTED_EXTENSIONS

def ocr_pdf(pdf_path: str, output_folder: str = OCR_CHUNKS_FOLDER):
    """
    Perform OCR on a scanned PDF (including handwritten text if possible)
    and save each page as a separate text file.
    """
    pdf_name = Path(pdf_path).stem
    pdf_output_dir = Path(output_folder) / pdf_name
    pdf_output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Performing OCR on {pdf_name}...")
    
    # Convert PDF pages to images
    pages = convert_from_path(pdf_path, dpi=300)
    
    for i, page in enumerate(tqdm(pages, desc="Processing pages")):
        # OCR each page
        text = pytesseract.image_to_string(page, lang="eng")  # add lang='eng+...'
        text = text.strip()
        
        # Save page text
        chunk_file = pdf_output_dir / f"{pdf_name}_p{i+1}_c1.txt"
        with open(chunk_file, "w", encoding="utf-8") as f:
            f.write(text)
    
    print(f"OCR complete. Chunks saved to {pdf_output_dir}")
    return pdf_output_dir

def ocr_multiple_pdfs(pdf_paths: list):
    """
    Perform OCR on multiple PDFs
    """
    for pdf in pdf_paths:
        ext = Path(pdf).suffix.lower()
        if ext in SUPPORTED_EXTENSIONS:
            ocr_pdf(pdf)
        else:
            print(f"Skipping unsupported file {pdf}")
