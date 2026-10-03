import requests
import os

# Maps functions (not function_tools)
def find_place_from_text(query: str, api_key: str = None) -> str:
    api_key = api_key or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return "Error: Google Maps API key not set."

    url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
    params = {
        "input": query,
        "inputtype": "textquery",
        "fields": "place_id,name,formatted_address,geometry",
        "key": api_key,
    }

    try:
        response = requests.get(url, params=params)
        if response.status_code != 200:
            return f"HTTP error {response.status_code}: {response.reason}"

        data = response.json()

        if data.get("status") != "OK" or not data.get("candidates"):
            return f"Google API error: {data.get('status')} – No match found for '{query}'."

        candidate = data["candidates"][0]
        name = candidate.get("name", "Unknown place")
        address = candidate.get("formatted_address", "No address found")
        location = candidate.get("geometry", {}).get("location", {})
        lat = location.get("lat")
        lng = location.get("lng")

        if lat is None or lng is None:
            return f"Found place but location coordinates are missing."

        return f"{name} — {address} (lat: {lat}, lng: {lng})"

    except Exception as e:
        return f"Unexpected error: {e}"