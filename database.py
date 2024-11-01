import mysql.connector
from config import host, user, password, database
import json

class DataBase():
    def get_connection(self):
        connection = mysql.connector.connect(
            host=host,
            database=database,
            user=user,
            password=password,
        )
        return connection

    def insert_branch(self, color, path_id, step_id=None):
        if step_id is not None:
            query = "INSERT INTO branch(id, color, path_id, step_id) VALUES(NULL, %s, %s, %s)"
            val = (color, path_id, step_id)
        else:
            query = "INSERT INTO branch(id, color, path_id) VALUES(NULL, %s, %s)"
            val = (color, path_id)

        connection = self.get_connection()
        cursor = connection.cursor(buffered=True)
        cursor.execute(query, val)
        connection.commit()
        inserted_id = cursor.lastrowid

        cursor.close()
        connection.close()

        print("Record inserted successfully. Inserted ID:", inserted_id)
        return inserted_id

    def insert_step(self, title, description, branch_id, sort, path_id):
        query = "INSERT INTO steps(id, title, description, sort, path_id, branch_id) VALUES(NULL, %s, %s, %s, %s, %s)"
        val = (title, description, sort, path_id, branch_id)

        connection = self.get_connection()
        cursor = connection.cursor(buffered=True)
        cursor.execute(query, val)
        connection.commit()
        inserted_id = cursor.lastrowid

        cursor.close()
        connection.close()

        print("Step inserted successfully. Inserted ID:", inserted_id)
        return inserted_id

    def insert_skill(self, title, sort, step_id):
        query = "INSERT INTO skills(id, title, sort, step_id) VALUES(NULL, %s, %s, %s)"
        val = (title, sort, step_id)

        connection = self.get_connection()
        cursor = connection.cursor(buffered=True)
        cursor.execute(query, val)
        connection.commit()
        inserted_id = cursor.lastrowid

        cursor.close()
        connection.close()

        print("Step inserted successfully. Inserted ID:", inserted_id)
        return inserted_id

    def check_path_exists(self, path_id):
        connection = self.get_connection()
        cursor = connection.cursor(buffered=True)
        try:
            query = "SELECT COUNT(*) FROM path WHERE id = %s"
            cursor.execute(query, (path_id,))
            result = cursor.fetchone()

            if result[0] > 0:
                print(f"Path with id {path_id} exists.")
                return True
            else:
                print(f"Path with id {path_id} does not exist.")
                return False

        except mysql.connector.Error as err:
            print("Error: ", err)
            return False
        finally:
            cursor.close()
            connection.close()

    def delete_data_by_path_id(self, path_id):
        connection = self.get_connection()
        cursor = connection.cursor(buffered=True)

        try:
            query_get_ids = "SELECT id, branch_id FROM steps WHERE path_id = %s"
            cursor.execute(query_get_ids, (path_id,))
            steps = cursor.fetchall()

            if not steps:
                print(f"No steps found with path_id {path_id}.")
                return

            step_ids = [step[0] for step in steps]
            branch_ids = set(step[1] for step in steps if step[1] is not None)

            if step_ids:
                query_delete_skills = "DELETE FROM skills WHERE step_id IN (%s)" % ','.join(['%s'] * len(step_ids))
                cursor.execute(query_delete_skills, tuple(step_ids))
                skills_deleted = cursor.rowcount
                print(f"Deleted {skills_deleted} skills with step_ids {step_ids}")

            if branch_ids:
                query_delete_branches = "DELETE FROM branch WHERE id IN (%s)" % ','.join(['%s'] * len(branch_ids))
                cursor.execute(query_delete_branches, tuple(branch_ids))
                branches_deleted = cursor.rowcount
                print(f"Deleted {branches_deleted} branches with branch_ids {branch_ids}")

            query_delete_steps = "DELETE FROM steps WHERE path_id = %s"
            cursor.execute(query_delete_steps, (path_id,))
            steps_deleted = cursor.rowcount
            print(f"Deleted {steps_deleted} steps with path_id {path_id}")

            connection.commit()

        except mysql.connector.Error as err:
            print("Error: ", err)
            connection.rollback()

        finally:
            cursor.close()
            connection.close()
        connection = self.get_connection()
        cursor = connection.cursor(buffered=True)

        try:
            query_delete_steps = "DELETE FROM steps WHERE path_id = %s"
            cursor.execute(query_delete_steps, (path_id,))
            steps_deleted = cursor.rowcount
            print(f"Deleted {steps_deleted} steps with path_id {path_id}")

            query_delete_branches = """
                DELETE b FROM branch b
                WHERE b.step_id IN (SELECT s.id FROM steps s WHERE s.path_id = %s)
            """
            cursor.execute(query_delete_branches, (path_id,))
            branches_deleted = cursor.rowcount
            print(f"Deleted {branches_deleted} branches associated with steps having path_id {path_id}")

            connection.commit()

        except mysql.connector.Error as err:
            print("Error: ", err)
            connection.rollback()

        finally:
            cursor.close()
            connection.close()

    def handle_branch(self, branch, path_id, step_id=None):
        color = branch.get('color', '')
        steps = branch.get('steps', [])
        branch_id = self.insert_branch(color, path_id, step_id)
        print(f"Branch ID: {branch_id}, Color: {color}")
        self.handle_steps(steps, branch_id, path_id)

    def handle_steps(self, steps, branch_id, path_id):
        for index, step in enumerate(steps):
            sort = index + 1
            title = step.get('title', '')
            description = step.get('description', '')
            print(f"Step Title: {title}, Description: {description}")
            print(sort)
            step_id = self.insert_step(title, description, branch_id, sort, path_id)
            print(f"Step ID: {step_id}")

            skills = step.get('skills', [])
            for index, skill in enumerate(skills):
                skill_sort = index + 1
                skill_title = skill.get('title', '')
                print(f"Skill: {skill_title}")
                self.insert_skill(skill_title, skill_sort, step_id)

            branches = step.get('branches', [])
            for branch in branches:
                self.handle_branch(branch, path_id, step_id)

    def insert_road_map(self, data, path_id):
        self.delete_data_by_path_id(path_id)
        path = self.check_path_exists(path_id)
        if path:
            branch = data.get('roadmap', {}).get('branch', '')
            self.handle_branch(branch, path_id)
            print("roadmap data successfully inserted")
        else:
            print("invalid path id")

    def get_data_for_pdf(self, branch_id):
        connection = self.get_connection()
        cursor = connection.cursor()
        try:
            query = """
            SELECT u.username, u.email
            FROM branch AS b
            JOIN path AS p ON b.path_id = p.id
            JOIN users AS u ON u.id = p.user_id
            WHERE b.id = %s;
            """
            
            cursor.execute(query, (branch_id,))
            
            result = cursor.fetchone()
            if result:
                data = {
                    "username": result[0],
                    "email": result[1]
                }
                return data
            
            else:
                return None
            
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            return None
        finally:
            cursor.close()
            connection.close()


# with open('training_steps.json', 'r') as file:
#     data = json.load(file)
    
# data = DataBase().get_data_for_pdf(2)
# print(data)
