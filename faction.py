import requests
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

def fetch_faction_data(api_key):
    api_url = f"https://api.torn.com/faction/?key={api_key}&selections=basic"
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()

        # Extract relevant information
        faction_data = {
            "name": data.get("name"),
            "rank": data.get("rank", {}).get("name"),
            "respect": "{:,}".format(data.get("respect", 0)),
            "members":[
                {
                    "name": member["name"],
                    "status": member["status"]["state"],
                    "description": member["status"]["description"],
                    "last_action": member["last_action"]["status"],
                    "status_color": member["status"]["color"],
                    "position": member["position"]
                }          
            for member_id, member in data.get("members", {}).items()
            ]   
        }
        return faction_data
    except requests.RequestException as e:
        return {"error": str(e)}
