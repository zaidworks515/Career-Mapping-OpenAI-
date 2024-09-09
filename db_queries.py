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


def insert_step(cursor, path_id, branch_no, title, description, is_optional, is_sub_branch, is_goal):
    insert_query = """
    INSERT INTO steps2 (path_id, branch_no, title, description, is_optional, is_sub_branch, is_goal)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(insert_query, (path_id, branch_no, title, description, is_optional, is_sub_branch, is_goal))
    return cursor.lastrowid  # Return the auto-generated step ID

def insert_skill(cursor, step_id, skill):
    insert_query = """
    INSERT INTO skills2 (step_id, skills)
    VALUES (%s, %s)
    """
    cursor.execute(insert_query, (step_id, skill))


def process_steps(cursor, path_id, branch_no, steps, is_sub_branch=False):
    for step_key, step_data in steps.items():
        # Check if the step is optional or a goal
        is_optional = 'optional' in step_key
        is_goal = 'goal' in step_key
        
        # Ensure the step has a "title" and "description" key before proceeding
        title = step_data.get("title", "Unknown Title")  # Default to "Unknown Title" if missing
        description = step_data.get("description", "No description")  # Default to "No description" if missing

        # Insert step data into steps2 table
        step_id = insert_step(
            cursor, 
            path_id, 
            branch_no, 
            title, 
            description, 
            is_optional, 
            is_sub_branch, 
            is_goal
        )

        # Insert skills data into skills2 table if key_skills are available
        key_skills = step_data.get("key_skills", [])
        for skill in key_skills:
            insert_skill(cursor, step_id, skill)

        # Check if the key starts with "sub_branch" to handle sub-branches
        if step_key.startswith("sub_branch"):
            process_steps(cursor, path_id, branch_no, step_data, is_sub_branch=True)


def store_roadmap_in_db(path_id, roadmap_json):
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()

            # Iterate through each branch in the roadmap JSON
            for branch_key, branch_data in roadmap_json["roadmap"].items():
                # Extract the branch number from the key (e.g., branch_1 -> 1)
                branch_no = int(branch_key.split("_")[1])

                # Process all steps within the branch
                process_steps(cursor, path_id, branch_no, branch_data)

            # Commit the transaction
            connection.commit()
            print("Roadmap data inserted successfully.")

        except Error as e:
            print(f"Error: {e}")
            connection.rollback()
        finally:
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
#     try:
#         connection = create_connection()
#         if connection:
#             cursor = connection.cursor()
            
#             cursor.execute('SET FOREIGN_KEY_CHECKS = 0')
            
#             cursor.execute(f'DELETE FROM {table_name}')
            
#             cursor.execute('SET FOREIGN_KEY_CHECKS = 1')
            
#             connection.commit()
#             print(f'Table {table_name} has been reset.')
#     except Exception as e:
#         print(f'An error occurred while resetting the table {table_name}: {e}')
#     finally:
#         if connection:
#             connection.close()

# reset_table('steps2')
# reset_table('skills2')

# print('DONE')
