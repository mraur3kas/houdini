import requests
def get_past_wars(api_key):
    """Fetch past ranked wars data from the Torn API."""
    url = "https://api.torn.com/faction/"
    params = {"key": api_key, "selections": "rankedwars"}
    try:
        response = requests.get(url, params=params)
        print(f"API Request URL: {response.url}")  # Log request URL
        print(f"Response Status Code: {response.status_code}")  # Log status code

        if response.status_code == 200:
            data = response.json()
            print(f"Ranked Wars Data: {data}")  # Log full response
            return data.get("rankedwars", {})  # Return the rankedwars section or an empty dict
        else:
            print(f"Unexpected Status Code: {response.status_code}")
            print(f"Error Message: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Request Exception: {e}")
    return {}
