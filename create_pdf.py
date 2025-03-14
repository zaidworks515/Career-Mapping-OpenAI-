from xhtml2pdf import pisa
import json
from database import DataBase
from datetime import datetime
from uuid import uuid4
from smtp import send_email
import os


db = DataBase()

style = """
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Career Development Plan</title>
        <style>
            @page {
                size: A4;
                margin: 10mm;
            }

            body {
                font-family: Arial, sans-serif;
                display: flex;
                flex-direction: column;
                align-items: center;
                margin: 0;
            }

            .main-title {
                font-size: 28px;
                font-weight: bold;
                text-align: center;
                margin-top: 20px;
            }

            .section-title {
                font-size: 20px;
                font-weight: bold;
                width: 100%;
                margin-top: 10px;
                margin-bottom: 10px;
            }

            .info {
                font-size: 14px;
                margin-top: 10px;
                width: 100%;
                text-align: left;
                padding-left: 20px;
            }

            .info-item {
                margin: 0;
            }

            .info-ol {
                padding-left: 20px;
            }

            .info-item-li {
                font-size: 14px;
                padding-left: 20px;
            }

            .info-ul {
                list-style-type: none;
                padding-left: 20px;
            }

            .sub-info-ul {
                padding-left: 40px;
                font-size: 14px;
            }

            .sub-info-li {
                padding-left: 40px;
            }

            a {
                color: blue;
                text-decoration: none;
            }

            a:hover {
                text-decoration: underline;
            }
            
            .resource-ul {
                list-style-type: none;
            }
            
            .signature-container {
                margin-top: 50px;
                
            }

            .signature {
                font-size: 14px;
            }


        </style>
    </head>
"""

def create_pdf(username, email, creation_date, html_data):
    html_content = f'''
    <!DOCTYPE html>
    <html lang="en">
        {style}

        <body>
            <div class="main-title">Career Development Plan</div>
            <div class="section-title">User Information:</div>
            <div class="info">
                <div class="info-item"><strong>User Name:</strong> {username}</div>
                <div class="info-item"><strong>Email:</strong> {email}</div>
                <div class="info-item"><strong>Date of Plan Creation:</strong> {creation_date}</div>
            </div>
            <br/>
            <div class="section-title">Career Goals Overview:</div>
            {html_data.get("career_goals_overview", '')}
            
            <div class="section-title">Skill Gap Analysis:</div>
            <ol class="info-ol">
                {html_data.get("skill_gap_analysis", '')}
            </ol>
            
            <div class="section-title">Training Activities:</div>
            {html_data.get("training_activities", '')}
            
            <div class="section-title">Career Path Progression Map:</div>
            {html_data.get("career_path_progression_map", '')}
            
            <div class="section-title">Action Plan Summary:</div>
            {html_data.get("action_plan_summary", '')}
            
            <div class="section-title">Next Steps Recommendations:</div>
            {html_data.get("next_steps_recommendations", '')}
            <br/>
            
            <div class="section-title">Training Plan:</div>
            {html_data.get("training_plan", '')}
            
            <br/>
            <br/>
            <br/>
            <br/>
            <br/>
            <br/>
            <div class="signature-container">
                <pre class="signature"><strong>User Signature:</strong> _________________              <strong>Supervisor Signature:</strong>_________________</pre>
            </div>
            

        </body>
    </html>
    '''
    # print(html_content)

    def convert_html_to_pdf(html_content, output_path):
        with open(output_path, "wb") as pdf_file:
            pisa_status = pisa.CreatePDF(html_content, dest=pdf_file)
        return pisa_status.err
    
    file_name = f"plan_pdfs/{uuid4()}.pdf"
    result = convert_html_to_pdf(html_content, file_name)

    if result == 0:
        return file_name
    else:
        print("Failed to create PDF.")
        return None


def get_current_date():
    current_date = datetime.now()
    formatted_date = current_date.strftime("%m/%d/%Y")
    return formatted_date

def get_full_type(value):
    if value == "l":
        return "Long Term"
    elif value == "s":
        return "Short Term"
    else:
        return None

def process_plan(username, email, creation_date, data):
    additional_actions_to_support_career_growth = data.get("additional_actions_to_support_career_growth", None)
    career_goals_overview = data.get("career_goals_overview", None)
    skill_gap_analysis = data.get("skill_gap_analysis", None)
    training_activities = data.get("training_activities", None)
    career_path_progression_map = data.get("career_path_progression_map", None)
    action_plan_summary = data.get("action_plan_summary", None)
    next_steps_recommendations = data.get("next_steps_recommendations", None)

    html_data = {}

    if additional_actions_to_support_career_growth:
        html_data["training_plan"] = f"<div class='info'><div class='info-item'>{additional_actions_to_support_career_growth}</div></div>"

        if career_goals_overview:
            career_goals_overview_html = ""
            for goal in career_goals_overview:
                title = goal.get("title", "")
                type = goal.get("type", "")
                full_type = get_full_type(type)
                completion_date = goal.get("completion_date", "")
                html = f"""
                    <div class="info">
                        <div class="info-item"><strong>Title:</strong> {title}</div>
                        <div class="info-item"><strong>Type:</strong> {full_type}</div>
                        <div class="info-item"><strong>Completion Date:</strong> {completion_date}</div>
                    </div>
                    <br/>
                """
                career_goals_overview_html += html
            
            html_data["career_goals_overview"] = career_goals_overview_html

        if skill_gap_analysis:
            skill_gap_analysis_html = ''
            for skill in skill_gap_analysis:
                title = skill.get("title", "")
                priority = skill.get("priority", "")
                status = skill.get("status", "")
                resources = skill.get("resources", None)

                if resources:
                    resource_html = ''
                    for resource in resources:
                        platform = resource.get("platform", "")
                        resource_title = resource.get("resource_title", "")
                        link = resource.get("link", "")
                        html = f"""
                            <li class="sub-info-li"><strong>{title}: </strong></li>
                                <ul class="resource-ul">
                                    <li class="resource-li"><strong>Platform:</strong> {platform}</li>
                                    <li class="resource-li"><strong>Link:</strong> <a href={link}>{link}</a></li>
                                </ul>
                            <br/>

                            """
                        resource_html += html
                        
                    html_skill = f"""
                        <li class="info-item-li"><strong>{title}</strong></li>
                        <ul class="info-ul">
                            <li class="info-item-li"><strong>Priority:</strong> {priority}</li>
                            <li class="info-item-li"><strong>Status:</strong> {status}</li>
                            <li class="info-item-li"><strong>Resources:</strong></li>
                            <ul class="sub-info-ul">
                                {resource_html}
                            </ul>
                        </ul>

                    """
                    
                else:
                    html_skill = f"""
                        <li class="info-item-li"><strong>{title}</strong></li>
                        <ul class="info-ul">
                            <li class="info-item-li"><strong>Priority:</strong> {priority}</li>
                            <li class="info-item-li"><strong>Status:</strong> {status}</li>
                        </ul>
                        <br/>
                    """
                skill_gap_analysis_html += html_skill
            
            html_data["skill_gap_analysis"] = skill_gap_analysis_html

        if training_activities:
            training_activities_html = ''
            for training in training_activities:
                title = training.get("title", "")
                expected_outcomes = training.get("expected_outcomes", "")
                progress_measurement = training.get("progress_measurement", "")
                duration = training.get("duration", "")
                date = training.get("date", "")
                responsible = training.get("responsible", "")
                
                html = f"""
                    <div class="info">
                        <div class="info-item"><strong>Title:</strong> {title}</div>
                        <div class="info-item"><strong>Expected Outcomes:</strong> {expected_outcomes}</div>
                        <div class="info-item"><strong>Progress Measurement:</strong> {progress_measurement}</div>
                        <div class="info-item"><strong>Duration:</strong> {duration}</div>
                        <div class="info-item"><strong>Date:</strong> {date}</div>
                        <div class="info-item"><strong>Responsible:</strong> {responsible}</div>
                    </div>
                    <br/>
                """
                training_activities_html += html
                
            html_data["training_activities"] = training_activities_html
            
        if career_path_progression_map:
            career_path_progression_map_html = ''
            for map in career_path_progression_map:
                role = map.get("role", "")
                suggested_timing = map.get("suggested_timing", "")
                html = f"""
                    <div class="info">
                        <div class="info-item"><strong>Role:</strong> {role}</div>
                        <div class="info-item"><strong>Suggested Timing:</strong> {suggested_timing}</div>
                    </div>
                    <br/>
                """
                career_path_progression_map_html += html
                
            html_data["career_path_progression_map"] = career_path_progression_map_html
                
        if action_plan_summary:
            action_plan_summary_html = ''
            for summary in action_plan_summary:
                action = summary.get("action", "")
                responsibility = summary.get("responsibility", "")
                html = f"""
                        <div class="info">
                            <div class="info-item"><strong>Action:</strong> {action}</div>
                            <div class="info-item"><strong>Responsibility:</strong> {responsibility}</div>
                        </div>
                        <br/>
                    """
                action_plan_summary_html += html
                    
            html_data["action_plan_summary"] = action_plan_summary_html
            
        if next_steps_recommendations:
            next_steps_recommendations_html = ''
            for recommendation in next_steps_recommendations:
                html = f"<div class='info'><div class='info-item'>{recommendation}</div></div>"
                
                next_steps_recommendations_html += html
                
            html_data["next_steps_recommendations"] = next_steps_recommendations_html
                
        path = create_pdf(username, email, creation_date, html_data)
        if path:
            return path
        else:
            return None
        

def send_plan_to_admin(branch_id, data):
    user_data = db.get_data_for_pdf(branch_id)
    if user_data:
        username = user_data['username']
        email = user_data['email']
        user_id = user_data["user_id"]
        creation_date = get_current_date()
        path = process_plan(username, email, creation_date, data)
        if path:
            print("created pdf path: ", path)
            # db.add_plans_count_in_subscription(user_id)
            send_email(username, path)
            os.remove(path)
    else:
        print("invalid branch")
    
# with open('training_steps.json', 'r') as file:
#     data = json.load(file)
    
# send_plan_to_admin(10, data)

# date = get_current_date()
# print(date)