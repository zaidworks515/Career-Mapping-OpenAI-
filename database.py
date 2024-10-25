import mysql.connector
from config import host, user, password, database


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

    def get_branch_id_by_path_id(self, path_id):
        connection = self.get_connection()
        cursor = connection.cursor()
        try:
            select_query = "SELECT id FROM branch WHERE path_id = %s"
            cursor.execute(select_query, (path_id,))
            result = cursor.fetchall()
            return [row[0] for row in result]
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            return None
        finally:
            cursor.close()
            connection.close()
            
    def get_plan_by_branch_id(self, path_id):
        connection = self.get_connection()
        cursor = connection.cursor()
        try:
            select_query = "SELECT id FROM trainning_plan WHERE branch_id = %s"
            cursor.execute(select_query, (path_id,))
            result = cursor.fetchall()
            return [row[0] for row in result]
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            return None
        finally:
            cursor.close()
            connection.close()
            
    def delete_plan_by_id(self, plan_id):
        connection = self.get_connection()
        cursor = connection.cursor()
        try:
            delete_query = "DELETE FROM trainning_plan WHERE id = %s"
            cursor.execute(delete_query, (plan_id,))
            connection.commit()
            print(f"Row with ID {plan_id} deleted successfully.")
        except mysql.connector.Error as err:
            print(f"Error: {err}")
        finally:
            cursor.close()
            connection.close()
            
    def dynamic_delete(self, table, column, id):
        connection = self.get_connection()
        cursor = connection.cursor()
        try:
            delete_query = f"DELETE FROM {table} WHERE {column} = %s"
            cursor.execute(delete_query, (id,))
            connection.commit()
        except mysql.connector.Error as err:
            print(f"Error: {err}")
        finally:
            cursor.close()
            connection.close()
            
    def get_skill_gap_ids_by_plan(self, plan_id):
        connection = self.get_connection()
        cursor = connection.cursor()
        try:
            select_query = "SELECT id FROM skill_gap_analysis WHERE plan_id = %s"
            cursor.execute(select_query, (plan_id,))
            result = cursor.fetchall()
            return [row[0] for row in result]
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            return None
        finally:
            cursor.close()
            connection.close()
        

    def delete_plan(self, path_id):
        branch_ids = self.get_branch_id_by_path_id(path_id)
        print(branch_ids)
        plan_ids = []
        analysis_ids = []
        for branch_id in branch_ids:
            plans = self.get_plan_by_branch_id(branch_id)
            for plan in plans:
                analysis_id = self.get_skill_gap_ids_by_plan(plan)
                for ana in analysis_id:
                    analysis_ids.append(ana)
                    
                plan_ids.append(plan)
                
        for reid in analysis_ids:
            self.dynamic_delete("skill_gap_analysis_resources", "skill_gap_analysis_id", reid)
            
        for plan in plan_ids:
            self.dynamic_delete("skill_gap_analysis", "plan_id", plan)
            self.dynamic_delete("training_activities", "plan_id", plan)
            self.dynamic_delete("career_path_progression_map", "plan_id", plan)
            self.dynamic_delete("action_plan_summary", "plan_id", plan)
            self.dynamic_delete("next_steps_recommendations", "plan_id", plan)
            self.dynamic_delete("career_goals_overview", "plan_id", plan)
            
        for branch_idds in branch_ids:
            self.dynamic_delete("trainning_plan", "branch_id", branch_idds)

    
    def insert_road_map(self, data, path_id):
        self.delete_plan(path_id)
        self.delete_data_by_path_id(path_id)
        path = self.check_path_exists(path_id)
        if path:
            branch = data.get('roadmap', {}).get('branch', '')
            self.handle_branch(branch, path_id)
            print("roadmap data successfully inserted")
        else:
            print("invalid path id")

    def insert_trainning_plan(self, plan_recommendation, branch_id):
        connection = self.get_connection()
        cursor = connection.cursor()
        try:
            insert_query = "INSERT INTO trainning_plan (plan_recommendation, branch_id) VALUES (%s,%s)"
            cursor.execute(insert_query, (plan_recommendation, branch_id,))
            connection.commit()
            return cursor.lastrowid
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            return None
        finally:
            cursor.close()
            connection.close()

    def insert_career_goals_overview(self, plan_id, title, type, completion_date):
        connection = self.get_connection()
        cursor = connection.cursor()
        try:
            insert_query = "INSERT INTO career_goals_overview (plan_id, title, type, completion_date) VALUES (%s,%s,%s,%s)"
            cursor.execute(insert_query, (plan_id, title, type, completion_date))
            connection.commit()
            return cursor.lastrowid
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            return None
        finally:
            cursor.close()
            connection.close()

    def insert_skill_gap_analysis(self, plan_id, title, priority, status):
        connection = self.get_connection()
        cursor = connection.cursor()
        try:
            insert_query = "INSERT INTO skill_gap_analysis (plan_id, title, priority, status) VALUES (%s,%s,%s,%s)"
            cursor.execute(insert_query, (plan_id, title, priority, status))
            connection.commit()
            return cursor.lastrowid
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            return None
        finally:
            cursor.close()
            connection.close()

    def insert_skill_gap_analysis_resources(self, skill_gap_analysis_id, title, platform, link):
        connection = self.get_connection()
        cursor = connection.cursor()
        try:
            insert_query = "INSERT INTO skill_gap_analysis_resources (skill_gap_analysis_id, title, platform, link) VALUES (%s,%s,%s,%s)"
            cursor.execute(insert_query, (skill_gap_analysis_id, title, platform, link))
            connection.commit()
            return cursor.lastrowid
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            return None
        finally:
            cursor.close()
            connection.close()

    def insert_training_activities(self, plan_id, title, expected_outcomes, progress_measurement, duration, date,
                                   responsible):
        connection = self.get_connection()
        cursor = connection.cursor()
        try:
            insert_query = "INSERT INTO training_activities (plan_id, title, expected_outcomes, progress_measurement, duration, date, responsible) VALUES (%s,%s,%s,%s,%s,%s,%s)"
            cursor.execute(insert_query,
                           (plan_id, title, expected_outcomes, progress_measurement, duration, date, responsible))
            connection.commit()
            return cursor.lastrowid
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            return None
        finally:
            cursor.close()
            connection.close()

    def insert_career_path_progression_map(self, plan_id, role, suggested_timing):
        connection = self.get_connection()
        cursor = connection.cursor()
        try:
            insert_query = "INSERT INTO career_path_progression_map (plan_id, role, suggested_timing) VALUES (%s,%s,%s)"
            cursor.execute(insert_query, (plan_id, role, suggested_timing))
            connection.commit()
            return cursor.lastrowid
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            return None
        finally:
            cursor.close()
            connection.close()

    def insert_action_plan_summary(self, plan_id, action, responsiblity):
        connection = self.get_connection()
        cursor = connection.cursor()
        try:
            insert_query = "INSERT INTO action_plan_summary (plan_id, action, responsiblity) VALUES (%s,%s,%s)"
            cursor.execute(insert_query, (plan_id, action, responsiblity))
            connection.commit()
            return cursor.lastrowid
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            return None
        finally:
            cursor.close()
            connection.close()

    def insert_next_steps_recommendations(self, plan_id, recommendations):
        connection = self.get_connection()
        cursor = connection.cursor()
        try:
            insert_query = "INSERT INTO next_steps_recommendations (plan_id, recommendations) VALUES (%s,%s)"
            cursor.execute(insert_query, (plan_id, recommendations))
            connection.commit()
            return cursor.lastrowid
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            return None
        finally:
            cursor.close()
            connection.close()

    def feed_data(self, data, branch_id):
        additional_actions_to_support_career_growth = data.get("additional_actions_to_support_career_growth", None)
        career_goals_overview = data.get("career_goals_overview", None)
        skill_gap_analysis = data.get("skill_gap_analysis", None)
        training_activities = data.get("training_activities", None)
        career_path_progression_map = data.get("career_path_progression_map", None)
        action_plan_summary = data.get("action_plan_summary", None)
        next_steps_recommendations = data.get("next_steps_recommendations", None)

        if additional_actions_to_support_career_growth:
            # print(additional_actions_to_support_career_growth)
            plan_id = self.insert_trainning_plan(additional_actions_to_support_career_growth, branch_id)
            # print(plan_id)

            # print("=" * 100)
            if career_goals_overview:
                for goal in career_goals_overview:
                    title = goal.get("title", "")
                    type = goal.get("type", "")
                    completion_date = goal.get("completion_date", "")
                    # print(title, type, completion_date)
                    career_goals_overview_id = self.insert_career_goals_overview(plan_id, title, type, completion_date)
            #         print(career_goals_overview_id)
            #         print("-" * 100)

            # print("=" * 100)
            if skill_gap_analysis:
                for skill in skill_gap_analysis:
                    title = skill.get("title", "")
                    priority = skill.get("priority", "")
                    status = skill.get("status", "")
                    resources = skill.get("resources", "")
                    skill_gap_analysis_id = self.insert_skill_gap_analysis(plan_id, title, priority, status)
                    # print(skill_gap_analysis_id)
                    # print(title, priority, status)
                    # print("resource :")
                    if resources:
                        for resource in resources:
                            platform = resource.get("platform", "")
                            resource_title = resource.get("resource_title", "")
                            link = resource.get("link", "")
                            resource_id = self.insert_skill_gap_analysis_resources(skill_gap_analysis_id, title, platform, link)
                            # print(resource_id)
                            # print(platform, resource_title, link)

                    # print("-" * 100)

            # print("=" * 100)
            if training_activities:
                for training in training_activities:
                    title = training.get("title", "")
                    expected_outcomes = training.get("expected_outcomes", "")
                    progress_measurement = training.get("progress_measurement", "")
                    duration = training.get("duration", "")
                    date = training.get("date", "")
                    responsible = training.get("responsible", "")
                    training_activitiy_id = self.insert_training_activities(plan_id, title, expected_outcomes,
                                                                            progress_measurement, duration, date,
                                                                            responsible)
                    # print(training_activitiy_id)
                    # print(title, expected_outcomes, progress_measurement, duration, date, responsible)
                    # print("-" * 100)

            # print("=" * 100)
            if career_path_progression_map:
                for map in career_path_progression_map:
                    role = map.get("role", "")
                    suggested_timing = map.get("suggested_timing", "")
                    career_path_progression_map_id = self.insert_career_path_progression_map(plan_id, role, suggested_timing)
                    # print(career_path_progression_map_id)
                    # print(role, suggested_timing)
                    # print("-" * 100)

            # print("=" * 100)
            if action_plan_summary:
                for summary in action_plan_summary:
                    action = summary.get("action", "")
                    responsibility = summary.get("responsibility", "")
                    summary_id = self.insert_action_plan_summary(plan_id, action, responsibility)
                    # print(summary_id)
                    # print(action, responsibility)
                    # print("-" * 100)

            if next_steps_recommendations:
                for recommendation in next_steps_recommendations:
                    recommendation_id = self.insert_next_steps_recommendations(plan_id, recommendation)
                    # print(recommendation_id)
                    # print(recommendation)
                    # print("-" * 100)


# data = DataBase().delete_plan(2)
# print(data)