import requests
def get_battle_stats(api_key):
    """Fetch battle stats data from the Torn API."""
    url = "https://api.torn.com/user/"
    params = {"key": api_key, "selections": "battlestats"}
    
    try:
        response = requests.get(url, params=params)
        print(f"Request URL: {response.url}")  # Log full URL of the API request
        print(f"Response Status Code: {response.status_code}")  # Log status code of the response
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response JSON Data: {data}")  # Log the full API response
            
            if "strength" in data:
                return data
            else:
                print(f"Error: 'battlestats' not found in response: {data}")
        else:
            print(f"Error: Unexpected status code {response.status_code} - {response.text}")
    
    except requests.exceptions.RequestException as e:
        print(f"Request Exception: {e}")
    
    return None