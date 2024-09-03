from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import requests
import PyPDF2
import json
from db_queries import check_prompt_file_db, store_roadmap_in_db, path_status
from concurrent.futures import ThreadPoolExecutor
import logging
from config import cv_path, port

app = Flask(__name__)
CORS(app)

openai.api_key = "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"

executor = ThreadPoolExecutor(max_workers=10)  

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
logging.basicConfig(level=logging.DEBUG)

    
def single_prompt(prompt, model, temperature=0.7):
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {openai.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "messages": [{
                    "role": "user",
                    "content": (
                        f"""As an experienced career advisor, analyze the following prompt and Create the best suitable career roadmap.
                        prompt: {prompt}."""
                        " Output should be in JSON format with unique keys for each step:"
                        """{
                          "roadmap": {
                            "step1": {"title": "Junior Developer", "description": "General description of the job", "key_skills": ["Skill 1", "Skill 2"]},
                            "step2": {"title": "Next Step Title", "description": "General description of the job", "key_skills": ["Skill 1", "Skill 2"]},
                            "optional_step1": {"title": "Optional Path Title", "description": "General description of the job", "key_skills": ["Skill 1", "Skill 2"]}
                          }
                        }

                        Start with current position and end with goal and explore all Optional steps and they can be placed between main steps if necessary. Ensure the final step is labeled as the 'goal' instead of 'step' which will come last in the data and number of skills required should be = 5."""
                    )
                }],
                "temperature": temperature
            }
        )
        result = response.json()
        return result
    except Exception as e:
        logger.error(f"Error in single_prompt: {str(e)}")
        return None
    


def extract_text_from_pdf(pdf_path):
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
        return text
    except Exception as e:
        logger.error(f"Error in extract_text_from_pdf: {str(e)}")
        return ""

def road_map_cv(resume_text, model, temperature= 0.7):
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {openai.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "messages": [{
                    "role": "user",
                    "content": "As an experienced career advisor, Analyze the following resume and create a career roadmap in JSON format, including optional career paths. Resume text: " + resume_text + """
                    Output should be in JSON format with unique keys for each step:
                    {
                      "roadmap": {
                        "step1": {"title": "Junior Developer", "description": "General description of the job", "key_skills": ["Skill 1", "Skill 2"]},
                        "step2": {"title": "Next Step Title", "description": "General description of the job", "key_skills": ["Skill 1", "Skill 2"]},
                        "optional_step1": {"title": "Optional Path Title", "description": "General description of the job", "key_skills": ["Skill 1", "Skill 2"]}
                      }
                    }
                    Start with current position and end with goal and explore all Optional steps and they can be placed between main steps if necessary. Ensure the final step is labeled as the 'goal' instead of 'step' which will come last in the data and number of skills required should be >=5."""
                }],
                "temperature": temperature
            }
        ) 
        result = response.json()
        return result
    except Exception as e:
        logger.error(f"Error in road_map_cv: {str(e)}")
        return None
    


def process_roadmap(id, model):
    try:
        prompt_file_data = check_prompt_file_db(id)

        prompt = None
        cv = None

        if prompt_file_data[0] is None and prompt_file_data[1] is not None:
            cv = f"{cv_path}/{prompt_file_data[1]}"
        elif prompt_file_data[0] is not None:
            prompt = prompt_file_data[0]
        elif prompt_file_data[1] is not None:
            prompt = prompt_file_data[1]

        if cv:
            resume_text = extract_text_from_pdf(cv)
            model = model
            result = road_map_cv(resume_text, model)
        elif prompt_file_data:
            if prompt_file_data[0] is not None:
                prompt = prompt_file_data[0]
            else:
                prompt = prompt_file_data[1]

            model = model
            result = single_prompt(prompt, model)
        else:
            message = logger.error(f"No valid CV or prompt found for ID: {id}")
            return message

        if result:
            content = result['choices'][0]['message']['content']
            response_formatted = content.strip('```json\n').strip()
            response_dict = json.loads(response_formatted)


            store_roadmap_in_db(path_id=id, roadmap_json=response_dict)  # Save to DB
            path_status(id)
            logger.info(f"Roadmap generated and saved for ID: {id}")
        else:
            logger.error(f"Failed to generate roadmap for ID: {id}")

    except Exception as e:
        logger.error(f"Error in process_roadmap for ID {id}: {str(e)}")


def process_regenerate_roadmap(id, model):
    try:
        prompt_file_data = check_prompt_file_db(id)

        prompt = None
        cv = None

        if prompt_file_data[0] is None and prompt_file_data[1] is not None:
            cv = f"{cv_path}/{prompt_file_data[1]}"
        elif prompt_file_data[0] is not None:
            prompt = prompt_file_data[0]
        elif prompt_file_data[1] is not None:
            prompt = prompt_file_data[1]

        if cv:
            resume_text = extract_text_from_pdf(cv)
            result = road_map_cv(resume_text, model, temperature=0.3)
        elif prompt_file_data:
            prompt = prompt_file_data[0] if prompt_file_data[0] else prompt_file_data[1]
            result = single_prompt(prompt, model)
        else:
            logger.error(f"No valid CV or prompt found for ID: {id}")
            return

        if result:
            content = result['choices'][0]['message']['content']
            response_formatted = content.strip('```json\n').strip()
            response_dict = json.loads(response_formatted)


            store_roadmap_in_db(path_id=id, roadmap_json=response_dict)  # Save to DB
            path_status(id)
            logger.info(f"Roadmap regenerated and saved for ID: {id}")
        else:
            logger.error(f"Failed to regenerate roadmap for ID: {id}")

    except Exception as e:
        logger.error(f"Error in process_regenerate_roadmap for ID {id}: {str(e)}")
    
    
    
@app.route('/generate_roadmap', methods=['POST'])
def generate_roadmap():
    try:
        id = request.args.get('id')
        if not id:
            return jsonify({'error': 'ID is required'}), 400

        response_message = f"Analyzing Starts Successfully"
        model = "gpt-4"
        executor.submit(process_roadmap, id, model)  
        return jsonify({'status': response_message}), 200

    except Exception as e:
        logger.error(f"Error in generate_roadmap: {str(e)}")
        return jsonify({'error': str(e)}), 500
    
    
@app.route('/regenerate_roadmap', methods=['POST'])
def regenerate_roadmap():
    try:
        id = request.args.get('id')
        if not id:
            return jsonify({'error': 'ID is required'}), 400

        response_message = f"Analyzing Starts Successfully"
        model = "gpt-4o"
        executor.submit(process_regenerate_roadmap, id, model)  
        return jsonify({'status': response_message}), 200

    except Exception as e:
        logger.error(f"Error in regenerate_roadmap: {str(e)}")
        return jsonify({'error': str(e)}), 500


if __name__ == "__main__":
    try:
        app.run(debug=True, host='0.0.0.0', threaded=True, port=port)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
