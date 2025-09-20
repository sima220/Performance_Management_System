import streamlit as st
import backend_pms as be
import pandas as pd
from datetime import datetime
from streamlit_option_menu import option_menu

# --- Streamlit Page Configuration ---
st.set_page_config(
    page_title="Performance Management System",
    page_icon="📈",
    layout="wide"
)

# --- State Management and Login/Logout Logic ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'user_id' not in st.session_state:
    st.session_state['user_id'] = None
if 'username' not in st.session_state:
    st.session_state['username'] = None
if 'role' not in st.session_state:
    st.session_state['role'] = None
if 'refresh_trigger' not in st.session_state:
    st.session_state['refresh_trigger'] = 0

def login_page():
    """Renders the login form."""
    st.title("Login to PMS")
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        with st.form("Login"):
            st.subheader("Login")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit_button = st.form_submit_button("Login")

            if submit_button:
                user_id, role = be.authenticate_user(username, password)
                if user_id:
                    st.session_state['authenticated'] = True
                    st.session_state['user_id'] = user_id
                    st.session_state['username'] = username
                    st.session_state['role'] = role
                    st.success("Logged in successfully!")
                    st.session_state['refresh_trigger'] += 1
                else:
                    st.error("Invalid username or password.")
        st.markdown("---")
        st.info("Don't have an account? Use the sidebar to create one.")

def create_account_page():
    """Renders the create account form."""
    st.title("Create an Account")
    with st.form("Create Account"):
        st.subheader("Create New Account")
        new_username = st.text_input("Username")
        new_email = st.text_input("Email")
        new_password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        role = st.selectbox("Role", ["employee", "manager"])
        create_button = st.form_submit_button("Create Account")

        if create_button:
            if new_password != confirm_password:
                st.error("Passwords do not match.")
            else:
                success, message = be.create_user(new_username, new_password, new_email, role)
                if success:
                    st.success(f"Account created successfully! You can now log in.")
                    st.session_state['refresh_trigger'] += 1
                else:
                    st.error(message)

def logout():
    """Clears session state and logs the user out."""
    st.session_state['authenticated'] = False
    st.session_state['user_id'] = None
    st.session_state['username'] = None
    st.session_state['role'] = None
    st.session_state['refresh_trigger'] += 1
    st.info("You have been logged out.")

# --- Page Contents ---
def dashboard_page():
    """Displays a welcome message and user-specific goals."""
    st.subheader(f"Welcome to the Dashboard, {st.session_state.username}!")
    st.write("Here you can get a quick overview of your performance.")

    if st.session_state['role'] == 'employee':
        st.markdown("#### Your Goals")
        goals_df = be.get_goals_by_employee(st.session_state.user_id)
        if not goals_df.empty:
            st.dataframe(goals_df, use_container_width=True)
        else:
            st.info("You have no goals assigned yet.")
    else: # Manager
        st.markdown("#### Goals for Your Team")
        goals_df = be.get_goals_by_manager(st.session_state.user_id)
        if not goals_df.empty:
            st.dataframe(goals_df, use_container_width=True)
        else:
            st.info("You have no goals assigned to your employees yet.")

def goals_page():
    """Manages goal creation and viewing based on user role."""
    st.subheader("Goals & Progress Tracking")
    
    if st.session_state['role'] == 'manager':
        # Manager can set goals
        st.markdown("### Set a New Goal for an Employee")
        employees = be.get_all_users()
        employees_df = employees[employees['role'] == 'employee']
        
        if employees_df.empty:
            st.warning("No employees available to set goals for. Please create an employee account first.")
        else:
            employee_options = {row['username']: row['user_id'] for _, row in employees_df.iterrows()}
            with st.form("new_goal_form"):
                selected_employee = st.selectbox("Select Employee", list(employee_options.keys()))
                employee_id = employee_options[selected_employee]
                title = st.text_input("Goal Title")
                description = st.text_area("Description")
                due_date = st.date_input("Due Date")
                
                submitted = st.form_submit_button("Set Goal")
                if submitted:
                    if be.create_goal(st.session_state.user_id, employee_id, title, description, due_date):
                        st.success("Goal set successfully!")
                        st.session_state['refresh_trigger'] += 1
                    else:
                        st.error("Failed to set goal.")

        st.markdown("---")
        st.markdown("### Review Employee Goals")
        goals_df = be.get_goals_by_manager(st.session_state.user_id)
        if not goals_df.empty:
            st.dataframe(goals_df, use_container_width=True)
            
            # Form for updating goal status and adding feedback
            st.markdown("---")
            st.markdown("### Update Goal Status & Provide Feedback")
            goal_options = {row['title']: row['goal_id'] for _, row in goals_df.iterrows()}
            with st.form("update_goal_form"):
                selected_goal_title = st.selectbox("Select Goal to Update", list(goal_options.keys()))
                goal_id_to_update = goal_options[selected_goal_title]
                new_status = st.selectbox("New Status", ["Draft", "In Progress", "Completed", "Cancelled"])
                
                feedback_content = st.text_area("Provide Written Feedback")

                submitted_update = st.form_submit_button("Update Goal & Add Feedback")
                if submitted_update:
                    if be.update_goal_status(goal_id_to_update, new_status):
                        st.success(f"Goal '{selected_goal_title}' status updated to '{new_status}'.")
                        if feedback_content:
                            if be.create_feedback(st.session_state.user_id, goal_id_to_update, feedback_content):
                                st.success("Feedback added successfully!")
                                st.session_state['refresh_trigger'] += 1
                            else:
                                st.error("Failed to add feedback.")
                        else:
                            st.session_state['refresh_trigger'] += 1
                    else:
                        st.error("Failed to update goal.")
    
    else: # Employee can only view goals
        st.markdown("### Your Goals & Tasks")
        goals_tasks_df = be.get_employee_goals_and_tasks(st.session_state.user_id)
        
        if not goals_tasks_df.empty:
            # Display goals and their associated tasks
            st.dataframe(goals_tasks_df, use_container_width=True)

            st.markdown("---")
            st.markdown("### Log a New Task for a Goal")
            goal_options = {row['goal_title']: row['goal_id'] for _, row in goals_tasks_df.drop_duplicates(subset=['goal_id']).iterrows()}
            with st.form("new_task_form"):
                selected_goal_title = st.selectbox("Select Goal", list(goal_options.keys()))
                goal_id = goal_options[selected_goal_title]
                task_title = st.text_input("Task Title")
                task_description = st.text_area("Task Description")

                submitted_task = st.form_submit_button("Log Task for Approval")
                if submitted_task:
                    if be.create_task(goal_id, task_title, task_description):
                        st.success("Task logged for manager approval!")
                        st.session_state['refresh_trigger'] += 1
                    else:
                        st.error("Failed to log task.")
        else:
            st.info("You have no goals or tasks to display.")

def feedback_page():
    """Allows managers to review and approve tasks, and view feedback."""
    st.subheader("Feedback & Task Approval")
    
    if st.session_state['role'] == 'manager':
        st.markdown("### Task Approval Queue")
        # Get all goals managed by the current user
        goals_managed_df = be.get_goals_by_manager(st.session_state.user_id)
        if not goals_managed_df.empty:
            # Find all unapproved tasks related to these goals
            tasks_to_approve = pd.DataFrame()
            for goal_id in goals_managed_df['goal_id']:
                tasks_df = be.get_tasks_by_goal(goal_id)
                unapproved_tasks = tasks_df[tasks_df['is_approved'] == False].copy()
                if not unapproved_tasks.empty:
                    unapproved_tasks['goal_title'] = goals_managed_df[goals_managed_df['goal_id'] == goal_id]['title'].iloc[0]
                    tasks_to_approve = pd.concat([tasks_to_approve, unapproved_tasks])
            
            if not tasks_to_approve.empty:
                st.dataframe(tasks_to_approve[['goal_title', 'title', 'description']], use_container_width=True)
                
                with st.form("task_approval_form"):
                    task_options = {row['title']: row['task_id'] for _, row in tasks_to_approve.iterrows()}
                    selected_task_title = st.selectbox("Select Task to Approve", list(task_options.keys()))
                    task_id_to_approve = task_options[selected_task_title]
                    
                    submitted_approval = st.form_submit_button("Approve Selected Task")
                    if submitted_approval:
                        if be.approve_task(task_id_to_approve):
                            st.success(f"Task '{selected_task_title}' approved successfully!")
                            st.session_state['refresh_trigger'] += 1
                        else:
                            st.error("Failed to approve task.")
            else:
                st.info("No tasks awaiting approval.")
        else:
            st.info("You are not managing any goals with pending tasks.")

    st.markdown("---")
    st.markdown("### Review Feedback")
    if st.session_state['role'] == 'employee':
        goals_df = be.get_goals_by_employee(st.session_state.user_id)
        if not goals_df.empty:
            feedback_df = pd.DataFrame()
            for goal_id in goals_df['goal_id']:
                fb = be.get_feedback_by_goal(goal_id)
                feedback_df = pd.concat([feedback_df, fb])
            
            if not feedback_df.empty:
                st.dataframe(feedback_df, use_container_width=True)
            else:
                st.info("No feedback has been provided for your goals yet.")
        else:
            st.info("You have no goals to display feedback for.")
    else: # Manager can see feedback they've provided
        goals_df = be.get_goals_by_manager(st.session_state.user_id)
        if not goals_df.empty:
            feedback_df = pd.DataFrame()
            for goal_id in goals_df['goal_id']:
                fb = be.get_feedback_by_goal(goal_id)
                feedback_df = pd.concat([feedback_df, fb])
            
            if not feedback_df.empty:
                st.dataframe(feedback_df, use_container_width=True)
            else:
                st.info("You have not provided any feedback yet.")


def reporting_page():
    """Provides a clear view of an employee's performance history."""
    st.subheader("Performance Reporting")
    
    if st.session_state['role'] == 'manager':
        employees_df = be.get_all_users()
        employees_df = employees_df[employees_df['role'] == 'employee']
        
        if employees_df.empty:
            st.info("No employee accounts found.")
            return

        employee_options = {row['username']: row['user_id'] for _, row in employees_df.iterrows()}
        selected_employee_name = st.selectbox("Select Employee to View Report", list(employee_options.keys()))
        selected_employee_id = employee_options[selected_employee_name]
    else:
        # Employee can only view their own report
        selected_employee_id = st.session_state.user_id
        selected_employee_name = st.session_state.username
    
    st.markdown(f"#### Performance History for {selected_employee_name}")
    
    goals_df, feedback_df = be.get_employee_performance_history(selected_employee_id)
    
    st.markdown("##### Goals")
    if not goals_df.empty:
        st.dataframe(goals_df, use_container_width=True)
    else:
        st.info("No goals found for this employee.")
    
    st.markdown("##### Feedback")
    if not feedback_df.empty:
        st.dataframe(feedback_df, use_container_width=True)
    else:
        st.info("No feedback found for this employee.")

def business_insights_page():
    """Displays key business insights using data from the database."""
    st.subheader("Business Insights")
    
    insights = be.get_business_insights()
    
    if not insights:
        st.error("Could not retrieve business insights. Please ensure the database is populated with data.")
        return
    
    st.markdown("### Overall Performance Metrics")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(label="Total Goals", value=int(insights['goals']['total_goals']))
    with col2:
        st.metric(label="Completed Goals", value=int(insights['goals']['completed_goals']))
    with col3:
        st.metric(label="In Progress Goals", value=int(insights['goals']['in_progress_goals']))

    st.markdown("---")
    
    st.markdown("### Key Averages & Extremes")
    col4, col5 = st.columns(2)
    
    with col4:
        st.metric(label="Average Days to Due Date", value=f"{insights['goals']['avg_days_to_due']:.2f} days" if insights['goals']['avg_days_to_due'] else "N/A")
        st.metric(label="Average Tasks per Goal", value=f"{insights['avg_tasks']['avg_tasks_per_goal']:.2f}" if insights['avg_tasks']['avg_tasks_per_goal'] else "N/A")
        
    with col5:
        # 🚨 FIX: Convert date objects to strings
        st.metric(label="Earliest Goal Due Date", value=str(insights['min_max_dates']['earliest_due_date']) if insights['min_max_dates']['earliest_due_date'] else "N/A")
        st.metric(label="Latest Goal Due Date", value=str(insights['min_max_dates']['latest_due_date']) if insights['min_max_dates']['latest_due_date'] else "N/A")

    st.markdown("---")
    
    st.markdown("### Top Employee & Recent Activity")
    col6, col7 = st.columns(2)
    
    with col6:
        st.metric(label="Top Performer (by Completed Goals)", value=insights['top_employee']['username'])
    with col7:
        st.metric(label="Completed Goals by Top Performer", value=int(insights['top_employee']['completed_count']))

# --- Main Application Logic ---

def main_app():
    """Main function to run the Streamlit application."""
    st.sidebar.title("Navigation")
    if not st.session_state['authenticated']:
        choice = st.sidebar.radio("Menu", ["Login", "Create Account"])
        if choice == "Login":
            login_page()
        elif choice == "Create Account":
            create_account_page()
    else:
        st.sidebar.title(f"Hello, {st.session_state.username} ({st.session_state.role})")
        with st.sidebar:
            if st.session_state['role'] == 'manager':
                selected_page = option_menu(
                    menu_title="PMS Menu",
                    options=["Dashboard", "Goals", "Feedback", "Reporting", "Business Insights"],
                    icons=["house-fill", "clipboard2-check", "chat-left-text", "file-bar-graph", "pie-chart"],
                    menu_icon="cast"
                )
            else: # Employee
                selected_page = option_menu(
                    menu_title="PMS Menu",
                    options=["Dashboard", "Goals", "Feedback", "Reporting"],
                    icons=["house-fill", "clipboard2-check", "chat-left-text", "file-bar-graph"],
                    menu_icon="cast"
                )
            st.button("Logout", on_click=logout)

        if selected_page == "Dashboard":
            dashboard_page()
        elif selected_page == "Goals":
            goals_page()
        elif selected_page == "Feedback":
            feedback_page()
        elif selected_page == "Reporting":
            reporting_page()
        elif selected_page == "Business Insights" and st.session_state['role'] == 'manager':
            business_insights_page()

# This is the main entry point for the Streamlit app.
# By referencing the refresh_trigger, Streamlit will re-run the script
# whenever the value of this session state variable changes.
if __name__ == "__main__":
    main_app()
    st.session_state['refresh_trigger']