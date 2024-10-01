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
from db_queries import check_prompt_file_db, path_status_analyzed, path_status_analyzing, path_status_pending
from config import cv_path, port, openapi_key, key, node_server_url
from test import DataBase
import requests

app = Flask(__name__)
CORS(app)

db = DataBase()
secret_key = key

openai.api_key = openapi_key

executor = ThreadPoolExecutor(max_workers=15)  

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
logging.basicConfig(level=logging.DEBUG)


def single_prompt(prompt, model, temperature=0.7):
    try:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {openai.api_key}",
            "Content-Type": "application/json"
        }

        system_message = {
            "role": "system",
            "content": (
                "You are an experienced career advisor with a deep understanding of career development paths. "
                "Provide detailed and structured career metro-map with multiple paths, branches, and goals based on the user's input."
            )
        }

        user_message = {
            "role": "user",
            "content": (
                f"""Create an in-depth career roadmap with multiple branches, steps, and goals from the following prompt. 
                Include different paths (managerial, technical, exploratory) with unique colors while keeping the main path in consistency combined towards the end goal. The steps array must have a minimum of 8 steps, with at least 5 steps dedicated to the black path (current path), and additional objects in the steps array for the remaining paths.

                Prompt: {prompt}
                Structure the output in JSON as follows:
                {{
                  "roadmap": {{
                    "branch": {{
                      "color": "black",  # Main path (current path toward the goal)
                      "steps": [
                        {{
                          "title": "Title for the first step",
                          "description": "Description for the first step",
                          "skills": [
                            {{ "title": "Skill name" }}  
                            # Add 5+ skills here
                          ],
                          "branches": [  # Sub-branches for career exploration
                            {{
                              "color": "green",  # Exploratory path
                              "steps": [
                                {{
                                  "title": "Exploratory Step Title",
                                  "description": "Description for this position",
                                  "skills": [
                                    {{ "title": "Skill name" }}
                                    # Add 5+ skills here
                                  ]
                                }}
                                # Add atleast 4 or more steps (if needed) for this branch
                              ]
                            }},
                            {{
                              "color": "purple",  # Managerial path
                              "steps": [
                                {{
                                  "title": "Managerial Step Title",
                                  "description": "Description for this position",
                                  "skills": [
                                    {{ "title": "Skill name" }}
                                    # Add 5+ skills here
                                  ]
                                }}
                                # Add atleast 4 or more steps (if needed) for this branch
                              ]
                            }},
                            {{
                              "color": "blue",  # Technical path
                              "steps": [
                                {{
                                  "title": "Technical Step Title",
                                  "description": "Description for this position",
                                  "skills": [
                                    {{ "title": "Skill name" }}
                                    # Add 5+ skills here
                                  ]
                                }}
                                # Add atleast 4 or more steps (if needed) for this branch
                              ]
                            }}
                          ]
                        }},
                        # Add at least 4 or more steps for the main black path here
                        {{
                          "title": "Title ",
                          "description": "Description of the job",
                          "skills": [
                            {{ "title": "Skill name" }}
                            # Add 5+ skills here
                          ]
                        }}
                       ]
                    }}
                  }}
                }}
                - Start with the current state.
                - Provide a detailed, in-depth career roadmap exploring all possible paths and each branch other than current one will reach to it's highest possible position whether it aligns with the user objective or not.
                - Separate paths by color: main path (black), default (green), managerial (purple), technical (blue).
                - Each branch must contain at least 5+ steps and sub-branches.
                - Ensure each step contains 5+ unique skills.
                - The last step represents reaching the goal of the respective branch.
                """
            )
        }

        data = {
            "model": model,
            "messages": [system_message, user_message],
            "temperature": temperature
        }

        response = requests.post(url, headers=headers, json=data)
        return response.json()
    
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
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {openai.api_key}",
            "Content-Type": "application/json"
        }

        system_message = {
            "role": "system",
            "content": (
                "You are an experienced career advisor with a deep understanding of career development paths. "
                "Provide detailed and structured career metro-map with multiple paths, branches, and goals based on the user's input."
            )
        }

        user_message = {
            "role": "user",
            "content": (
                f"""Create an in-depth career roadmap with multiple branches, steps, and goals from the following prompt. 
                Include different paths (managerial, technical, exploratory) with unique colors while keeping the main path in consistency combined towards the end goal. The steps array must have a minimum of 8 steps, with at least 5 steps dedicated to the black path (current path), and additional objects in the steps array for the remaining paths.

                Resume Text: {resume_text}
                Structure the output in JSON as follows:
                {{
                  "roadmap": {{
                    "branch": {{
                      "color": "black",  # Main path (current path toward the goal)
                      "steps": [
                        {{
                          "title": "Title for the first step",
                          "description": "Description for the first step",
                          "skills": [
                            {{ "title": "Skill name" }}  
                            # Add 5+ skills here
                          ],
                          "branches": [  # Sub-branches for career exploration
                            {{
                              "color": "green",  # Exploratory path
                              "steps": [
                                {{
                                  "title": "Exploratory Step Title",
                                  "description": "Description for this position",
                                  "skills": [
                                    {{ "title": "Skill name" }}
                                    # Add 5+ skills here
                                  ]
                                }}
                                # Add atleast 4 or more steps (if needed) for this branch
                              ]
                            }},
                            {{
                              "color": "purple",  # Managerial path
                              "steps": [
                                {{
                                  "title": "Managerial Step Title",
                                  "description": "Description for this position",
                                  "skills": [
                                    {{ "title": "Skill name" }}
                                    # Add 5+ skills here
                                  ]
                                }}
                                # Add atleast 4 or more steps (if needed) for this branch
                              ]
                            }},
                            {{
                              "color": "blue",  # Technical path
                              "steps": [
                                {{
                                  "title": "Technical Step Title",
                                  "description": "Description for this position",
                                  "skills": [
                                    {{ "title": "Skill name" }}
                                    # Add 5+ skills here
                                  ]
                                }}
                                # Add atleast 4 or more steps (if needed) for this branch
                              ]
                            }}
                          ]
                        }},
                        # Add at least 4 or more steps for the main black path here
                        {{
                          "title": "Title ",
                          "description": "Description of the job",
                          "skills": [
                            {{ "title": "Skill name" }}
                            # Add 5+ skills here
                          ]
                        }}
                       ]
                    }}
                  }}
                }}
                - Start with the current state.
                - Provide a detailed, in-depth career roadmap exploring all possible paths and each branch other than current one will reach to it's highest possible position whether it aligns with the user objective or not.
                - Separate paths by color: main path (black), default (green), managerial (purple), technical (blue).
                - Each branch must contain at least 5+ steps and sub-branches.
                - Ensure each step contains 5+ unique skills.
                - The last step represents reaching the goal of the respective branch.
                """
            )
        }

        data = {
            "model": model,
            "messages": [system_message, user_message],
            "temperature": temperature
        }

        response = requests.post(url, headers=headers, json=data)
        return response.json()

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
      
def send_notification (token,id):
    URL = f"{node_server_url}/create-path-analyse-notifications/{id}"
    headers = {
      'Accept': 'application/json',
      'Content-Type': 'application/json',
      'Authorization': f"Bearer {token}"
    }
    logger.debug(URL)
    req = requests.post(url=URL,headers=headers)
    if req.status_code == 200:
      data = json.loads(req.json)
      logger.debug(data['message'])
    else:
      logger.debug("Send Notification Request Failed")
      


def process_roadmap(id, model, token):
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
                    # store_roadmap_in_db(path_id=id, roadmap_json=response_formatted)  # Save to DB
                    db.insert_road_map(response_formatted, id)
                    
                    # """ REMOVE THIS AFTER INCLUDING DB QUERIES """
                    
                    file_path = 'response.json'

                    with open(file_path, 'w') as json_file:
                        json.dump(response_formatted, json_file, indent=4)

                    print(f"Data successfully saved to {file_path}")
                    
                    
                    
                    logger.info(f"Output saved successfully to db against path_id = {id}.")
                    path_status_analyzed(id)
                    logger.info(f"Status Changed to 'analyzed' against path_id = {id}.")
                    send_notification(token,id)
                    
                except Exception as e:
                    logger.error(f"Error saving JSON to file or database: {str(e)}")
                    path_status_pending(id)
            else:
                logger.error("No valid JSON block found in the content.")
                path_status_pending(id)

    except Exception as e:
        logger.error(f"Error in process_roadmap for ID {id}: {str(e)}")
        path_status_pending(id)
        
                

def process_regenerate_roadmap(id, model,token):
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
                    # store_roadmap_in_db(path_id=id, roadmap_json=response_formatted)  # Save to DB
                    db.insert_road_map(response_formatted, id)
                    logger.info(f"Output saved successfully to db against path_id = {id}.")
                    path_status_analyzed(id)
                    logger.info(f"Status Changed to 'analyzed' against path_id = {id}.")
                    send_notification(token,id)
                except Exception as e:
                    logger.error(f"Error saving JSON to file or database: {str(e)}")
                    path_status_pending(id)
            else:
                logger.error("No valid JSON block found in the content.")
                path_status_pending(id)

    except Exception as e:
        logger.error(f"Error in process_roadmap for ID {id}: {str(e)}")
        path_status_pending(id)
        
    
    
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
        executor.submit(process_roadmap, id, model,token)  
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
        executor.submit(process_regenerate_roadmap, id, model,token)  
        return jsonify({'status': True, 'message': response_message}), 200

    except Exception as e:
        logger.error(f"Error in regenerate_roadmap: {str(e)}")
        return jsonify({'status': False}), 500


if __name__ == "__main__":
    try:
        app.run(debug=True, host='0.0.0.0', threaded=True, port=port)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
