from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import requests
import os
import sqlite3
from battlestats import *
from faction import *
from login import *
from member import *




app = Flask(__name__)
app.secret_key = "your_secret_key"  # Replace with a strong secret key for session encryption

TORN_API_URL = "https://api.torn.com/user"
API_KEYS_FILE = "api_keys.txt"  # For saving the last remembered API key
API_LOG_FILE = "api_log.txt"   # For logging all API keys and names

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        api_key = request.form.get("api_key")
        remember = request.form.get("remember")  # "on" if checked, None if not

        # Validate the API key
        response = validate_api_key(api_key)

        if response and "name" in response:
            name = response["name"]
            user_id = response["player_id"]
            session["logged_in"] = True
            session["user_name"] = name
            session["api_key"] = api_key
            log_api_key_and_name(api_key,name,user_id)
            # Fetch and store battle stats in the session
            battle_stats = get_battle_stats(api_key)
            if battle_stats:
                session["battle_stats"] = battle_stats
            # Insert data
            # Connect to SQLite database
            # Connect to SQLite database
            conn = sqlite3.connect('battlestats.db')
            cursor = conn.cursor()
            create_table_query = """
            CREATE TABLE IF NOT EXISTS battlestats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,    -- Unique identifier
                name    TEXT NOT NULL,                   -- User name
                user_id  REAL NOT NULL,                  -- User ID
                strength REAL NOT NULL,                  -- Strength stat
                defense REAL NOT NULL,                   -- Defense stat
                speed REAL NOT NULL,                     -- Speed stat
                dexterity REAL NOT NULL,                 -- Dexterity stat
                total REAL GENERATED ALWAYS AS (         -- Automatically calculates total stats
                    strength + defense + speed + dexterity
                ) STORED,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP -- Timestamp for last update
            );
            """
            cursor.execute(create_table_query)
            conn.commit()
            insert_query = """
            INSERT INTO battlestats (name,user_id,strength, defense, speed, dexterity)
            VALUES (?, ?, ?, ?, ?, ?);
            """
            data = (name,user_id , battle_stats["strength"], battle_stats["defense"], battle_stats["speed"], battle_stats["dexterity"])
            cursor.execute(insert_query, data)
            conn.commit()

            if remember:
                save_api_key(api_key)  # Save the API key if "Remember" is checked

            return redirect(url_for("dashboard"))
        else:
            error = "Invalid API key. Please try again."
            return render_template("login.html", error=error)

    saved_api_key = get_saved_api_key()
    return render_template("login.html", saved_api_key=saved_api_key)

@app.route("/dashboard")
def dashboard():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    name = session.get("user_name", "Unknown User")
    return render_template("dashboard.html", name=name)

def get_past_wars(api_key):
    """Fetch past wars data from the Torn API."""
    url = "https://api.torn.com/faction/"
    params = {"key": api_key, "selections": "rankedwars"}
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json().get("rankedwars", {})
    except requests.exceptions.RequestException as e:
        print(f"Error fetching past wars: {e}")
    return None

@app.route("/battle-stats")
def battle_stats():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    api_key = session.get("api_key")
    print(f"API Key used for fetching stats: {api_key}")  # Log the API key used
    
    if not api_key:
        return redirect(url_for("login"))

    # Fetch battle stats data
    stats_data = get_battle_stats(api_key)
    print(f"Fetched Battle Stats: {stats_data}")  # Log the fetched stats

    if not stats_data:
        error = "Unable to fetch battle stats data. Please try again later."
        return render_template("battle_stats.html", error=error)

    return render_template("battle_stats.html", stats=stats_data)



@app.route("/faction")
async def faction():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    api_key = session.get("api_key")
    if not api_key:
        return redirect(url_for("login"))

    # Fetch faction data
    faction_data = await get_faction_data(api_key)
    if faction_data is None:
        error = "Unable to fetch faction data. Please try again later."
        return render_template("faction.html", error=error)

    return render_template("faction.html", faction=faction_data)

@app.route("/member/<member_id>")
def member(member_id):
    if not session.get("logged_in"):
        return {"error": "Not logged in"}, 403

    api_key = session.get("api_key")
    if not api_key:
        return {"error": "API key missing"}, 403

    # Fetch member data from the Torn API
    member_data = get_member_data(api_key, member_id)
    if member_data is None:
        return {"error": "Unable to fetch member details"}, 500

    return member_data  # Return as JSON

@app.route("/logout")
def logout():
    session.clear()  # Clear session data
    return redirect(url_for("login"))

@app.route("/past-wars")
def past_wars():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    api_key = session.get("api_key")
    if not api_key:
        return redirect(url_for("login"))

    # Fetch ranked wars data
    wars_data = get_past_wars(api_key)

    if not wars_data:
        error = "No past ranked wars available."
        return render_template("past_wars.html", error=error)

    return render_template("past_wars.html", wars=wars_data)

@app.route('/war-report/<war_id>')
def war_report(war_id):
    api_key = session.get('api_key')  # Retrieve the API key from the session
    url = f"https://api.torn.com/torn/{war_id}?selections=rankedwarreport&key={api_key}"

    try:
        response = requests.get(url)
        response.raise_for_status()
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500




import datetime

@app.template_filter('datetime')
def format_datetime(value):
    try:
        # Use timezone-aware datetime object
        return datetime.datetime.fromtimestamp(value, datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    except (ValueError, TypeError):
        return "N/A"







if __name__ == "__main__":
    app.run(debug=True)
