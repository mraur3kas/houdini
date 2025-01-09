import aiohttp
import asyncio

async def get_faction_data(api_key):
    """Fetch faction data and include member statuses asynchronously."""
    url = "https://api.torn.com/faction"
    params = {"key": api_key}
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    faction_data = await response.json()
                    
                    # Fetch statuses for all members concurrently
                    member_ids = faction_data.get("members", {}).keys()
                    member_statuses = await fetch_member_statuses(session, api_key, member_ids)
                    
                    # Add statuses to faction data
                    for member_id, status in member_statuses.items():
                        if member_id in faction_data["members"]:
                            faction_data["members"][member_id]["status"] = status
                    
                    return faction_data
                else:
                    print(f"Error fetching faction data: {response.status}")
        except aiohttp.ClientError as e:
            print(f"Request Exception: {e}")
    return None


async def fetch_member_statuses(session, api_key, member_ids):
    """Fetch statuses for multiple members concurrently."""
    member_statuses = {}
    
    async def fetch_status(member_id):
        url = f"https://api.torn.com/user/{member_id}"
        params = {"key": api_key, "selections": "basic"}
        
        try:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    user_data = await response.json()
                    return user_data.get("status", {}).get("description", "Unknown")
                else:
                    print(f"Error fetching member {member_id}: {response.status}")
                    return "Error"
        except aiohttp.ClientError as e:
            print(f"Error fetching member {member_id}: {e}")
            return "Error"
    
    # Create tasks for all members
    tasks = {member_id: asyncio.create_task(fetch_status(member_id)) for member_id in member_ids}
    
    # Gather results
    for member_id, task in tasks.items():
        member_statuses[member_id] = await task
    
    return member_statuses


# Example Usage
# asyncio.run(get_faction_data("<your_api_key>"))