import streamlit as st
import db_utils
import auth

# Initialize the database and tables
db_utils.init_db()
db_utils.purge_old_tasks() # Clean up old tasks in recycle bin

st.set_page_config(page_title="To-Do App", page_icon="📝")

# --- Authentication and Session State Management ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.username = None
    st.session_state.page = "login"

def login_success(user_id, username):
    st.session_state.logged_in = True
    st.session_state.user_id = user_id
    st.session_state.username = username
    st.session_state.page = "main"
    st.rerun()

def logout():
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.username = None
    st.session_state.page = "login"
    st.rerun()

# --- Main App Logic ---
if st.session_state.page == "main":
    st.title(f"📝 {st.session_state.username}'s To-Do List")
    
    col_header, col_logout = st.columns([4, 1])
    with col_logout:
        st.button("Logout", on_click=logout)

    # --- To-Do List Management ---
    st.header("My Tasks")
    
    with st.form(key='add_task_form'):
        new_task = st.text_input("New Task")
        add_task_button = st.form_submit_button("Add Task")
    
    if add_task_button and new_task:
        db_utils.add_task(st.session_state.user_id, new_task)
        st.rerun()

    tasks = db_utils.get_tasks(st.session_state.user_id)
    if tasks:
        for task in tasks:
            col1, col2, col3, col4 = st.columns([0.6, 0.15, 0.15, 0.1])
            with col1:
                is_done = task['status'] == 'done'
                checked = st.checkbox(task['description'], value=is_done, key=f"task_{task['id']}", on_change=db_utils.toggle_task_status, args=(task['id'],))
            with col2:
                if st.button("✏️", key=f"edit_{task['id']}"):
                    st.session_state.edit_id = task['id']
                    st.session_state.edit_description = task['description']
                    st.session_state.page = "edit"
                    st.rerun()
            with col3:
                if st.button("🗑️", key=f"delete_{task['id']}"):
                    db_utils.delete_task(task['id'])
                    st.rerun()
            with col4:
                 if is_done:
                    st.markdown("✅")
    else:
        st.info("You have no tasks! Time to add some. 🎉")

    st.markdown("---")
    
    # --- Recycle Bin Section ---
    st.header("Recycle Bin")
    recycle_bin_items = db_utils.get_recycle_bin_items(st.session_state.user_id)
    if recycle_bin_items:
        for item in recycle_bin_items:
            col1, col2, col3 = st.columns([0.6, 0.2, 0.2])
            with col1:
                st.write(f"- {item['description']}")
                st.caption(f"Deleted on: {item['deleted_at']}")
            with col2:
                if st.button("Restore", key=f"restore_{item['id']}"):
                    db_utils.restore_task(item['id'])
                    st.rerun()
            with col3:
                if st.button("Purge", key=f"purge_{item['id']}"):
                    db_utils.purge_task(item['id'])
                    st.rerun()
    else:
        st.info("Recycle bin is empty. 🥳")

# --- Page for Editing a Task ---
elif st.session_state.page == "edit":
    st.title("✏️ Edit Task")
    
    edited_task = st.text_input("Edit Description", value=st.session_state.edit_description)
    
    col_buttons = st.columns(2)
    with col_buttons[0]:
        if st.button("Save Changes"):
            db_utils.update_task(st.session_state.edit_id, edited_task)
            st.session_state.page = "main"
            st.rerun()
    with col_buttons[1]:
        if st.button("Cancel"):
            st.session_state.page = "main"
            st.rerun()

# --- Login and Sign Up Page ---
elif st.session_state.page == "login":
    st.title("Welcome to the To-Do App!")
    st.subheader("Please Login or Sign Up")
    
    login_tab, signup_tab = st.tabs(["Login", "Sign Up"])

    with login_tab:
        with st.form(key='login_form'):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            login_button = st.form_submit_button("Login")

            if login_button:
                user = auth.authenticate_user(username, password)
                if user:
                    login_success(user['id'], user['username'])
                else:
                    st.error("Invalid username or password.")
    
    with signup_tab:
        with st.form(key='signup_form'):
            new_username = st.text_input("New Username")
            new_password = st.text_input("New Password", type="password")
            signup_button = st.form_submit_button("Sign Up")
            
            if signup_button:
                if auth.register_user(new_username, new_password):
                    st.success("Account created successfully! Please log in.")
                else:
                    st.error("Username already exists. Please choose another one.")
