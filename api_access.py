import requests
import json


# prompt = "I am a python developer and I have done Bachelors in Computer Science from Karachi University and I have 1 year of experience in python and related frameworks and I want to apply for the Mid-level developer who will handle all of the frameworks related to my field"


# """ ========================= JOB DESCRIPTION PROMPT ==========================="""

# prompt = """𝐉𝐨𝐢𝐧 𝐎𝐮𝐫 𝐓𝐞𝐚𝐦! Tassaract Corp Pvt Ltd 𝐢𝐬 𝐇𝐢𝐫𝐢𝐧𝐠 𝐚 𝐆𝐫𝐚𝐩𝐡𝐢𝐜 𝐃𝐞𝐬𝐢𝐠𝐧𝐞𝐫
#                                     Are you a creative thinker with a passion for design? Tassaract Corp Pvt Ltd is looking for a talented Graphic Designer to elevate our brand with creative and impactful designs! 
#                                     Position: Graphic Designer
#                                     Experience Required: Minimum 1 year
#                                     Job Type: Hybrid
#                                     Location: Gulshan-e-Iqbal, Karachi

#                                     𝗞𝗲𝘆 𝗥𝗲𝘀𝗽𝗼𝗻𝘀𝗶𝗯𝗶𝗹𝗶𝘁𝗶𝗲𝘀:
#                                     •Design eye-catching visuals for both digital and print media
#                                     •Collaborate with the team to create engaging content for various platforms
#                                     •Develop creative concepts that align with our brand identity
#                                     •Ensure all designs are consistent with the latest design trends
#                                     •Provide input on design strategies and improve existing designs

#                                     𝗥𝗲𝗾𝘂𝗶𝗿𝗲𝗺𝗲𝗻𝘁𝘀:
#                                     •Strong portfolio showcasing your design skills across different mediums
#                                     •Proficiency in Adobe Creative Suite (Photoshop, Illustrator, InDesign)
#                                     •Experience with UI/UX design is a plus
#                                     •Familiarity with web design tools such as Figma or Sketch
#                                     •Excellent communication and collaboration skills
#                                     •1 year of experience in graphic design

#                                     𝗛𝗼𝘄 𝘁𝗼 𝗔𝗽𝗽𝗹𝘆:
#                                     If you're passionate about design and ready to make an impact, we want to hear from you! Please send your resume and portfolio to 𝗰𝗮𝗿𝗲𝗲𝗿𝘀@𝘁𝗮𝘀𝘀𝗮𝗿𝗮𝗰𝘁.𝗰𝗼𝗺"""



# data = {
#     'user_id': user_id,
#     'prompt': prompt
# }

# response = requests.post('http://127.0.0.1:80/generate_skills', )

"""========================GENERATE ROADMAP======================"""


# id = 1
# response1 = requests.post(f'http://127.0.0.1:5000/generate_roadmap?id={id}')

# if response1.status_code == 200:
#     print("Status:", response1.json().get('status'))
# else:
#     print(f"Failed to get response. Status Code: {response1.status_code}")


id = 2
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOjMwLCJlbWFpbCI6InN5ZWR0YWxoYTcxeEBnbWFpbC5jb20iLCJhdXRoVHlwZSI6InN0YW5kYXJkIiwiaWF0IjoxNzI1NDM0MzY4LCJleHAiOjE3MjU0Mzc5Njh9.zFbw8UQ9UW6BXNPJEgi_HezEN_-8CUiqeKtTq3jF4fE"
response2 = requests.post(f'http://127.0.0.1:5000/generate_roadmap?id={id}&token={token}')

if response2.status_code == 200:
    print("Status:", response2.json().get('status'))
else:
    print(f"Failed to get response. Status Code: {response2.status_code}")


# id = 3
# response3 = requests.post(f'http://127.0.0.1:5000/generate_roadmap?id={id}')

# if response3.status_code == 200:
#     print("Status:", response3.json().get('status'))
# else:
#     print(f"Failed to get response. Status Code: {response3.status_code}")






"""========================RE-GENERATE ROADMAP======================"""

# id = 1
# response = requests.post(f'http://127.0.0.1:5000/regenerate_roadmap?id={id}')

# id = 2
# response = requests.post(f'http://127.0.0.1:5000/regenerate_roadmap?id={id}')

# id = 2
# response = requests.post(f'http://127.0.0.1:5000/regenerate_roadmap?id={id}')



# if response.status_code == 200:
#     print("Status:", response.json().get('status'))
# else:
#     print(f"Failed to get response. Status Code: {response.status_code}")
