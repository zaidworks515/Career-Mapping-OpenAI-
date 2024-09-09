import re
from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import requests
import PyPDF2
import json
from jwt import decode, ExpiredSignatureError, InvalidTokenError
from concurrent.futures import ThreadPoolExecutor
import logging
from db_queries import check_prompt_file_db, store_roadmap_in_db, path_status_analyzed, path_status_analyzing
from config import cv_path, port, openapi_key, key

app = Flask(__name__)
CORS(app)

secret_key = key

openai.api_key = openapi_key

executor = ThreadPoolExecutor(max_workers=15)  

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
                "messages": [
                    {"role": "system", "content": "You are an experienced career advisor with a deep understanding of career development paths. Provide detailed and structured career roadmaps with multiple paths and goals based on the user's input."},
                    {
                        "role": "user",
                        "content": (
                            f"""Create an in depth detailed career roadmap with multiple branches, steps, and goals from the following prompt. Include branches, optional steps, and sub-branches as needed.

                            Prompt: {prompt}

                            Structure the output in JSON as follows:

                            {{
                              "roadmap": {{
                                "branch_{{branch_number}}": {{
                                  "step_{{step_number}}": {{
                                    "title": "Job Title",
                                    "description": "Job description",
                                    "key_skills": ["Skill 1", "Skill 2", "Skill 3", "Skill 4", "Skill 5"]
                                  }},
                                  "optional_step_{{optional_step_number}}": {{
                                    "title": "Job Title",
                                    "description": "Job description",
                                    "key_skills": ["Skill 1", "Skill 2", "Skill 3", "Skill 4", "Skill 5"]
                                  }},
                                  "sub_branch_{{sub_branch_number}}": {{
                                    "step_{{sub_step_number}}": {{
                                      "title": "Sub-branch Job Title",
                                      "description": "Sub-branch job description",
                                      "key_skills": ["Skill 1", "Skill 2", "Skill 3", "Skill 4", "Skill 5"]
                                    }},
                                    "optional_step_{{sub_optional_step_number}}": {{
                                      "title": "Job Title",
                                      "description": "Job description",
                                      "key_skills": ["Skill 1", "Skill 2", "Skill 3", "Skill 4", "Skill 5"]
                                    }},
                                    "goal_{{sub_goal_number}}": {{
                                      "title": "Final Sub-branch Goal",
                                      "description": "Sub-branch goal description",
                                      "key_skills": ["Skill 1", "Skill 2", "Skill 3", "Skill 4", "Skill 5"]
                                    }}
                                  }},
                                  "goal_{{branch_goal_number}}": {{
                                    "title": "Final Branch Goal",
                                    "description": "Branch goal description",
                                    "key_skills": ["Skill 1", "Skill 2", "Skill 3", "Skill 4", "Skill 5"]
                                  }}
                                }},
                                "branch_{{branch_number}}": {{
                                  "step_{{step_number}}": {{
                                    "title": "Job Title",
                                    "description": "Job description",
                                    "key_skills": ["Skill A", "Skill B", "Skill C", "Skill D", "Skill E"]
                                  }},
                                  "optional_step_{{optional_step_number}}": {{
                                    "title": "Job Title",
                                    "description": "Job description",
                                    "key_skills": ["Skill A", "Skill B", "Skill C", "Skill D", "Skill E"]
                                  }},
                                  "sub_branch_{{sub_branch_number}}": {{
                                    "step_{{sub_step_number}}": {{
                                      "title": "Sub-branch Job Title",
                                      "description": "Sub-branch job description",
                                      "key_skills": ["Skill A", "Skill B", "Skill C", "Skill D", "Skill E"]
                                    }},
                                    "goal_{{sub_goal_number}}": {{
                                      "title": "Final Sub-branch Goal",
                                      "description": "Sub-branch goal description",
                                      "key_skills": ["Skill A", "Skill B", "Skill C", "Skill D", "Skill E"]
                                    }}
                                  }},
                                  "goal_{{branch_goal_number}}": {{
                                    "title": "Final Branch Goal",
                                    "description": "Branch goal description",
                                    "key_skills": ["Skill A", "Skill B", "Skill C", "Skill D", "Skill E"]
                                  }}
                                }}
                              }}
                            }}

                            - Ensure each branch and sub-branch has unique steps and skills, and a final goal.
                            - Include optional steps and alternate paths as relevant.
                            - Avoid repeating steps or goals.
                            """
                        )
                    }
                ],
                "temperature": temperature
            }
        )
        result = response.json()
        return result
    except Exception as e:
        logger.error(f"Error in single_prompt: {str(e)}")
        return None
    


def extract_text_from_pdf(pdf_path):
    text = ""
    
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            text += page.extract_text() or ''  
    
    text = re.sub(r'\s+', ' ', text)  
    
    text = re.sub(r'[^\x00-\x7F]+', '', text)  
    text = text.strip()

    return text



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
                "messages": [
                    {"role": "system", "content": "You are an experienced career advisor with a deep understanding of career development paths. Provide detailed and structured career roadmaps with multiple paths and goals based on the user's input."},
                    {
                        "role": "user",
                        "content": (
                            f"""Create an in depth detailed career roadmap with multiple branches, steps, and goals from the following extracted resume text. Include branches, optional steps, and sub-branches as needed.

                            Resume Text: {resume_text}

                            Structure the output in JSON as follows:

                            {{
                              "roadmap": {{
                                "branch_{{branch_number}}": {{
                                  "step_{{step_number}}": {{
                                    "title": "Job Title",
                                    "description": "Job description",
                                    "key_skills": ["Skill 1", "Skill 2", "Skill 3", "Skill 4", "Skill 5"]
                                  }},
                                  "optional_step_{{optional_step_number}}": {{
                                    "title": "Job Title",
                                    "description": "Job description",
                                    "key_skills": ["Skill 1", "Skill 2", "Skill 3", "Skill 4", "Skill 5"]
                                  }},
                                  "sub_branch_{{sub_branch_number}}": {{
                                    "step_{{sub_step_number}}": {{
                                      "title": "Sub-branch Job Title",
                                      "description": "Sub-branch job description",
                                      "key_skills": ["Skill 1", "Skill 2", "Skill 3", "Skill 4", "Skill 5"]
                                    }},
                                    "optional_step_{{sub_optional_step_number}}": {{
                                      "title": "Job Title",
                                      "description": "Job description",
                                      "key_skills": ["Skill 1", "Skill 2", "Skill 3", "Skill 4", "Skill 5"]
                                    }},
                                    "goal_{{sub_goal_number}}": {{
                                      "title": "Final Sub-branch Goal",
                                      "description": "Sub-branch goal description",
                                      "key_skills": ["Skill 1", "Skill 2", "Skill 3", "Skill 4", "Skill 5"]
                                    }}
                                  }},
                                  "goal_{{branch_goal_number}}": {{
                                    "title": "Final Branch Goal",
                                    "description": "Branch goal description",
                                    "key_skills": ["Skill 1", "Skill 2", "Skill 3", "Skill 4", "Skill 5"]
                                  }}
                                }},
                                "branch_{{branch_number}}": {{
                                  "step_{{step_number}}": {{
                                    "title": "Job Title",
                                    "description": "Job description",
                                    "key_skills": ["Skill A", "Skill B", "Skill C", "Skill D", "Skill E"]
                                  }},
                                  "optional_step_{{optional_step_number}}": {{
                                    "title": "Job Title",
                                    "description": "Job description",
                                    "key_skills": ["Skill A", "Skill B", "Skill C", "Skill D", "Skill E"]
                                  }},
                                  "sub_branch_{{sub_branch_number}}": {{
                                    "step_{{sub_step_number}}": {{
                                      "title": "Sub-branch Job Title",
                                      "description": "Sub-branch job description",
                                      "key_skills": ["Skill A", "Skill B", "Skill C", "Skill D", "Skill E"]
                                    }},
                                    "goal_{{sub_goal_number}}": {{
                                      "title": "Final Sub-branch Goal",
                                      "description": "Sub-branch goal description",
                                      "key_skills": ["Skill A", "Skill B", "Skill C", "Skill D", "Skill E"]
                                    }}
                                  }},
                                  "goal_{{branch_goal_number}}": {{
                                    "title": "Final Branch Goal",
                                    "description": "Branch goal description",
                                    "key_skills": ["Skill A", "Skill B", "Skill C", "Skill D", "Skill E"]
                                  }}
                                }}
                              }}
                            }}

                            - Ensure each branch and sub-branch has unique steps and skills, and a final goal.
                            - Include optional steps and alternate paths as relevant.
                            - Avoid repeating steps or goals.
                            """
                        )
                    }
                    ],
                "temperature": temperature
            }
        ) 
        result = response.json()
        return result
    except Exception as e:
        logger.error(f"Error in road_map_cv: {str(e)}")
        return None
    

    
    
def extract_json_from_content(content):
    try:
        start_idx = content.find('{')
        end_idx = content.rfind('}') + 1
        
        if start_idx == -1 or end_idx == -1:
            return None  # If No JSON block found

        json_str = content[start_idx:end_idx].strip()
        
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from content: {e}")
        return None
    except Exception as e:
        logger.error(f"Error extracting JSON from content: {e}")
        return None


def process_roadmap(id, model):
    try:
        prompt_file_data = check_prompt_file_db(id)

        prompt = None
        cv = None

        if prompt_file_data[0]:
            prompt = prompt_file_data[0]
        else:
            cv = f"{cv_path}/{prompt_file_data[1]}"

        if cv:
            resume_text = extract_text_from_pdf(cv)
            result = road_map_cv(resume_text, model)
        elif prompt_file_data:
            prompt = prompt_file_data[0] if prompt_file_data[0] else prompt_file_data[1]
            result = single_prompt(prompt, model)
        else:
            logger.error(f"No valid CV or prompt found for ID: {id}")
            return "No valid CV or prompt found"

        if result:
            content = result['choices'][0]['message']['content']
            logger.debug(f"API response content: {content}")
            
            response_formatted = extract_json_from_content(content)

            if response_formatted:
                try:
                    store_roadmap_in_db(path_id=id, roadmap_json=response_formatted)  # Save to DB
                    
                    """ REMOVE THIS AFTER INCLUDING DB QUERIES """
                    
                    file_path = 'response.json'

                    with open(file_path, 'w') as json_file:
                        json.dump(response_formatted, json_file, indent=4)

                    print(f"Data successfully saved to {file_path}")
                    
                    
                    
                    
                    
                    logger.info(f"Output saved successfully to db against path_id = {id}.")
                    path_status_analyzed(id)
                    logger.info(f"Status Changed to 'analyzed' against path_id = {id}.")
                except Exception as e:
                    logger.error(f"Error saving JSON to file or database: {str(e)}")
            else:
                logger.error("No valid JSON block found in the content.")

    except Exception as e:
        logger.error(f"Error in process_roadmap for ID {id}: {str(e)}")
        
                

def process_regenerate_roadmap(id, model):
    try:
        prompt_file_data = check_prompt_file_db(id)

        prompt = None
        cv = None

        if prompt_file_data[0]:
            prompt = prompt_file_data[0]
        else:
            cv = f"{cv_path}/{prompt_file_data[1]}"

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
            logger.debug(f"API response content: {content}")
            
            response_formatted = extract_json_from_content(content)

            if response_formatted:
                try:
                    store_roadmap_in_db(path_id=id, roadmap_json=response_formatted)  # Save to DB
                    logger.info(f"Output saved successfully to db against path_id = {id}.")
                    path_status_analyzed(id)
                    logger.info(f"Status Changed to 'analyzed' against path_id = {id}.")
                except Exception as e:
                    logger.error(f"Error saving JSON to file or database: {str(e)}")
            else:
                logger.error("No valid JSON block found in the content.")

    except Exception as e:
        logger.error(f"Error in process_roadmap for ID {id}: {str(e)}")
        
    
    
@app.route('/generate_roadmap', methods=['POST'])
def generate_roadmap():
    try:
        auth_header = request.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authorization required'}), 400
        
        token = auth_header.split(' ')[1]
        
        try:
            decoded_token = decode(token, secret_key, algorithms=["HS256"])
        except ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        
        
        id = request.args.get('id')
        if not id:
            return jsonify({'error': 'ID is required'}), 400
        
        path_status_analyzing(id)
        response_message = f"Analyzing Starts Successfully"
        model = "gpt-4"
        executor.submit(process_roadmap, id, model)  
        return jsonify({'status': True, 'message': response_message}), 200

    except Exception as e:
        logger.error(f"Error in generate_roadmap: {str(e)}")
        return jsonify({'status': False}), 500
    
    
@app.route('/regenerate_roadmap', methods=['POST'])
def regenerate_roadmap():
    try:
        auth_header = request.headers.get('Authorization')
                
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authorization required'}), 400
        
        token = auth_header.split(' ')[1]
        
        try:
            decoded_token = decode(token, secret_key, algorithms=["HS256"])
        except ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        
        
        id = request.args.get('id')
        if not id:
            return jsonify({'error': 'ID is required'}), 400

        path_status_analyzing(id)
        response_message = f"Analyzing Starts Successfully"
        model = "gpt-4o"
        executor.submit(process_regenerate_roadmap, id, model)  
        return jsonify({'status': True, 'message': response_message}), 200

    except Exception as e:
        logger.error(f"Error in regenerate_roadmap: {str(e)}")
        return jsonify({'status': False}), 500


if __name__ == "__main__":
    try:
        app.run(debug=True, host='0.0.0.0', threaded=True, port=port)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
