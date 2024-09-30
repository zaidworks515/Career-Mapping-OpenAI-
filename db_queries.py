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
                SET status = 'analyse'
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
