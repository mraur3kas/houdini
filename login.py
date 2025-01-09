import requests
import os
import sqlite3
TORN_API_URL = "https://api.torn.com/user"
API_KEYS_FILE = "api_keys.txt"  # For saving the last remembered API key
API_LOG_FILE = "api_log.txt"   # For logging all API keys and names

def get_saved_api_key():
    """Retrieve the saved API key from the file, if it exists."""
    if os.path.exists(API_KEYS_FILE):
        with open(API_KEYS_FILE, "r") as file:
            return file.read().strip()
    return None

def validate_api_key(api_key):
    """Validate the Torn API key by making a request to the Torn API."""
    params = {"key": api_key}
    try:
        response = requests.get(TORN_API_URL, params=params)
        if response.status_code == 200:
            print(response.json())
            return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error validating API key: {e}")
    return None

def save_api_key(api_key):
    """Save the last remembered API key to a file."""
    with open(API_KEYS_FILE, "w") as file:
        file.write(api_key)

def log_api_key_and_name(api_key, name, user_id):
    """Log the API key and the name of the user to a log file."""
    with open(API_LOG_FILE, "a") as file:
        file.write(f"{name}: {api_key}\n")


    # SQL query to create the api_keys table
    conn = sqlite3.connect('battlestats.db')
    cursor = conn.cursor()
    create_api_keys_table_query = """
    CREATE TABLE IF NOT EXISTS api_keys (
        id INTEGER PRIMARY KEY AUTOINCREMENT,    -- Unique identifier
        api_key TEXT NOT NULL UNIQUE,            -- API key
        user_id INTEGER NOT NULL,                -- Associated user ID
        name    TEXT NOT NULL UNIQUE,            -- Player name
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP -- Creation timestamp
    );
    """

    # Execute the query to create the api_keys table
    cursor.execute(create_api_keys_table_query)

    # Commit changes and close the connection
    conn.commit()
    insert_query = """
    INSERT OR IGNORE INTO api_keys (api_key,user_id,name)
    VALUES (?, ?, ?);
    """
    data = (api_key,user_id,name)
    cursor.execute(insert_query, data)
    conn.commit()
    conn.close()