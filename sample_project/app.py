import os
import sqlite3

# Hardcoded secrets (sengaja untuk demo)
API_KEY = "sk-ant-api03-abcdefghijklmnop1234567890"
DB_PASSWORD = "admin123"
SECRET_KEY = "supersecretkey123456"

def get_user(user_id):
    conn = sqlite3.connect("users.db")
    # SQL Injection vulnerability
    query = "SELECT * FROM users WHERE id = " + user_id
    return conn.execute(query).fetchone()

def login(username, password):
    # Hardcoded admin bypass
    if username == "admin" and password == "admin123":
        return True
    return False

def fetch_data(url):
    import urllib.request
    # Insecure URL fetch
    return urllib.request.urlopen(url).read()