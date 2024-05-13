import os
import logging
import openai
import tiktoken
import re
import anthropic
import cohere
import google.generativeai as genai
import time
from file_utils import read_file
from openai import OpenAI

class Paper:
    def __init__(self, arxiv_id, tex_file):
        self.arxiv_id = arxiv_id
        self.tex_file = tex_file

class PaperProcessor:
    MAX_TOKENS = 127192
    encoding = tiktoken.encoding_for_model("gpt-4-0125-preview")

    def __init__(self, prompt_dir, model, openai_api_key, claude_api_key, gemini_api_key, commandr_api_key):
        self.prompt_dir = prompt_dir
        self.model = model
        self.openai_api_key = openai_api_key
        self.claude_api_key = claude_api_key
        self.gemini_api_key = gemini_api_key
        self.commandr_api_key = commandr_api_key

    def count_tokens(self, text):
        return len(self.encoding.encode(text))

    def truncate_content(self, content):
        token_count = self.count_tokens(content)
        logging.debug(f"Token count before truncation: {token_count}")
        if token_count > self.MAX_TOKENS:
            tokens = self.encoding.encode(content)
            truncated_tokens = tokens[:self.MAX_TOKENS]
            truncated_content = self.encoding.decode(truncated_tokens)
            logging.debug(f"Content truncated. Token count after truncation: {self.count_tokens(truncated_content)}")
            return truncated_content
        return content

    def prepare_base_prompt(self, paper):
        return paper.tex_file

    def call_model(self, prompt, model_type):
        system_role_file_path = os.path.join(self.prompt_dir, "systemrole.txt")
        if not os.path.exists(system_role_file_path):
            logging.error(f"System role file not found: {system_role_file_path}")
            return None

        system_role = read_file(system_role_file_path)
        logging.debug(f"Token count of full prompt: {self.count_tokens(prompt)}")
        logging.info(f"Sending the following prompt to {model_type}: {prompt}")

        try:
            if model_type == 'gpt':
                client = OpenAI(api_key=self.openai_api_key)
                messages = [{"role": "system", "content": system_role}, {"role": "user", "content": prompt}]
                completion = client.chat.completions.create(
                    model="gpt-4-turbo-2024-04-09",
                    messages=messages,
                    temperature=1
                )
                return completion.choices[0].message.content.strip()

            elif model_type == 'claude':
                client = anthropic.Anthropic(api_key=self.claude_api_key)
                response = client.messages.create(
                    model='claude-3-opus-20240229',
                    max_tokens=4096,
                    system=system_role,
                    temperature=0.5, 
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text

            elif model_type == 'commandr':
                co = cohere.Client(self.commandr_api_key)
                response = co.chat(
                    model="command-r-plus",
                    message=prompt,
                    preamble=system_role
                )
                return response.text

            elif model_type == 'gemini':
                genai.configure(api_key=self.gemini_api_key)
                model = genai.GenerativeModel('gemini-pro')
                response = model.generate_content(prompt)
                return response.candidates[0].content.parts[0].text

        except Exception as e:
            logging.error(f"Exception occurred: {e}")
            return None

    def is_content_appropriate(self, content):
        try:
            response = openai.moderations.create(input=content)
            return not response["results"][0]["flagged"]
        except Exception as e:
            logging.error(f"Exception occurred while checking content appropriateness: {e}")
            return True  # In case of an error, default to content being appropriate
    
    def get_prompt_files(self, prompt_dir):
        return [f for f in os.listdir(prompt_dir) if f.endswith('.txt') and f.startswith('question')]

    def process_paper(self, paper):
        openai.api_key = self.openai_api_key
        start_time = time.time()

        base_prompt = self.prepare_base_prompt(paper)
        if base_prompt is None:
            return "Error: Base prompt could not be prepared."

        moderation_response = openai.moderations.create(input=base_prompt)
        if moderation_response.results[0].flagged:
            return ["Desk Rejected", "The paper contains inappropriate or harmful content."]

        review_output = []
        previous_responses = []
        header = ['Summary:', 'Soundness:', 'Presentation:', 'Contribution:', 'Strengths:', 'Weaknesses:', 'Questions:', 'Flag For Ethics Review:', 'Rating:', 'Confidence:', 'Code Of Conduct:']
        for i in range(1, 12):
            question_file = os.path.join(self.prompt_dir, f"question{i}.txt")
            question_text = read_file(question_file)

            if i == 1:
                prompt = f"{question_text}\n\n####\n{base_prompt}\n####"
            else:
                prompt = f"\nHere is your review so far:\n{' '.join(previous_responses)}\n\nHere are your reviewer instructions. Please answer the following question:\n{question_text}"

            truncated_prompt = self.truncate_content(prompt)
            logging.info(f"Processing prompt for question {i}")

            response = self.call_model(truncated_prompt, self.model)
            if response is None:
                response = "N/A"

            if i in [2, 3, 4, 10]:
                number_match = re.search(r'\b\d+\b', response)
                if number_match:
                    number = int(number_match.group(0))
                    response = '5/5' if number > 5 else number_match.group(0) + '/5'
            elif i == 9:
                number_match = re.search(r'\b\d+\b', response)
                if number_match:
                    response = number_match.group(0) + '/10'

            response_with_header = f"{header[i-1]} {response}"
            review_output.append(response_with_header)
            previous_responses.append(response)

        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"Time taken to process paper: {elapsed_time:.2f} seconds")
        return review_output

