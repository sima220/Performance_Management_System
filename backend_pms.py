import psycopg2
import bcrypt
import pandas as pd
import json
from datetime import datetime, date, timedelta
import random

# Database Connection Details
DB_HOST = "localhost"
DB_NAME = "pms_db"
DB_USER = "postgres"
DB_PASSWORD = "seemaxime@30190" # 🚨 IMPORTANT: Replace this with your actual PostgreSQL password

def get_db_connection():
    """Establishes and returns a new database connection."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except psycopg2.Error as e:
        print(f"Database connection failed: {e}")
        return None

# --- User Management (CRUD) ---

def create_user(username, password, email, role):
    """Creates a new user with a hashed password."""
    conn = get_db_connection()
    if conn is None: return False, "Database connection failed."
    
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users (username, password_hash, email, role) VALUES (%s, %s, %s, %s);",
                (username, hashed_password, email, role)
            )
            conn.commit()
            return True, "User created successfully."
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return False, "Username or email already exists."
    except Exception as e:
        conn.rollback()
        print(f"Error creating user: {e}")
        return False, f"An error occurred: {e}"
    finally:
        conn.close()

def authenticate_user(username, password):
    """Authenticates a user and returns their user_id and role if successful."""
    conn = get_db_connection()
    if conn is None: return None, None
    
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT user_id, password_hash, role FROM users WHERE username = %s;", (username,))
            result = cur.fetchone()
            if result:
                user_id, hashed_password, role = result
                if bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8')):
                    return user_id, role
    except Exception as e:
        print(f"Authentication error: {e}")
    finally:
        conn.close()
    return None, None

def get_all_users():
    """Retrieves all users with their roles."""
    conn = get_db_connection()
    if conn is None: return pd.DataFrame()
    query = "SELECT user_id, username, email, role FROM users ORDER BY username ASC;"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# --- Goal Setting & Tracking (CRUD) ---

def create_goal(manager_id, employee_id, title, description, due_date, status='Draft'):
    """Creates a new goal for an employee."""
    conn = get_db_connection()
    if conn is None: return False
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO goals (manager_id, employee_id, title, description, due_date, status) VALUES (%s, %s, %s, %s, %s, %s);",
                (manager_id, employee_id, title, description, due_date, status)
            )
            conn.commit()
            return True
    except Exception as e:
        conn.rollback()
        print(f"Error creating goal: {e}")
        return False
    finally:
        conn.close()

def get_goals_by_employee(employee_id):
    """Retrieves all goals for a specific employee."""
    conn = get_db_connection()
    if conn is None: return pd.DataFrame()
    query = """
    SELECT g.goal_id, g.title, g.description, g.due_date, g.status, u.username as manager_name
    FROM goals g
    JOIN users u ON g.manager_id = u.user_id
    WHERE g.employee_id = %s
    ORDER BY g.due_date ASC;
    """
    df = pd.read_sql(query, conn, params=(employee_id,))
    conn.close()
    return df

def get_goals_by_manager(manager_id):
    """Retrieves all goals managed by a specific manager."""
    conn = get_db_connection()
    if conn is None: return pd.DataFrame()
    query = """
    SELECT g.goal_id, g.title, g.description, g.due_date, g.status, u.username as employee_name
    FROM goals g
    JOIN users u ON g.employee_id = u.user_id
    WHERE g.manager_id = %s
    ORDER BY g.due_date ASC;
    """
    df = pd.read_sql(query, conn, params=(manager_id,))
    conn.close()
    return df

def update_goal_status(goal_id, status):
    """Updates the status of a goal."""
    conn = get_db_connection()
    if conn is None: return False
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE goals SET status = %s WHERE goal_id = %s;",
                (status, goal_id)
            )
            conn.commit()
            return True
    except Exception as e:
        conn.rollback()
        print(f"Error updating goal status: {e}")
        return False
    finally:
        conn.close()

# --- Task Logging (CRUD) ---

def create_task(goal_id, title, description):
    """Creates a new task for a goal."""
    conn = get_db_connection()
    if conn is None: return False
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO tasks (goal_id, title, description) VALUES (%s, %s, %s);",
                (goal_id, title, description)
            )
            conn.commit()
            return True
    except Exception as e:
        conn.rollback()
        print(f"Error creating task: {e}")
        return False
    finally:
        conn.close()

def get_tasks_by_goal(goal_id):
    """Retrieves all tasks for a specific goal."""
    conn = get_db_connection()
    if conn is None: return pd.DataFrame()
    query = "SELECT task_id, title, description, is_approved FROM tasks WHERE goal_id = %s ORDER BY created_at ASC;"
    df = pd.read_sql(query, conn, params=(goal_id,))
    conn.close()
    return df

def approve_task(task_id):
    """Approves a task."""
    conn = get_db_connection()
    if conn is None: return False
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE tasks SET is_approved = TRUE WHERE task_id = %s;",
                (task_id,)
            )
            conn.commit()
            return True
    except Exception as e:
        conn.rollback()
        print(f"Error approving task: {e}")
        return False
    finally:
        conn.close()

# --- Feedback (CRUD) ---

def create_feedback(manager_id, goal_id, content):
    """Creates new feedback for a goal."""
    conn = get_db_connection()
    if conn is None: return False
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO feedback (manager_id, goal_id, content) VALUES (%s, %s, %s);",
                (manager_id, goal_id, content)
            )
            conn.commit()
            return True
    except Exception as e:
        conn.rollback()
        print(f"Error creating feedback: {e}")
        return False
    finally:
        conn.close()

def get_feedback_by_goal(goal_id):
    """Retrieves all feedback for a specific goal."""
    conn = get_db_connection()
    if conn is None: return pd.DataFrame()
    query = """
    SELECT f.content, f.created_at, u.username as manager_name
    FROM feedback f
    JOIN users u ON f.manager_id = u.user_id
    WHERE f.goal_id = %s
    ORDER BY f.created_at DESC;
    """
    df = pd.read_sql(query, conn, params=(goal_id,))
    conn.close()
    return df

# --- Business Insights ---

def get_business_insights():
    """Provides key performance insights using aggregation functions."""
    conn = get_db_connection()
    if conn is None: return {}
    
    insights = {}
    try:
        # Total number of goals and average days to due date
        query_total_goals = """
        SELECT
            COUNT(*) as total_goals,
            AVG(due_date - created_at::DATE) as avg_days_to_due,
            SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as completed_goals,
            SUM(CASE WHEN status = 'In Progress' THEN 1 ELSE 0 END) as in_progress_goals,
            SUM(CASE WHEN status = 'Cancelled' THEN 1 ELSE 0 END) as cancelled_goals
        FROM goals;
        """
        df_goals = pd.read_sql(query_total_goals, conn)
        insights['goals'] = df_goals.iloc[0].to_dict()

        # Employee with the most completed goals
        query_top_employee = """
        SELECT
            u.username,
            COUNT(g.goal_id) AS completed_count
        FROM goals g
        JOIN users u ON g.employee_id = u.user_id
        WHERE g.status = 'Completed' AND u.role = 'employee'
        GROUP BY u.username
        ORDER BY completed_count DESC
        LIMIT 1;
        """
        df_top_employee = pd.read_sql(query_top_employee, conn)
        insights['top_employee'] = df_top_employee.iloc[0].to_dict() if not df_top_employee.empty else {"username": "N/A", "completed_count": 0}

        # Average number of tasks per goal
        query_avg_tasks = """
        SELECT
            AVG(task_count) AS avg_tasks_per_goal
        FROM (
            SELECT
                goal_id,
                COUNT(task_id) AS task_count
            FROM tasks
            GROUP BY goal_id
        ) AS task_counts;
        """
        df_avg_tasks = pd.read_sql(query_avg_tasks, conn)
        insights['avg_tasks'] = df_avg_tasks.iloc[0].to_dict()

        # Min and Max due dates for goals
        query_min_max_dates = """
        SELECT MIN(due_date) as earliest_due_date, MAX(due_date) as latest_due_date FROM goals;
        """
        df_min_max_dates = pd.read_sql(query_min_max_dates, conn)
        insights['min_max_dates'] = df_min_max_dates.iloc[0].to_dict()

    except Exception as e:
        print(f"Error fetching business insights: {e}")
        return {}
    finally:
        conn.close()
    
    return insights

# --- Reporting ---
def get_employee_performance_history(employee_id):
    """Retrieves all goals and associated feedback for an employee."""
    conn = get_db_connection()
    if conn is None: return pd.DataFrame(), pd.DataFrame()

    goals_query = """
    SELECT
        g.goal_id,
        g.title,
        g.description,
        g.due_date,
        g.status,
        u.username as manager_name
    FROM goals g
    JOIN users u ON g.manager_id = u.user_id
    WHERE g.employee_id = %s
    ORDER BY g.due_date ASC;
    """
    goals_df = pd.read_sql(goals_query, conn, params=(employee_id,))

    feedback_query = """
    SELECT
        f.feedback_id,
        f.content,
        f.created_at,
        g.title as goal_title,
        u.username as manager_name
    FROM feedback f
    JOIN goals g ON f.goal_id = g.goal_id
    JOIN users u ON f.manager_id = u.user_id
    WHERE g.employee_id = %s
    ORDER BY f.created_at DESC;
    """
    feedback_df = pd.read_sql(feedback_query, conn, params=(employee_id,))

    conn.close()
    return goals_df, feedback_df

def get_employee_goals_and_tasks(employee_id):
    """Retrieves goals and their tasks for a specific employee."""
    conn = get_db_connection()
    if conn is None: return pd.DataFrame()
    
    query = """
    SELECT
        g.goal_id,
        g.title as goal_title,
        g.description as goal_description,
        g.due_date,
        g.status,
        t.task_id,
        t.title as task_title,
        t.description as task_description,
        t.is_approved
    FROM goals g
    LEFT JOIN tasks t ON g.goal_id = t.goal_id
    WHERE g.employee_id = %s
    ORDER BY g.due_date, t.created_at;
    """
    df = pd.read_sql(query, conn, params=(employee_id,))
    conn.close()
    return df