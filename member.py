import requests
def get_member_data(api_key, member_id):
    """Fetch user details from the Torn API."""
    url = f"https://api.torn.com/user/{member_id}"
    params = {"key": api_key, "selections": "personalstats,basic"}
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching member data: {e}")
    return None