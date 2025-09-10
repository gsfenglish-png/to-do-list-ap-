import sqlite3
import bcrypt
import db_utils # To use the database connection function

def register_user(username, password):
    conn = db_utils.get_db_connection()
    c = conn.cursor()
    
    # Check if username already exists
    c.execute("SELECT id FROM users WHERE username = ?", (username,))
    if c.fetchone():
        conn.close()
        return False
        
    # Hash the password
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
    conn.commit()
    conn.close()
    return True

def authenticate_user(username, password):
    conn = db_utils.get_db_connection()
    c = conn.cursor()
    
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    conn.close()
    
    if user:
        # Compare the entered password with the stored hash
        if bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            return user
            
    return None
