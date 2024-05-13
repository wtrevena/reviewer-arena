import fitz
import os
import logging
import random 
from models import Paper, PaperProcessor

def extract_text_from_pdf(filename):
    with fitz.open(filename) as pdf_document:
        text = ""
        for page in pdf_document:
            text += page.get_text()
    return text.encode('latin-1', 'replace').decode('latin-1')

def process_paper(pdf_file, paper_dir, prompt_dir, api_keys):
    logging.info(f"Processing file type in process_paper: {type(pdf_file)}")  # Log the type of the file here as well
    logging.debug(f"Starting to process paper: {pdf_file}")
    # Ensure the directory exists
    os.makedirs(paper_dir, exist_ok=True)

    # Handle file based on its type
    if isinstance(pdf_file, str):
        # Assume pdf_file is a path to the PDF file
        pdf_path = pdf_file
    elif hasattr(pdf_file, 'name') and hasattr(pdf_file, 'read'):
        # It's a file-like object
        pdf_path = os.path.join(paper_dir, pdf_file.name)
        with open(pdf_path, "wb") as f:
            f.write(pdf_file.read())
    else:
        logging.error("Received object is neither a path nor a file-like object.")
        return []

    # Extract text from the PDF
    extracted_text = extract_text_from_pdf(pdf_path)
    paper = Paper(pdf_file.name if hasattr(pdf_file, 'name') else os.path.basename(pdf_path), extracted_text)

    # Randomly select two models
    models = ['gpt', 'claude', 'gemini', 'commandr']
    selected_models = random.sample(models, 2)

    # Process the paper with each selected model
    reviews = []
    for model in selected_models:
        processor = PaperProcessor(prompt_dir, model, **api_keys)
        review_text = processor.process_paper(paper)
        #review_dict = {section.split(':')[0]: section.split(':')[1].strip() for section in review_text}
        reviews.append(review_text)
    logging.debug(f"Reviews generated: {reviews}")
    return reviews