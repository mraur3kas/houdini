from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import requests
import os
import sqlite3
from battlestats import *
from login import *
from member import *
from faction import *



app = Flask(__name__)
app.secret_key = "your_secret_key"  # Replace with a strong secret key for session encryption

TORN_API_URL = "https://api.torn.com/user"
API_KEYS_FILE = "api_keys.txt"  # For saving the last remembered API key
API_LOG_FILE = "api_log.txt"   # For logging all API keys and names

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        api_key = request.form.get("api_key")

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
                name TEXT NOT NULL,                      -- User name
                user_id REAL NOT NULL UNIQUE,            -- User ID
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
            INSERT INTO battlestats (name, user_id, strength, defense, speed, dexterity)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id)
            DO UPDATE SET
                name = excluded.name,
                strength = excluded.strength,
                defense = excluded.defense,
                speed = excluded.speed,
                dexterity = excluded.dexterity,
                last_updated = CURRENT_TIMESTAMP; -- Updates the timestamp
            """
            data = (name,user_id , battle_stats["strength"], battle_stats["defense"], battle_stats["speed"], battle_stats["dexterity"])
            cursor.execute(insert_query, data)
            conn.commit()

            return redirect(url_for("dashboard"))
        else:
            error = "Invalid API key. Please try again."
            return render_template("login.html", error=error)
    return render_template("login.html")

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

@app.route("/faction", methods=["GET"])
def get_faction_data():
    api_key = session.get("api_key")
    if not api_key:
        return jsonify({"error": "API key is required."}), 400

    faction_data = fetch_faction_data(api_key)
    if "error" in faction_data:
        return jsonify({"error": faction_data["error"]}), 500

    return render_template("faction.html", faction=faction_data, error=None)

@app.route("/member_details/<member_id>", methods=["GET"])
def get_member_details(member_id):
    api_key = session.get("api_key")
    if not api_key:
        return jsonify({"error": "API key is required."}), 400

    try:
        api_url = f"https://api.torn.com/user/?key={api_key}&selections=basic&user={member_id}"
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()

        member_details = {
            "status": data.get("status", {}).get("state"),
        }
        return jsonify(member_details)
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500


@app.route('/faction-battle-stats')
def faction_battle_stats():
    # Connect to the SQLite3 database
    conn = sqlite3.connect('battlestats.db')
    cursor = conn.cursor()

    # Fetch all faction members' battle stats
    cursor.execute("SELECT name, strength, defense, speed, dexterity, total FROM battlestats")
    faction_stats = cursor.fetchall()

    # Close the database connection
    conn.close()

    # Render the faction battle stats page
    return render_template('faction-battle-stats.html', faction_stats=faction_stats, int=int)

# Custom Jinja2 filter to convert to integer
@app.template_filter('to_int')
def to_int(value):
    return int(value)



#track-enemy.html shit
# Route for Tracking page
@app.route('/track-enemy', methods=['GET', 'POST'])
def track_enemy():
    if 'api_key' not in session:
        return redirect(url_for('login'))  # Redirect to login if the user is not signed in

    api_key = session['api_key']  # Use the API key from the session

    if request.method == 'POST':
        # Get the faction ID from the form
        faction_id = request.form.get('faction_id')

        # Validate the faction ID
        if not faction_id or not faction_id.isdigit():
            return render_template('track-enemy.html', error="Please enter a valid numeric Faction ID.")

        # Construct the API URL
        url = f"https://api.torn.com/faction/{faction_id}"
        params = {
            'key': api_key,
            'selections': 'basic'  # Only fetch supported data
        }

        # Make the API request
        try:
            response = requests.get(url, params=params)

            # Check HTTP status code
            if response.status_code == 200:
                data = response.json()  # Parse the JSON response

                if 'error' in data:
                    # Handle API errors
                    error_message = data['error']['error']
                    return render_template('track-enemy.html', error=error_message)

                # Process faction data
                faction = {
                    'name': data.get('name', 'Unknown Faction'),
                    'rank': data.get('rank', 'N/A'),
                    'respect': data.get('respect', 'N/A'),
                    'members': []
                }

                # Process faction members
                members = data.get('members', {})
                for member_id, member_data in members.items():
                    faction['members'].append({
                        'id': member_id,  # Use the member_id (key from the API response)
                        'name': member_data.get('name', 'Unknown'),
                        'status': member_data.get('status', {}).get('description', 'N/A'),
                        'last_action': member_data.get('last_action', {}).get('relative', 'N/A'),
                        'position': member_data.get('position', 'N/A'),
                        'status_color': 'green' if member_data.get('status', {}).get('state') == 'Okay' else 'red',
                        'description': member_data.get('status', {}).get('description', 'N/A')
                    })

                # Render the faction data
                return render_template('track-enemy.html', faction=faction)

            else:
                # Handle non-200 HTTP errors
                return render_template(
                    'track-enemy.html',
                    error=f"Failed to fetch data from Torn API. HTTP Status Code: {response.status_code}"
                )

        except requests.exceptions.RequestException as e:
            # Handle request exceptions
            return render_template(
                'track-enemy.html',
                error=f"A network error occurred: {str(e)}"
            )

    # Render the form for GET requests
    return render_template('track-enemy.html')




if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, debug=True)
