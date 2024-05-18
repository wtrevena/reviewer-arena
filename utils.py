import fitz
import os
import logging
import random
from models import Paper, PaperProcessor
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor

def extract_text_from_pdf(filename):
    with fitz.open(filename) as pdf_document:
        text = ""
        for page in pdf_document:
            text += page.get_text()
    return text.encode('latin-1', 'replace').decode('latin-1')


def process_paper(pdf_file, paper_dir, prompt_dir, api_keys):
    logging.info(f"Processing file type in process_paper: {type(pdf_file)}")
    logging.debug(f"Starting to process paper: {pdf_file}")
    os.makedirs(paper_dir, exist_ok=True)

    if isinstance(pdf_file, str):
        pdf_path = pdf_file
    elif hasattr(pdf_file, 'name') and hasattr(pdf_file, 'read'):
        pdf_path = os.path.join(paper_dir, pdf_file.name)
        with open(pdf_path, "wb") as f:
            f.write(pdf_file.read())
    else:
        logging.error(
            "Received object is neither a path nor a file-like object.")
        return [], []

    extracted_text = extract_text_from_pdf(pdf_path)
    paper = Paper(pdf_file.name if hasattr(pdf_file, 'name')
                  else os.path.basename(pdf_path), extracted_text)

    models = ['gpt-4-turbo-2024-04-09', 'gpt-4o', 'claude-3-opus-20240229', 'gemini-pro', 'command-r-plus']
    selected_models = random.sample(models, 2)

    # REPLACE ONE OF THE MODELS WITH command-r-plus
    # selected_models = ['gpt-4o', 'command-r-plus']

    reviews = []

    def process_with_model(model):
        processor = PaperProcessor(prompt_dir, model, **api_keys)
        return processor.process_paper(paper)

    with ThreadPoolExecutor() as executor:
        future_to_model = {executor.submit(process_with_model, model): model for model in selected_models}
        for future in concurrent.futures.as_completed(future_to_model):
            model = future_to_model[future]
            try:
                review_text = future.result()
                reviews.append(review_text)
            except Exception as exc:
                logging.error(f"Model {model} generated an exception: {exc}")

    logging.debug(f"Reviews generated: {reviews}")
    return reviews, selected_models
