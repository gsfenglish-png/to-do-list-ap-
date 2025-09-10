import sqlite3
from datetime import datetime, timedelta

DB_NAME = "todo_app.db"
RECYCLE_BIN_RETENTION_DAYS = 10

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row # Allows accessing columns by name
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            description TEXT NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS recycle_bin (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            original_id INTEGER NOT NULL,
            description TEXT NOT NULL,
            deleted_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    conn.commit()
    conn.close()

# --- Task CRUD Operations ---
def add_task(user_id, description):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO tasks (user_id, description, status) VALUES (?, ?, ?)", (user_id, description, "pending"))
    conn.commit()
    conn.close()

def get_tasks(user_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM tasks WHERE user_id = ? ORDER BY id DESC", (user_id,))
    tasks = c.fetchall()
    conn.close()
    return tasks

def update_task(task_id, new_description):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE tasks SET description = ? WHERE id = ?", (new_description, task_id))
    conn.commit()
    conn.close()

def toggle_task_status(task_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT status FROM tasks WHERE id = ?", (task_id,))
    current_status = c.fetchone()['status']
    new_status = "done" if current_status == "pending" else "pending"
    c.execute("UPDATE tasks SET status = ? WHERE id = ?", (new_status, task_id))
    conn.commit()
    conn.close()

def delete_task(task_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    task_info = c.fetchone()
    if task_info:
        # Move to recycle bin
        deleted_at = datetime.now().isoformat()
        c.execute("INSERT INTO recycle_bin (user_id, original_id, description, deleted_at) VALUES (?, ?, ?, ?)",
                  (task_info['user_id'], task_id, task_info['description'], deleted_at))
        # Delete from tasks table
        c.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
    conn.close()

# --- Recycle Bin Operations ---
def get_recycle_bin_items(user_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM recycle_bin WHERE user_id = ? ORDER BY deleted_at DESC", (user_id,))
    items = c.fetchall()
    conn.close()
    return items

def restore_task(original_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM recycle_bin WHERE original_id = ?", (original_id,))
    item = c.fetchone()
    if item:
        c.execute("INSERT INTO tasks (user_id, description, status) VALUES (?, ?, ?)",
                  (item['user_id'], item['description'], "pending"))
        c.execute("DELETE FROM recycle_bin WHERE original_id = ?", (original_id,))
        conn.commit()
    conn.close()

def purge_task(original_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM recycle_bin WHERE original_id = ?", (original_id,))
    conn.commit()
    conn.close()

def purge_old_tasks():
    conn = get_db_connection()
    c = conn.cursor()
    ten_days_ago = (datetime.now() - timedelta(days=RECYCLE_BIN_RETENTION_DAYS)).isoformat()
    c.execute("DELETE FROM recycle_bin WHERE deleted_at < ?", (ten_days_ago,))
    conn.commit()
    conn.close()
