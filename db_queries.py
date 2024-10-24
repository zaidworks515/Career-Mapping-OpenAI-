import mysql.connector
from mysql.connector import Error
from config import host, user, password, database
import pandas as pd
import json

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
    INSERT INTO steps (path_id, branch_no, title, description, is_optional, is_sub_branch, is_goal)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(insert_query, (path_id, branch_no, title, description, is_optional, is_sub_branch, is_goal))
    return cursor.lastrowid  # Return the auto-generated step ID

def insert_skill(cursor, step_id, skill):
    insert_query = """
    INSERT INTO skills (step_id, skills)
    VALUES (%s, %s)
    """
    cursor.execute(insert_query, (step_id, skill))


def process_steps(cursor, path_id, branch_no, steps, is_sub_branch=False):
    for step_key, step_data in steps.items():
        is_optional = 'optional' in step_key
        is_goal = 'goal' in step_key
        
        title = step_data.get("title", "Unknown Title")  # Default to "Unknown Title" if missing
        description = step_data.get("description", "No description")  # Default to "No description" if missing

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

        key_skills = step_data.get("key_skills", [])
        for skill in key_skills:
            insert_skill(cursor, step_id, skill)

        if step_key.startswith("sub_branch"):
            process_steps(cursor, path_id, branch_no, step_data, is_sub_branch=True)


def store_roadmap_in_db(path_id, roadmap_json):
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()

            # Iterate through each branch in the roadmap JSON
            for branch_key, branch_data in roadmap_json["roadmap"].items():
                branch_no = int(branch_key.split("_")[1])

                process_steps(cursor, path_id, branch_no, branch_data)

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
                SET status = 'analysed'
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
                SET status = 'analysing'
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
            
            
def path_status_pending(id):
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute('''
                UPDATE path
                SET status = 'pending'
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


def check_branch(branch_id):
    try:
        connection = create_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)  
            
            cursor.execute('SELECT * FROM branch WHERE id = %s', (branch_id,))
            parent_check = cursor.fetchall()

            branch_origin = None
            
            if parent_check:
                branch_info = parent_check[0]  
                
                branch_origin = branch_info['step_id'] if branch_info['step_id'] else None
                
                print(branch_origin)
            else:
                print(f"No branch found with ID: {branch_id}")
                return pd.DataFrame()  
            
            first_row = None
            if branch_origin:
                cursor.execute('SELECT * FROM steps WHERE id = %s', (branch_origin,))
                first_row = cursor.fetchall()    
            
            cursor.execute('SELECT * FROM steps WHERE branch_id = %s', (branch_id,))
            rows = cursor.fetchall()
            
            df = pd.DataFrame(rows)
            
            if first_row:
                first_row_df = pd.DataFrame(first_row)  
                df = pd.concat([first_row_df, df], ignore_index=True) 
            
            cursor.close()
            connection.close()
            
            return df
    except Exception as e:
        print(f"Error checking branch: {e}")
        return pd.DataFrame()


def check_skills(step_id):
    try:
        connection = create_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)  
            
            cursor.execute('SELECT * FROM skills WHERE step_id = %s', (step_id,))
            rows = cursor.fetchall()
            
            df = pd.DataFrame(rows)
            
            cursor.close()
            connection.close()
            
            return df
    except Exception as e:
        print(f"Error checking skills: {e}")
        return pd.DataFrame() 


def get_all_steps_and_skills(branch_id):
    steps_df = check_branch(branch_id)
    
    if steps_df.empty:
        print("No steps found for the given branch.")
        return None
    
    all_steps_with_skills = []
    
    for _, step_row in steps_df.iterrows():
        step_id = step_row['id']
        step_title = step_row['title']
    
        skills_df = check_skills(step_id)
        
        if not skills_df.empty:
            skill_details = [
                {"name": skill_row['title'], "status": skill_row['status']}
                for _, skill_row in skills_df.iterrows()
            ]
        else:
            skill_details = []
        
        all_steps_with_skills.append({
            'step_title': step_title,
            'skills': skill_details
        })
    
    return all_steps_with_skills






# def save_response_content(path_id, response_content):
#     connection = create_connection()  
#     if connection:
#         try:
#             cursor = connection.cursor()
#             cursor.execute('SELECT id FROM path_gpt_response WHERE path_id = %s', (path_id,))
#             existing_record = cursor.fetchone()
            
#             if existing_record:
#                 cursor.execute('''
#                     UPDATE path_gpt_response
#                     SET response = %s
#                     WHERE path_id = %s
#                 ''', (response_content, path_id))
#                 action = "response updated"
#             else:
#                 cursor.execute('''
#                     INSERT INTO path_gpt_response (path_id, response)
#                     VALUES (%s, %s)
#                 ''', (path_id, response_content))
#                 action = "response inserted"
            
#             connection.commit()
#             return action    
#         except Exception as e:
#             print(f"An error occurred: {e}")
#             connection.rollback()
#             return f"Error: {str(e)}"  
#         finally:
#             cursor.close()  
#             connection.close()  
#     else:
#         return "Error: Unable to create database connection." 


# def get_response_content(path_id):
#     connection = create_connection()  
#     if connection:
#         try:
#             cursor = connection.cursor()
#             cursor.execute('SELECT response FROM path_gpt_response WHERE path_id = %s', (path_id,))
#             result = cursor.fetchone()
#             connection.commit()  
            
#             if result:
#                 return result[0] 
#             else:
#                 return None  
#         except Exception as e:
#             print(f"An error occurred: {e}")
#             connection.rollback()
#             return f"Error: {str(e)}"  
#         finally:
#             cursor.close()  
#             connection.close()  
#     else:
#         return "Error: Unable to create database connection."
        
    

# path_status_pending(3)
# path_status_analyzing(3)


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

# reset_table('steps')
# reset_table('skills')

# print('DONE')
