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
from db_queries import check_prompt_file_db, path_status_analyzed, path_status_analyzing, path_status_pending, get_all_steps_and_skills
from config import cv_path, port, openapi_key, key, node_server_url
from database import DataBase
import requests
import time
from datetime import datetime
from create_pdf import send_plan_to_admin


app = Flask(__name__)
CORS(app)

db = DataBase()
secret_key = key

openai.api_key = openapi_key

executor = ThreadPoolExecutor(max_workers=15)  

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
logging.basicConfig(level=logging.DEBUG)


def update_title(obj):
    """
    Recursively updates the title field in the JSON object by splitting on ':'
    and taking the last part.
    """
    if isinstance(obj, dict):
        updated_obj = {}
        for key, value in obj.items():
            if key == "title" and isinstance(value, str):
                updated_obj[key] = value.split(":")[-1].strip()
            else:
                updated_obj[key] = update_title(value)
        return updated_obj
    elif isinstance(obj, list):
        return [update_title(item) for item in obj]
    return obj



def single_prompt(prompt, model, temperature=0.6):
    system_instructions = (
                "You are an experienced career advisor with a deep understanding of career development paths. "
                "Provide detailed and structured career metro-map with multiple paths, branches, and goals based on the user's input."
                "Make sure that while making json Property name must be enclosed in double quotes"
            )
    
    try:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {openai.api_key}",
            "Content-Type": "application/json"
        }

        system_message = {
            "role": "system",
            "content": system_instructions
        }

        user_message = {
            "role": "user",
            "content": (
                f"""Create an in-depth career roadmap with multiple branches, steps, and goals from the following prompt. 
                Include different paths (managerial, technical, exploratory) with unique colors while keeping the main path in consistency combined towards the end goal. The steps array must have a minimum of 8 steps, with at least 5 steps dedicated to the #f4b084 path (current path), and additional objects in the steps array for the remaining paths.

                Prompt: {prompt}
                Structure the output in JSON as follows:
                {{
                  "roadmap": {{
                    "branch": {{
                      "color": "#f4b084",  # Main path (current path toward the goal)
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
                              "color": "#a9d08e",  # Exploratory path
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
                              "color": "#ccccff",  # Managerial path
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
                              "color": "#9bc2e6",  # Technical path
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
                        # Add at least 4 or more steps for the main #f4b084 path here
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
                - Separate paths by color: main path (#f4b084), default (#a9d08e), managerial (#ccccff), technical (#9bc2e6).
                - Each branch must contain at least 5+ steps and sub-branches.
                - Ensure each step contains 5+ unique skills.
                - The last step represents reaching the goal of the respective branch.
                - Try your best to avoid all possible errors in the output and json formatting.
                - Property name must be enclosed in double quotes.
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


# def training_steps_generation(previous_response, current_date, model, temperature=0.6):
#     try:
#         url = "https://api.openai.com/v1/chat/completions"
#         headers = {
#             "Authorization": f"Bearer {openai.api_key}",
#             "Content-Type": "application/json"
#         }

#         if not isinstance(previous_response, str):
#             previous_response = json.dumps(previous_response)

#         system_message = {
#             "role": "system",
#             "content": (
#                 "You are an experienced career advisor with a deep understanding of career development training paths. "
#                 "Provide a comprehensive training structure for the given career map, highlighting the key components as requested. "
#                 f"All planning and completion dates should be set in the future. The current date is {current_date}. "
#                 "You must complete all the skill steps outlined in the input career path as part of the skill_gap_analysis."
#                 "Ensure the JSON formatting is valid with property names enclosed in double quotes."
#             )
#         }

#         user_message = {
#             "role": "user",
#             "content": (
#                 f"""Create a detailed training structure for the following career map:
                
#                 Career Map: {previous_response}
                
#                 Structure the output in JSON as follows:
#                 {{
#                     "career_goals_overview": [
#                         {{
#                             "title": "career goal description", # could be short term or long term
#                             "type": "s/l",  # if s then expected to be 6-12 months from the current date.
#                             "completion_date": "YYYY-MM-DD"  
#                         }},
#                         {{
#                             "title": "career goal description", # could be short term or long term
#                             "type": "s/l",   # if l then expected to be 1 to 5 years from the last preceedence date.
#                             "completion_date": "YYYY-MM-DD"  
#                         }}
#                         # Add more career goals if needed.
#                     ],
#                     "skill_gap_analysis": [
#                         {{
#                             "title": "Current Skill Title",
#                             "priority": null, # will always be null in current skills if status is completed, else priority will be 'high'.. (current skills will be in the first step of given input prompt)
#                             "status": "completed",
#                             "resources": null  # will always be null in current skills if status is completed, else resources will be needed (current skills will be in the first step of given input prompt)
#                         }},
#                         {{
#                             "title": "Skill Needed",
#                             "priority": "priority level", # could be high/medium/low as per the need.
#                             "status": "pending",
#                             "resources": [
#                                 {{
#                                     "platform": "Platform Name",
#                                     "resource_title": "Resource Title",
#                                     "link": "https://example.com/resource-link"
#                                 }},
#                                 {{
#                                     "platform": "Platform Name",
#                                     "resource_title": "Resource Title",
#                                     "link": "https://example.com/resource-link"
#                                 }}
#                             ]
#                         }}
#                         "You must complete all the skill steps outlined in the input career path as part of the skill_gap_analysis."
#                     ],
#                     "training_activities": [
#                         {{
#                             "title": "Training Activity Title",
#                             "expected_outcomes": "Outcome Description",
#                             "progress_measurement": "Measurement Method",
#                             "duration": "Duration (e.g., 2 days, 4 weeks)",
#                             "date": "YYYY-MM-DD",
#                             "responsible": "Self"
#                         }}
#                     ],
#                     "career_path_progression_map": {{
#                         "steps": [
#                             {{
#                                 "role": "Current Role Title",
#                                 "suggested_timing": null  #will always be null in current role
#                             }},
#                             {{
#                                 "role": "Next Role Title",
#                                 "suggested_timing": "6 months"  # may vary with the complexity level to handle
#                             }},
#                             {{
#                                 "role": "Advanced Role Title",
#                                 "suggested_timing": "12 months"  # may vary with the complexity level to handle
#                             }}
#                         ]
#                     }},
#                     "action_plan_summary": [
#                         {{
#                             "action": "Action Description",
#                             "responsibility": "Self or Mentor"
#                         }},
#                         {{
#                             "action": "Another Action Description",
#                             "responsibility": "Self or Mentor"
#                         }},
#                         # Add more actions according to need and balance between self and mentor responsibilities.
#                     ],
#                     "next_steps_recommendations": [
#                         "Recommendation 1",
#                         "Recommendation 2",
#                         "Recommendation 3"
#                         # add more if needed
#                     ],
#                     "additional_actions_to_support_career_growth": [
#                         "Recommendations for continuous learning beyond initial training. (Long but valid description)"
#                     ]
#                 }}
                
#                 - Ensure all dates (e.g., YYYY-MM-DD) are in the future, dependant to each other avoiding any conflicts and properly formatted.
#                 - Arrange completion dates sequentially, avoiding any overlap or conflicts with preceding dates.
#                 - Include resources with valid and relevant links for each skill when applicable.
#                 - Learning resource links might be of a book, course, video tutorial, online article, GitHub repository, or any other educational material that is relevant to building the required skills.                
#                 - All of the problem solving and technical skills will be highly prioritized in 'skill_gap_analysis' irrespective of its time.                
#                 - Ensure that JSON formatting is valid with property names enclosed in double quotes.
#                 - Provide a comprehensive breakdown of each section as per the request.
#                 """
#             )
#         }

#         data = {
#             "model": model,
#             "messages": [system_message, user_message],
#             "temperature": temperature
#         }

#         response = requests.post(url, headers=headers, json=data)

#         if response is not None and response.status_code == 200:
#             return response.json()
#         else:
#             logging.error(f"Failed to get a valid response from OpenAI API. Status code: {response.status_code}, Response: {response.text}")
#             return None

#     except requests.exceptions.HTTPError as http_err:
#         logging.error(f"HTTP error occurred: {http_err}")
#     except requests.exceptions.RequestException as req_err:
#         logging.error(f"Request error occurred: {req_err}")
#     except Exception as e:
#         logging.error(f"An unexpected error occurred: {str(e)}")

#     return None


def training_steps_generation(previous_response, current_date, model, temperature=0.6):
    try:
        url = "https://api.openai.com/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {openai.api_key}",
            "Content-Type": "application/json"
        }

        if not isinstance(previous_response, str):
            previous_response = json.dumps(previous_response)

        system_message = {
            "role": "system",
            "content": (
                "You are an experienced career advisor with a deep understanding of career development training paths. "
                "Provide a comprehensive training structure for the given career map, highlighting the key components as requested. "
                f"All planning and completion dates should be set in the future. The current date is {current_date}. "
                "You must complete all the skill steps outlined in the input career path as part of the skill_gap_analysis. "
                "Ensure the JSON formatting is valid with property names enclosed in double quotes."
            )
        }

        user_message = {
            "role": "user",
            "content": (
                f"""Create a detailed training structure for the following career map:
                
                Career Map: {previous_response}
                
                Structure the output in JSON as follows:
                {{
                    "career_goals_overview": [
                        {{
                            "title": "career goal description",  # Could be short-term or long-term goal.
                            "type": "s/l",  # 's' for short-term (6-12 months), 'l' for long-term (1-5 years).
                            "completion_date": "YYYY-MM-DD"  # Date should be in the future.
                        }},
                        {{
                            "title": "career goal description",
                            "type": "s/l",
                            "completion_date": "YYYY-MM-DD"
                        }}
                        # Add more career goals if needed.
                    ],
                    "skill_gap_analysis": [
                        {{
                            "title": "Current Skill Title",
                            "priority": null,  # Null if status is 'completed', otherwise 'high'.
                            "status": "completed",
                            "resources": null  # Null if status is 'completed', otherwise include relevant resources.
                        }},
                        {{
                            "title": "Skill Needed",
                            "priority": "priority level",  # Can be high/medium/low.
                            "status": "pending",
                            "resources": [
                                {{
                                    "platform": "Platform Name",
                                    "resource_title": "Resource Title",
                                    "link": "https://example.com/resource-link"
                                }},
                                {{
                                    "platform": "Platform Name",
                                    "resource_title": "Resource Title",
                                    "link": "https://example.com/resource-link"
                                }}
                            ]
                        }}
                        # Add all required skill steps outlined in the input.
                    ],
                    "training_activities": [
                        {{
                            "title": "Training Activity Title",
                            "expected_outcomes": "Outcome Description",
                            "progress_measurement": "Measurement Method",
                            "duration": "Duration (e.g., 2 days, 4 weeks)",
                            "date": "YYYY-MM-DD",
                            "responsible": "Self"
                        }}
                        # Add more training activities as needed.
                    ],
                    "career_path_progression_map": [
                        {{
                            "role": "Current Role Title",
                            "suggested_timing": null  # Null for the current role.
                        }},
                        {{
                            "role": "Next Role Title",
                            "suggested_timing": "6 months"  # Adjust based on complexity.
                        }},
                        {{
                            "role": "Advanced Role Title",
                            "suggested_timing": "12 months"  # Adjust based on complexity.
                        }}
                        # Add additional roles as necessary.
                    ],
                    "action_plan_summary": [ # If there are pending skills in the current state, add this as a recommendation
                        {{
                            "action": "Action Description",
                            "responsibility": "Self or Mentor"
                        }},
                        {{
                            "action": "Another Action Description",
                            "responsibility": "Self or Mentor"
                        }}
                        # Add more actions as needed, balancing between self and mentor responsibilities (both should have some responsibility).
                    ],
                    "next_steps_recommendations": [ 
                        "Recommendation 1",
                        "Recommendation 2",
                        "Recommendation 3"
                        # Add more if needed.
                    ],
                    "additional_actions_to_support_career_growth": "Recommendations for continuous learning beyond initial training. (Detailed but valid description)."
                    
                }}
                
                - Ensure all dates (e.g., YYYY-MM-DD) are in the future, dependant to each other avoiding any conflicts and properly formatted.
                - Arrange completion dates sequentially, avoiding any overlap or conflicts with preceding dates.
                - Include resources with valid and relevant links for each skill when applicable.
                - Learning resource links might be of a book, course, video tutorial, online article, GitHub repository, or any other educational material that is relevant to building the required skills.                
                - All of the problem solving and technical skills will be highly prioritized in 'skill_gap_analysis' irrespective of its time.                
                - Ensure that JSON formatting is valid with property names enclosed in double quotes.
                - Provide a comprehensive breakdown of each section as per the request.
                """
            )
        }

        data = {
            "model": model,
            "messages": [system_message, user_message],
            "temperature": temperature
        }

        response = requests.post(url, headers=headers, json=data)

        if response is not None and response.status_code == 200:
            return response.json()
        else:
            logging.error(f"Failed to get a valid response from OpenAI API. Status code: {response.status_code}, Response: {response.text}")
            return None

    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
    except requests.exceptions.RequestException as req_err:
        logging.error(f"Request error occurred: {req_err}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}")

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


def road_map_cv(resume_text, model, temperature= 0.6):
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
                "Make sure that while making json Property name must be enclosed in double quotes"
            )
        }

        user_message = {
            "role": "user",
            "content": (
                f"""Create an in-depth career roadmap with multiple branches, steps, and goals from the following prompt. 
                Include different paths (managerial, technical, exploratory) with unique colors while keeping the main path in consistency combined towards the end goal. The steps array must have a minimum of 8 steps, with at least 5 steps dedicated to the #f4b084 path (current path), and additional objects in the steps array for the remaining paths.

                Resume Text: {resume_text}
                Structure the output in JSON as follows:
                {{
                  "roadmap": {{
                    "branch": {{
                      "color": "#f4b084",  # Main path (current path toward the goal)
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
                              "color": "#a9d08e",  # Exploratory path
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
                              "color": "#ccccff",  # Managerial path
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
                              "color": "#9bc2e6",  # Technical path
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
                        # Add at least 4 or more steps for the main #f4b084 path here
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
                - Separate paths by color: main path (#f4b084), default (#a9d08e), managerial (#ccccff), technical (#9bc2e6).
                - Each branch must contain at least 5+ steps and sub-branches.
                - Ensure each step contains 5+ unique skills.
                - The last step represents reaching the goal of the respective branch.
                - Try your best to avoid all possible errors in the output and json formatting.
                - Property name must be enclosed in double quotes
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
    # print(node_server_url)
    URL = f"{node_server_url}/create-path-analyse-notifications/{id}"
    # print(URL)
    headers = {
      'Accept': 'application/json',
      'Content-Type': 'application/json',
      'Authorization': f"Bearer {token}"
    }
    req = requests.post(url=URL,headers=headers)
    if req.status_code == 200:
      # data = json.loads(req.json())
      print(req.json())
    else:
      print("Send Notification Request Failed",req.status_code)
      

def process_roadmap(id, model, token):
    try:
        prompt_file_data = check_prompt_file_db(id)

        prompt = None
        cv = None

        if prompt_file_data[1]:
            cv = f"{cv_path}/{prompt_file_data[1]}"
        else:
            prompt = prompt_file_data[0]

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

            max_retries = 3  
            for attempt in range(max_retries + 1):  
                response_formatted = extract_json_from_content(content)

                if response_formatted:
                    try:
                        response_formatted = update_title(response_formatted)

                        file_path = 'response.json'
                        with open(file_path, 'w') as json_file:
                            json.dump(response_formatted, json_file, indent=4)

                        print(f"Data successfully saved to {file_path}")
                        
                        # response_string = str(response_formatted)
                        # save_response_content(path_id=id, response_content=response_string)
                        # print(f"Response data saved to database table: path_gpt_response")
                        

                        db.insert_road_map(response_formatted, id)
                        logger.info(f"Output saved successfully to db against path_id = {id}.")
                        path_status_analyzed(id)
                        logger.info(f"Status Changed to 'analyzed' against path_id = {id}.")
                        send_notification(token, id)
                        break  

                    except Exception as e:
                        logger.error(f"Error saving JSON to file or database: {str(e)}")
                        path_status_pending(id)
                        return "Error while saving JSON to file or database"
                else:
                    logger.warning(f"Attempt {attempt + 1}: No valid JSON block found in content for ID {id}. Retrying...")
                    if attempt < max_retries:
                        if cv:
                            result = road_map_cv(resume_text, model)
                        else:
                            result = single_prompt(prompt, model)
                        
                        if result:
                            content = result['choices'][0]['message']['content']
                    else:
                        logger.error(f"No valid JSON block found after {max_retries + 1} attempts.")
                        path_status_pending(id)
                        return "No valid JSON block found after multiple attempts."

    except Exception as e:
        logger.error(f"Error in process_roadmap for ID {id}: {str(e)}")
        path_status_pending(id)
        return f"Error in process_generate_roadmap for ID {id}: {str(e)}"
               

def process_regenerate_roadmap(id, model, token):
    try:
        prompt_file_data = check_prompt_file_db(id)

        prompt = None
        cv = None

        if prompt_file_data[1]:
            cv = f"{cv_path}/{prompt_file_data[1]}"
        else:
            prompt = prompt_file_data[0]

        if cv:
            resume_text = extract_text_from_pdf(cv)
            max_retries = 4  
            for attempt in range(max_retries + 1):  
                result = road_map_cv(resume_text, model, temperature=0.35)
                if result:
                    content = result['choices'][0]['message']['content']
                    response_formatted = extract_json_from_content(content)

                    
                    if response_formatted:
                        break  
                    else:
                        logger.warning(f"Attempt {attempt + 1}: No valid JSON block found in content for ID {id}. Retrying road_map_cv...")
                if attempt == max_retries:
                    logger.error(f"No valid JSON block found after {max_retries + 1} attempts with road_map_cv.")
                    path_status_pending(id)
                    return "No valid JSON block found after multiple attempts."
        elif prompt_file_data:
            prompt = prompt_file_data[0] if prompt_file_data[0] else prompt_file_data[1]
            max_retries = 2  
            for attempt in range(max_retries + 1):  
                result = single_prompt(prompt, model, temperature=0.35)
                if result:
                    content = result['choices'][0]['message']['content']
                    response_formatted = extract_json_from_content(content)
                    if response_formatted:
                        break 
                    else:
                        logger.warning(f"Attempt {attempt + 1}: No valid JSON block found in content for ID {id}. Retrying single_prompt...")
                if attempt == max_retries:
                    logger.error(f"No valid JSON block found after {max_retries + 1} attempts with single_prompt.")
                    path_status_pending(id)
                    return "No valid JSON block found after multiple attempts."
        else:
            logger.error(f"No valid CV or prompt found for ID: {id}")
            return

        if response_formatted:
            try:
                response_formatted = update_title(response_formatted)

                file_path = 'response.json'
                with open(file_path, 'w') as json_file:
                    json.dump(response_formatted, json_file, indent=4)
                print(f"Data successfully saved to {file_path}")  

                # response_string = str(response_formatted)
                # save_response_content(path_id=id, response_content=response_string)
                # print(f"Response data saved to database table: path_gpt_response")

                db.insert_road_map(response_formatted, id)
                print("=======================data saved successfully==============================")
                logger.info(f"Output saved successfully to db against path_id = {id}.")
                path_status_analyzed(id)
                logger.info(f"Status Changed to 'analyzed' against path_id = {id}.")
                send_notification(token, id)

            except Exception as e:
                logger.error(f"Error saving JSON to file or database: {str(e)}")
                path_status_pending(id)
                return "Error while saving JSON to file or database"

    except Exception as e:
        logger.error(f"Error in process_regenerate_roadmap for ID {id}: {str(e)}")
        path_status_pending(id)
        return f"Error in process_regenerate_roadmap for ID {id}: {str(e)}"
    
    
def process_training_steps(branch_id, input_content, model, max_retries):
    attempts = 0
    user_data = db.get_data_for_pdf(branch_id)
    
    if user_data['user_id']:
      user_id = user_data["user_id"]
      db.add_plans_count_in_subscription(user_id)
      
    while attempts <= max_retries:
        try:
            current_date = datetime.now()
            current_date_str = current_date.strftime("%Y-%m-%d")
            response = training_steps_generation(previous_response=input_content, current_date=current_date_str, model=model, temperature=0.7)

            if response and 'choices' in response and response['choices']:
                content = response['choices'][0]['message']['content']
                response_formatted = extract_json_from_content(content)
                
                if response_formatted:
                    send_plan_to_admin(branch_id, response_formatted)
                    file_path = 'training_steps.json'
                    with open(file_path, 'w') as json_file:
                        json.dump(response_formatted, json_file, indent=4)
                    print(f"Data successfully saved to {file_path}")
                    break  
            else:
                logger.error("Invalid response structure from OpenAI API.")
      
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {str(e)}")
            attempts += 1
            if attempts > max_retries:
                logger.error("Failed to generate valid response after multiple attempts.")
            db.subtract_plans_count_in_subscription(user_data['user_id'])
            time.sleep(2)    
    
    
@app.route('/ai/generate_roadmap', methods=['POST'])
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
      model = "gpt-4o"
      executor.submit(process_roadmap, id, model,token)  
      return jsonify({'status': True, 'message': response_message}), 200

    except Exception as e:
      logger.error(f"Error in generate_roadmap: {str(e)}")
      return jsonify({'status': False}), 500
    
    
@app.route('/ai/regenerate_roadmap', methods=['POST'])
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


@app.route('/ai/generate_training_steps', methods=['POST'])
def generate_training_steps():
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

        branch_id = request.args.get('branch_id')
        if not branch_id:
            return jsonify({'error': 'ID is required'}), 400

        # response_content = get_response_content(path_id=id)

        # file_path = 'response_content.txt'
        # with open(file_path, 'w') as txt:
        #     json.dump(response_content, txt, indent=4)
        
        all_steps_skills = get_all_steps_and_skills(branch_id)

        if all_steps_skills:
            input_content = json.dumps(all_steps_skills, indent=4)  
            print(input_content)
        else:
            print('No steps found for the given branch.')

        model = "gpt-4o"
        max_retries = 3
        
        executor.submit(process_training_steps, branch_id, input_content, model, max_retries)

        return jsonify({'status': True, 'message': 'Training steps generation has started'})

    except Exception as e:
        logger.error(f"Error in generating training steps: {str(e)}")
        return jsonify({'status': False, 'error': str(e)}), 500
    

if __name__ == "__main__":
  try:
    app.run(debug=True, host='0.0.0.0', threaded=True, port=port)
  except Exception as e:
    print(f"An error occurred: {str(e)}")
