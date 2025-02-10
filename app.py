import streamlit as st
import pandas as pd
from utils.auth import (
    authenticate_user, create_user, has_permission,
    Permission, UserRole, initialize_super_admin, approve_user, manage_user_tabs
)
from utils.company_data import get_tab_data, generate_sample_company_data
from utils.models import init_db, get_db, User, Tab, SessionLocal
import os

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'role' not in st.session_state:
    st.session_state.role = None
if 'user_id' not in st.session_state:
    st.session_state.user_id = None

# Initialize database and create root user
try:
    print("Initializing database...")
    init_db()
    print("Database initialized successfully")
    print("Creating super admin...")
    initialize_super_admin()
    print("Super admin created successfully")
    print("Generating sample data...")
    generate_sample_company_data()
    print("Sample data generated successfully")
except Exception as e:
    print(f"Error during initialization: {str(e)}")
    st.error("Error initializing application. Please check the logs.")

# Custom CSS for better styling
st.markdown("""
<style>
    .stTextInput > div > div > input {
        border-radius: 5px;
    }
    .stButton>button {
        border-radius: 5px;
        width: 100%;
    }
    .auth-container {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .metric-container {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 5px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .profile-section {
        padding: 20px;
        background-color: #ffffff;
        border-radius: 10px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

def main():
    st.title("Company Management System")

    if not st.session_state.authenticated:
        tab1, tab2 = st.tabs(["Login", "Register"])

        with tab1:
            st.markdown('<div class="auth-container">', unsafe_allow_html=True)
            st.subheader("Login")
            username_email = st.text_input("Username or Email", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")

            if st.button("Login", key="login_button"):
                success, user = authenticate_user(username_email, password)
                if success and user:
                    st.session_state.authenticated = True
                    st.session_state.username = user.username
                    st.session_state.role = user.role_name
                    st.session_state.user_id = user.id
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid credentials or account not approved")
            st.markdown('</div>', unsafe_allow_html=True)

        with tab2:
            st.markdown('<div class="auth-container">', unsafe_allow_html=True)
            st.subheader("Register")
            new_first_name = st.text_input("First Name", key="register_first_name")
            new_last_name = st.text_input("Last Name", key="register_last_name")
            new_username = st.text_input("Username", key="register_username")
            new_email = st.text_input("Email", key="register_email")
            new_password = st.text_input("Password", type="password", key="register_password")
            confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")

            if st.button("Register", key="register_button"):
                if not all([new_first_name, new_last_name, new_username, new_email, new_password]):
                    st.error("Please fill in all fields!")
                elif new_password != confirm_password:
                    st.error("Passwords do not match!")
                else:
                    success, message = create_user(
                        new_username,
                        new_email,
                        new_password,
                        first_name=new_first_name,
                        last_name=new_last_name
                    )
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
            st.markdown('</div>', unsafe_allow_html=True)

    else:
        # Get current user from a new database session
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == st.session_state.user_id).first()

            if user:
                st.sidebar.title(f"Welcome, {user.first_name}!")

                # Profile Section
                if st.sidebar.checkbox("Show Profile", value=True):
                    st.markdown('<div class="profile-section">', unsafe_allow_html=True)
                    st.subheader("Profile Information")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**First Name:**", user.first_name)
                        st.write("**Last Name:**", user.last_name)
                        st.write("**Username:**", user.username)
                    with col2:
                        st.write("**Email:**", user.email)
                        st.write("**Role:**", user.role_name)
                        st.write("**Last Login:**", user.last_login.strftime("%Y-%m-%d %H:%M:%S") if user.last_login else "Never")
                    st.markdown('</div>', unsafe_allow_html=True)

                # Super Admin Controls
                if user.role_name == UserRole.SUPER_ADMIN.value:
                    with st.sidebar.expander("Admin Controls"):
                        st.subheader("Pending Approvals")
                        pending_users = db.query(User).filter(
                            User.is_approved == False,
                            User.role_name != UserRole.SUPER_ADMIN.value
                        ).all()

                        for pending_user in pending_users:
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.write(f"User: {pending_user.username} ({pending_user.email})")
                            with col2:
                                if st.button("Approve", key=f"approve_{pending_user.id}"):
                                    success, message = approve_user(st.session_state.username, pending_user.id)
                                    if success:
                                        st.success(message)
                                        st.rerun()
                                    else:
                                        st.error(message)

                        st.subheader("Manage Tab Access")
                        user_to_manage = st.selectbox(
                            "Select User",
                            [u.username for u in db.query(User).filter(User.role_name != UserRole.SUPER_ADMIN.value).all()]
                        )
                        if user_to_manage:
                            tabs = db.query(Tab).all()
                            selected_tabs = st.multiselect(
                                "Select Accessible Tabs",
                                [tab.name for tab in tabs],
                                key=f"tabs_{user_to_manage}"
                            )
                            if st.button("Update Access"):
                                manage_user = db.query(User).filter(User.username == user_to_manage).first()
                                success, message = manage_user_tabs(
                                    st.session_state.username,
                                    manage_user.id,
                                    selected_tabs
                                )
                                if success:
                                    st.success(message)
                                else:
                                    st.error(message)

                # Logout button
                if st.sidebar.button("Logout"):
                    st.session_state.authenticated = False
                    st.session_state.username = None
                    st.session_state.role = None
                    st.session_state.user_id = None
                    st.rerun()

                # Display available tabs
                available_tabs = user.accessible_tabs

                if available_tabs:
                    selected_tab = st.selectbox(
                        "Select Dashboard",
                        [tab.name for tab in available_tabs],
                        format_func=lambda x: x.replace('_', ' ').title()
                    )

                    if selected_tab:
                        data, message = get_tab_data(user.username, selected_tab)

                        if data:
                            # Group data by metric name
                            metrics = {}
                            for record in data:
                                if record.metric_name not in metrics:
                                    metrics[record.metric_name] = []
                                metrics[record.metric_name].append({
                                    'date': record.date,
                                    'value': record.value
                                })

                            # Display metrics
                            for metric_name, values in metrics.items():
                                st.subheader(metric_name)
                                df = pd.DataFrame(values)

                                # Display latest value
                                latest_value = values[0]['value']
                                st.metric(
                                    label="Current Value",
                                    value=f"{latest_value:,.2f}"
                                )

                                # Display chart
                                st.line_chart(df.set_index('date')['value'])
                        else:
                            st.error(message)
                else:
                    st.warning("No dashboard access. Please contact the administrator.")
            else:
                st.error("Session expired. Please log in again.")
                st.session_state.authenticated = False
                st.rerun()
        finally:
            db.close()

if __name__ == "__main__":
    main()
