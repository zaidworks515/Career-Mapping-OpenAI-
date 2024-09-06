import mysql.connector
from mysql.connector import Error
from config import host, user, password, database

def create_connection():
    try:
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        if connection.is_connected():
            print("Connected to MySQL database")
        return connection
    except Error as e:
        print(f"Error: {e}")
        return None
    
    
    
def check_prompt_file_db(id):
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute('SELECT prompt, file FROM path WHERE id = %s', (id,))
        result = cursor.fetchone()
        cursor.close()
        connection.close()
        return result
    return None



def store_roadmap_in_db(path_id, roadmap_json):
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        
        cursor.execute("DELETE FROM skills WHERE step_id IN (SELECT id FROM steps WHERE path_id = %s)", (path_id,))
        cursor.execute("DELETE FROM steps WHERE path_id = %s", (path_id,))
        
        def insert_step(path_id, title, description, sort):
            cursor.execute('''
                INSERT INTO steps (path_id, title, description, sort, status)
                VALUES (%s, %s, %s, %s, 'pending')
            ''', (path_id, title, description, sort))
            return cursor.lastrowid

        def insert_skill(step_id, skill_title, sort):
            cursor.execute('''
                INSERT INTO skills (step_id, title, sort, status)
                VALUES (%s, %s, %s, 'pending')
            ''', (step_id, skill_title, sort))

        sort_step = 1
        last_main_step_sort = 1

        for step_key, step_data in roadmap_json['roadmap'].items():
            title = step_data.get('title', 'No Title')
            description = step_data.get('description', '')

            if 'optional_' in step_key:
                sort = last_main_step_sort
            else:
                sort = sort_step
                last_main_step_sort = sort_step
                sort_step += 1

            step_id = insert_step(path_id, title, description, sort)

            sort_skill = 1
            for skill in step_data.get('key_skills', []):
                insert_skill(step_id, skill, sort_skill)
                sort_skill += 1

        connection.commit()
        cursor.close()
        connection.close()
        

def path_status_analyzed(id):
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute('''
                UPDATE path
                SET status = 'analyzed'
                WHERE id = %s
            ''', (id,))
            connection.commit()  
            return cursor.rowcount  
        except Exception as e:
            print(f"An error occurred: {e}")
            connection.rollback()  
        finally:
            cursor.close()
            connection.close()  


def path_status_analyzing(id):
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute('''
                UPDATE path
                SET status = 'analyzing'
                WHERE id = %s
            ''', (id,))
            connection.commit()  
            return cursor.rowcount  
        except Exception as e:
            print(f"An error occurred: {e}")
            connection.rollback()  
        finally:
            cursor.close()
            connection.close()  




# def insert_path(id, file, color, status, user_id, prompt=None):
    # connection = create_connection()
    # if connection:
    #     cursor = connection.cursor()
    #     cursor.execute('''
    #         INSERT INTO path (id, prompt, file, color, status, user_id)
    #         VALUES (%s, %s, %s, %s, %s, %s)
    #     ''', (id, prompt, file, color, status, user_id))
        
    #     connection.commit()
    #     cursor.close()
    #     connection.close()


# insert_path(1, 'Abdul Basit Arif Resume (1).pdf', 'blue', 'pending', 2)

# prompt ="""𝐉𝐨𝐢𝐧 𝐎𝐮𝐫 𝐓𝐞𝐚𝐦! Tassaract Corp Pvt Ltd 𝐢𝐬 𝐇𝐢𝐫𝐢𝐧𝐠 𝐚 𝐆𝐫𝐚𝐩𝐡𝐢𝐜 𝐃𝐞𝐬𝐢𝐠𝐧𝐞𝐫
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
#                                     If you're passionate about design and ready to make an impact, we want to hear from you! Please send your resume and portfolio to 𝗰𝗮𝗿𝗲𝗲𝗿𝘀@𝘁𝗮𝘀𝘀𝗮𝗿𝗮𝗰𝘁.𝗰𝗼𝗺

#                                     Based on this info write the skills which are required for this role"""

# insert_path(3, None, 'blue', 'pending', 2, prompt= prompt)
           


""" ============================== TABLE RESET QUERIES ==================================="""


# def reset_table(table_name):
#     connection = create_connection()
#     if connection:
#         cursor = connection.cursor()
    
#         cursor.execute(f'''
#         DELETE FROM {table_name}
#         ''')

#         connection.commit()
#         connection.close()


# reset_table('steps')
# reset_table('skills')


# print('DONE')