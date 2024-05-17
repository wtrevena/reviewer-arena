import gradio as gr
from utils import process_paper
import os
import logging
import html
from logging_config import setup_logging
from aws_utils import update_leaderboard, get_leaderboard, write_request
from flask import request
import hashlib
import uuid

setup_logging()
paper_dir = 'path_to_temp_storage'
prompt_dir = 'iclr2024'
api_keys = {
    'openai_api_key': os.environ.get('openai_api_key'),
    'claude_api_key': os.environ.get('anthropic_api_key'),
    'gemini_api_key': os.environ.get('google_api_key'),
    'commandr_api_key': os.environ.get('cohere_api_key')
}

use_real_api = False

# Function to generate a paper_id using SHA-512 hash
def generate_paper_id(paper_content):
    return hashlib.sha512(paper_content).hexdigest()

# Function to get user IP address
def get_user_ip():
    return request.remote_addr

def review_papers(pdf_file):
    logging.info(f"Received file type: {type(pdf_file)}")
    paper_content = pdf_file.read()  # Read the content of the uploaded PDF file
    if use_real_api:
        reviews, selected_models = process_paper(
            pdf_file, paper_dir, prompt_dir, api_keys)
        processed_reviews = []
        for review in reviews:
            processed_review = {}
            for section in review:
                if ':' in section:
                    key, value = section.split(':', 1)
                    processed_value = value.strip().replace('\n', '<br>')
                    processed_review[key.strip()] = html.escape(
                        processed_value)
            processed_reviews.append(processed_review)
        reviews = processed_reviews
    else:
        reviews = [
            # Placeholder reviews
        ]
        selected_models = ['model1-placeholder', 'model2-placeholder']

    review_texts = []
    for review in reviews:
        formatted_review = "<div class='review-container'>"
        for section, content in review.items():
            formatted_review += f"<div class='review-section'><strong>{section}:</strong> <span>{html.unescape(content)}</span></div>"
        formatted_review += "</div>"
        review_texts.append(formatted_review)

    model_a = selected_models[0]
    model_b = selected_models[1]

    logging.debug(f"Final formatted reviews: {review_texts}")
    return review_texts[0], review_texts[1], gr.update(visible=True), gr.update(visible=True), model_a, model_b, paper_content

def handle_vote(vote, model_a, model_b, paper_content):
    user_id = get_user_ip()  # Get the user IP address as user_id
    paper_id = generate_paper_id(paper_content)  # Generate paper_id from paper content
    
    # Write the request
    write_request(user_id, paper_id, model_a, model_b, vote)
    
    # Update the leaderboard
    update_leaderboard(model_a, model_b, vote)
    
    # Fetch the updated leaderboard (optional, if you want to display it immediately)
    leaderboard = get_leaderboard()
    
    message = f"<p>Thank you for your vote!</p><p>Model A: {model_a}</p><p>Model B: {model_b}</p>"
    return gr.update(value=message, visible=True), gr.update(visible=False), gr.update(visible=False), gr.update(visible=True)


def setup_interface():
    logging.debug("Setting up Gradio interface.")
    css = """
    .review-container {
        padding: 10px;
        margin-bottom: 20px;
        border: 1px solid #ccc;
        background-color: #f9f9f9;
    }
    .review-section {
        margin-bottom: 12px;
        padding: 8px;
        background-color: #ffffff;
        border-left: 4px solid #007BFF;
        padding-left: 10px;
    }
    .review-section strong {
        color: #333;
        font-weight: bold;
        display: block;
        margin-bottom: 5px;
    }
    .review-section span, .gr-markdown {
        color: #000;
        font-size: 14px;
        line-height: 1.5;
        display: block;
        white-space: normal;
        opacity: 1;
    }
    .model-label {
        font-size: 18px;
        font-weight: bold;
        color: #007BFF;
        margin-bottom: 10px;
    }
    .gr-file, .gr-button, .gr-radio {
        width: 300px;
        margin: auto;
    }
    .gr-button-small {
        width: 150px;
        height: 40px;
        font-size: 16px;
    }
    """
    with gr.Blocks(css=css) as demo:
        with gr.Tabs():
            with gr.TabItem("Reviewer Arena"):
                gr.Markdown("## Reviewer Arena")
                gr.Markdown("Upload an academic paper to get reviews from two randomly selected LLMs.")
                with gr.Row():
                    file_input = gr.File(label="Upload Academic Paper")
                    submit_button = gr.Button("Submit!", elem_id="submit-button")
                with gr.Row():
                    with gr.Column():
                        gr.HTML("<div class='model-label'>Model A</div>")
                        review1 = gr.Markdown()
                    with gr.Column():
                        gr.HTML("<div class='model-label'>Model B</div>")
                        review2 = gr.Markdown()

                vote_options = ["👍 A is better", "👍 B is better", "👔 Tie", "👎 Both are bad"]
                vote = gr.Radio(label="Vote on the best model", choices=vote_options, value="Tie", visible=False)
                vote_button = gr.Button("Submit Vote", visible=False)
                vote_message = gr.HTML("", visible=False)
                another_paper_button = gr.Button("Review another paper", visible=False)

                model_identity_message = gr.HTML("", visible=False)

                def handle_vote_interface(vote, model_identity_message_a, model_identity_message_b, paper_content):
                    return handle_vote(vote, model_identity_message_a, model_identity_message_b, paper_content)

                submit_button.click(fn=review_papers, inputs=[file_input],
                                    outputs=[review1, review2, vote, vote_button, model_identity_message, model_identity_message])

                vote_button.click(fn=handle_vote_interface, inputs=[vote, model_identity_message, model_identity_message],
                                  outputs=[vote_message, vote, vote_button, another_paper_button])

                another_paper_button.click(fn=lambda: None, inputs=None, outputs=None, js="() => { location.reload(); }")

            with gr.TabItem("Leaderboard"):
                gr.Markdown("## Leaderboard")
                # Fetch the leaderboard data from the database
                leaderboard_data = get_leaderboard()
                leaderboard_html = """
                    <table style="width:100%; border: 1px solid #444; border-collapse: collapse; font-family: Arial, sans-serif; background-color: #2b2b2b;">
                        <thead>
                            <tr style="border: 1px solid #444; padding: 12px; background-color: #1a1a1a;">
                                <th style="border: 1px solid #444; padding: 12px; color: #ddd;">Rank</th>
                                <th style="border: 1px solid #444; padding: 12px; color: #ddd;">Model</th>
                                <th style="border: 1px solid #444; padding: 12px; color: #ddd;">Arena Elo</th>
                                <th style="border: 1px solid #444; padding: 12px; color: #ddd;">95% CI</th>
                                <th style="border: 1px solid #444; padding: 12px; color: #ddd;">Votes</th>
                                <th style="border: 1px solid #444; padding: 12px; color: #ddd;">Organization</th>
                                <th style="border: 1px solid #444; padding: 12px; color: #ddd;">License</th>
                                <th style="border: 1px solid #444; padding: 12px; color: #ddd;">Knowledge Cutoff</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr style="border: 1px solid #444; padding: 12px;">
                                <td style="border: 1px solid #444; padding: 12px; color: #ddd;">1</td>
                                <td style="border: 1px solid #444; padding: 12px; color: #ddd;">GPT-4-Turbo-2024-04-09</td>
                                <td style="border: 1px solid #444; padding: 12px; color: #ddd;">1258</td>
                                <td style="border: 1px solid #444; padding: 12px; color: #ddd;">+3/-3</td>
                                <td style="border: 1px solid #444; padding: 12px; color: #ddd;">44592</td>
                                <td style="border: 1px solid #444; padding: 12px; color: #ddd;">OpenAI</td>
                                <td style="border: 1px solid #444; padding: 12px; color: #ddd;">Proprietary</td>
                                <td style="border: 1px solid #444; padding: 12px; color: #ddd;">2023/12</td>
                            </tr>
                            <tr style="border: 1px solid #444; padding: 12px;">
                                <td style="border: 1px solid #444; padding: 12px; color: #ddd;">2</td>
                                <td style="border: 1px solid #444; padding: 12px; color: #ddd;">GPT-4-1106-preview</td>
                                <td style="border: 1px solid #444; padding: 12px; color: #ddd;">1252</td>
                                <td style="border: 1px solid #444; padding: 12px; color: #ddd;">+2/-3</td>
                                <td style="border: 1px solid #444; padding: 12px; color: #ddd;">76173</td>
                                <td style="border: 1px solid #444; padding: 12px; color: #ddd;">OpenAI</td>
                                <td style="border: 1px solid #444; padding: 12px; color: #ddd;">Proprietary</td>
                                <td style="border: 1px solid #444; padding: 12px; color: #ddd;">2023/4</td>
                            </tr>
                            <tr style="border: 1px solid #444; padding: 12px;">
                                <td style="border: 1px solid #444; padding: 12px; color: #ddd;">2</td>
                                <td style="border: 1px solid #444; padding: 12px; color: #ddd;">Gemini 1.5 Pro API-0409-Preview</td>
                                <td style="border: 1px solid #444; padding: 12px; color: #ddd;">1249</td>
                                <td style="border: 1px solid #444; padding: 12px; color: #ddd;">+3/-3</td>
                                <td style="border: 1px solid #444; padding: 12px; color: #ddd;">61011</td>
                                <td style="border: 1px solid #444; padding: 12px; color: #ddd;">Google</td>
                                <td style="border: 1px solid #444; padding: 12px; color: #ddd;">Proprietary</td>
                                <td style="border: 1px solid #444; padding: 12px; color: #ddd;">2023/11</td>
                            </tr>
                            <tr style="border: 1px solid #444; padding: 12px;">
                                <td style="border: 1px solid #444; padding: 12px; color: #ddd;">2</td>
                                <td style="border: 1px solid #444; padding: 12px; color: #ddd;">Claude 3 Opus</td>
                                <td style="border: 1px solid #444; padding: 12px; color: #ddd;">1248</td>
                                <td style="border: 1px solid #444; padding: 12px; color: #ddd;">+2/-2</td>
                                <td style="border: 1px solid #444; padding: 12px; color: #ddd;">101063</td>
                                <td style="border: 1px solid #444; padding: 12px; color: #ddd;">Anthropic</td>
                                <td style="border: 1px solid #444; padding: 12px; color: #ddd;">Proprietary</td>
                                <td style="border: 1px solid #444; padding: 12px; color: #ddd;">2023/8</td>
                            </tr>
                            <tr style="border: 1px solid #444; padding: 12px;">
                                <td style="border: 1px solid #444; padding: 12px; color: #ddd;">3</td>
                                <td style="border: 1px solid #444; padding: 12px; color: #ddd;">GPT-4-0125-preview</td>
                                <td style="border: 1px solid #444; padding: 12px; color: #ddd;">1246</td>
                                <td style="border: 1px solid #444; padding: 12px; color: #ddd;">+3/-2</td>
                                <td style="border: 1px solid #444; padding: 12px; color: #ddd;">70239</td>
                                <td style="border: 1px solid #444; padding: 12px; color: #ddd;">OpenAI</td>
                                <td style="border: 1px solid #444; padding: 12px; color: #ddd;">Proprietary</td>
                                <td style="border: 1px solid #444; padding: 12px; color: #ddd;">2023/12</td>
                            </tr>
                        </tbody>
                    </table>
                """
                leaderboard_html += """
                        </tbody>
                    </table>
                """
                
                gr.HTML(leaderboard_html)


    logging.debug("Gradio interface setup complete.")
    return demo


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    demo = setup_interface()
    demo.launch()
