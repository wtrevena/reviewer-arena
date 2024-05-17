import gradio as gr
from utils import process_paper
import os
import logging
import html
from logging_config import setup_logging

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


def review_papers(pdf_file):
    logging.info(f"Received file type: {type(pdf_file)}")
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
            {
                "Summary": "This is a placeholder review for Model 1. The paper explores advanced methodologies in reinforcement learning applied to autonomous driving systems, proposing significant enhancements to decision-making algorithms that could improve safety and operational efficiency. The authors provide a detailed analysis of the current limitations of existing systems and suggest innovative solutions that could transform the field.",
                "Soundness": "The assumptions underlying the proposed enhancements are occasionally not fully justified, particularly concerning the scalability of the algorithms under varied and unpredictable traffic conditions. A more rigorous examination of these assumptions is necessary to solidify the paper's foundation.",
                "Presentation": "While the paper is structured adequately, some sections delve into technical details that are not sufficiently elucidated for a broader audience. This could potentially limit the paper's impact and accessibility, making it challenging for non-specialists to fully grasp the implications of the research.",
                "Contribution": "The paper makes a moderate contribution to the existing body of knowledge, offering incremental improvements over current methodologies rather than a completely novel approach. However, these improvements are significant and could lead to better practical implementations in the field of autonomous driving.",
                "Strengths": "The initial results presented in the paper are promising, showing potential for the proposed methods. The inclusion of real-world data in the preliminary experiments adds a layer of credibility and relevance to the results, showcasing the practical applicability of the research.",
                "Weaknesses": "The paper lacks detailed exposition on the methodology, particularly in how the algorithms adapt to unexpected or novel scenarios. This is a critical area that requires further development and testing to ensure the robustness and reliability of the proposed solutions.",
                "Questions/Suggestions": "The statistical analysis section could be enhanced by incorporating more robust statistical techniques and a wider array of metrics. Additionally, conducting tests in a variety of driving environments could help in substantiating the claims made and strengthen the overall findings of the research.",
                "Ethics Review": "The research complies with all ethical standards, addressing potential ethical issues related to autonomous driving comprehensively. Issues such as privacy concerns, decision-making in critical situations, and the overall impact on societal norms are discussed and handled with the utmost care.",
                "Overall Score": "3/5",
                "Confidence": "Confidence in the findings is moderate. While the initial results are encouraging, the limited scope of testing and some unresolved questions regarding scalability and robustness temper the confidence in these results.",
                "Code of Conduct": "There are no violations of the code of conduct noted. The research upholds ethical standards and maintains transparency in methodologies and data usage, contributing to its integrity and the trustworthiness of the findings."
            },
            {
                "Summary": "This is a placeholder review for Model 2. The paper explores advanced methodologies in reinforcement learning applied to autonomous driving systems, proposing significant enhancements to decision-making algorithms that could improve safety and operational efficiency. The authors provide a detailed analysis of the current limitations of existing systems and suggest innovative solutions that could transform the field.",
                "Soundness": "The assumptions underlying the proposed enhancements are occasionally not fully justified, particularly concerning the scalability of the algorithms under varied and unpredictable traffic conditions. A more rigorous examination of these assumptions is necessary to solidify the paper's foundation.",
                "Presentation": "While the paper is structured adequately, some sections delve into technical details that are not sufficiently elucidated for a broader audience. This could potentially limit the paper's impact and accessibility, making it challenging for non-specialists to fully grasp the implications of the research.",
                "Contribution": "The paper makes a moderate contribution to the existing body of knowledge, offering incremental improvements over current methodologies rather than a completely novel approach. However, these improvements are significant and could lead to better practical implementations in the field of autonomous driving.",
                "Strengths": "The initial results presented in the paper are promising, showing potential for the proposed methods. The inclusion of real-world data in the preliminary experiments adds a layer of credibility and relevance to the results, showcasing the practical applicability of the research.",
                "Weaknesses": "The paper lacks detailed exposition on the methodology, particularly in how the algorithms adapt to unexpected or novel scenarios. This is a critical area that requires further development and testing to ensure the robustness and reliability of the proposed solutions.",
                "Questions/Suggestions": "The statistical analysis section could be enhanced by incorporating more robust statistical techniques and a wider array of metrics. Additionally, conducting tests in a variety of driving environments could help in substantiating the claims made and strengthen the overall findings of the research.",
                "Ethics Review": "The research complies with all ethical standards, addressing potential ethical issues related to autonomous driving comprehensively. Issues such as privacy concerns, decision-making in critical situations, and the overall impact on societal norms are discussed and handled with the utmost care.",
                "Overall Score": "3/5",
                "Confidence": "Confidence in the findings is moderate. While the initial results are encouraging, the limited scope of testing and some unresolved questions regarding scalability and robustness temper the confidence in these results.",
                "Code of Conduct": "There are no violations of the code of conduct noted. The research upholds ethical standards and maintains transparency in methodologies and data usage, contributing to its integrity and the trustworthiness of the findings."
            }
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
    return review_texts[0], review_texts[1], gr.update(visible=True), gr.update(visible=True), model_a, model_b


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
                gr.Markdown(
                    "Upload an academic paper to get reviews from two randomly selected LLMs.")
                with gr.Row():
                    file_input = gr.File(label="Upload Academic Paper")
                    submit_button = gr.Button(
                        "Submit!", elem_id="submit-button")
                with gr.Row():
                    with gr.Column():
                        gr.HTML("<div class='model-label'>Model A</div>")
                        review1 = gr.Markdown()
                    with gr.Column():
                        gr.HTML("<div class='model-label'>Model B</div>")
                        review2 = gr.Markdown()

                vote_options = ["👍 A is better",
                                "👍 B is better", "👔 Tie", "👎 Both are bad"]
                vote = gr.Radio(label="Vote on the best model",
                                choices=vote_options, value="Tie", visible=False)
                vote_button = gr.Button("Submit Vote", visible=False)
                vote_message = gr.HTML("", visible=False)
                another_paper_button = gr.Button(
                    "Review another paper", visible=False)

                model_identity_message = gr.HTML("", visible=False)

                def handle_vote(vote, model_a, model_b):
                    print(f"Vote received: {vote}")
                    message = f"<p>Thank you for your vote!</p><p>Model A: {model_a}</p><p>Model B: {model_b}</p>"
                    return gr.update(value=message, visible=True), gr.update(visible=False), gr.update(visible=False), gr.update(visible=True)

                vote_button.click(fn=handle_vote, inputs=[vote, model_identity_message, model_identity_message], outputs=[
                                  vote_message, vote, vote_button, another_paper_button])

                submit_button.click(
                    fn=review_papers,
                    inputs=[file_input],
                    outputs=[review1, review2, vote, vote_button,
                             model_identity_message, model_identity_message] 
                )

                another_paper_button.click(
                    fn=lambda: None, inputs=None, outputs=None, js="() => { location.reload(); }")
            with gr.TabItem("Leaderboard"):
                gr.Markdown("## Leaderboard")
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
                gr.HTML(leaderboard_html)

    logging.debug("Gradio interface setup complete.")
    return demo


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    demo = setup_interface()
    demo.launch()
