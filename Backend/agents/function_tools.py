import logging
from livekit.agents import function_tool, RunContext, get_job_context
import base64
from email.mime.text import MIMEText
from datetime import datetime
import os
from text_message import send_text_message, auto_send_email
from typing import List, Dict


@function_tool()
async def start_google_maps() -> str:
    """
    Opens the Google Maps app on the user's device.
    
    :return: Status of the broadcast
    """
    print("\n[start_google_maps]\n")
    
    context = get_job_context()

    try:
        text = 'open_maps'
        info = await context.room.local_participant.send_text(text,topic='my-topic')
        print(f"Sent text with stream ID: {info.stream_id}")
        return f"Sent text with stream ID: {info.stream_id}"
    except Exception as error:
        print(f"Failed to send to frontend: {error}")
        return f"Failed to send to frontend: {error}"

from services.gmail_service import get_gmail_service
from agents.tools import find_place_from_text
from agents.location_manager import location_manager
from agents.invoice_tools import INVOICE_TOOLS
import requests
import os
import re
import json

# General Gmail stuff
@function_tool()
async def get_user_id(context: RunContext) -> str:
    """
    Gets the current user's Gmail userId (email address) using the Gmail API.
    :param service: An authorized Gmail API service instance.
    :return: The user's email address.
    """
    print("\n[get_user_id]\n")
    try:
        service = get_gmail_service()
        if service is None:
            return "Authentication failed. Please re-authenticate Gmail."
        profile = service.users().getProfile(userId='me').execute()
        email = profile.get("emailAddress")
        if email:
            logging.info(f"Retrieved user email: {email}")
            return email
        else:
            logging.error("Email address not found in profile.")
            return "Email address not found."
    except Exception as error:
        logging.error(f"Error retrieving user profile: {error}")
        return f"Error retrieving user profile: {error}"

# Message Gmail stuff
@function_tool()
async def send_gmail_message(context: RunContext, to: str, subject: str, message_text: str) -> str:
    """
    Creates and sends an email message using the Gmail API.

    :param service: An authorized Gmail API service instance.
    :param to: The recipient's email address.
    :param subject: The subject of the email.
    :param message_text: The plain text content of the email.
    :return: The ID of the sent message or an error message.
    """
    print("\n[send_gmail_message]\n")
    try:
        service = get_gmail_service()
        if service is None:
            return "Authentication failed. Please re-authenticate Gmail."
        # Create the email
        message = MIMEText(message_text)
        message['to'] = to
        message['from'] = 'me'
        message['subject'] = subject
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        # Send the email
        sent_message = service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()

        message_id = sent_message.get('id')
        logging.info(f"Email sent successfully. Message ID: {message_id}")
        return message_id
    except Exception as error:
        logging.error(f"Failed to send email: {error}")
        return f"Failed to send email: {error}"
    
@function_tool()
async def delete_gmail_message(context: RunContext, message_id: str) -> str:
    """
    Deletes an email message using the Gmail API.

    :param service: An authorized Gmail API service instance.
    :param message_id: The ID of the email message to delete.
    :return: Success message or error message.
    """
    print("\n[delete_gmail_message]\n")
    try:
        service = get_gmail_service()
        if service is None:
            return "Authentication failed. Please re-authenticate Gmail."
        service.users().messages().delete(userId='me', id=message_id).execute()
        logging.info(f"Deleted message with ID: {message_id}")
        return f"Message with ID {message_id} deleted successfully."
    except Exception as error:
        logging.error(f"Failed to delete message: {error}")
        return f"Failed to delete message: {error}"

# Draft Gmail stuff
@function_tool()
async def create_gmail_draft(context: RunContext, to: str, subject: str, message_text: str) -> str:
    """
    Creates an email draft using the Gmail API.

    :param service: An authorized Gmail API service instance.
    :param to: The recipient's email address.
    :param subject: The subject of the email.
    :param message_text: The plain text content of the email.
    :return: The ID of the created draft or an error message.
    """
    print("\n[create_gmail_draft]\n")
    try:
        service = get_gmail_service()
        if service is None:
            return "Authentication failed. Please re-authenticate Gmail."
        # Create the MIME email
        message = MIMEText(message_text)
        message['to'] = to
        message['from'] = 'me'
        message['subject'] = subject
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        # Create the draft
        draft = service.users().drafts().create(
            userId='me',
            body={'message': {'raw': raw_message}}
        ).execute()

        draft_id = draft.get('id')
        logging.info(f"Draft created successfully. Draft ID: {draft_id}")
        return draft_id
    except Exception as error:
        logging.error(f"Failed to create draft: {error}")
        return f"Failed to create draft: {error}"
    
@function_tool()
async def delete_gmail_draft(context: RunContext, draft_id: str) -> str:
    """
    Deletes a specified email draft using the Gmail API.

    :param service: An authorized Gmail API service instance.
    :param draft_id: The ID of the draft to delete.
    :return: Success message or error message.
    """
    print("\n[delete_gmail_draft]\n")
    try:
        service = get_gmail_service()
        if service is None:
            return "Authentication failed. Please re-authenticate Gmail."
        service.users().drafts().delete(userId='me', id=draft_id).execute()
        logging.info(f"Draft deleted successfully. Draft ID: {draft_id}")
        return f"Draft deleted successfully. ID: {draft_id}"
    except Exception as error:
        logging.error(f"Failed to delete draft: {error}")
        return f"Failed to delete draft: {error}"
    
@function_tool()
async def get_gmail_draft(context: RunContext, draft_id: str) -> str:
    """
    Retrieves a specific Gmail draft by its ID using the Gmail API.

    :param service: An authorized Gmail API service instance.
    :param draft_id: The ID of the draft to retrieve.
    :return: The subject line of the draft or an error message.
    """
    print("\n[get_gmail_draft]\n")
    try:
        service = get_gmail_service()
        if service is None:
            return "Authentication failed. Please re-authenticate Gmail."
        draft = service.users().drafts().get(userId='me', id=draft_id, format='metadata').execute()
        message = draft.get('message', {})
        headers = message.get('payload', {}).get('headers', [])
        
        # Extract the subject
        subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), "(No Subject)")
        logging.info(f"Retrieved draft with ID: {draft_id}, Subject: {subject}")
        return f"Draft ID: {draft_id}, Subject: {subject}"
    except Exception as error:
        logging.error(f"Failed to retrieve draft: {error}")
        return f"Failed to retrieve draft: {error}"
    
@function_tool()
async def send_gmail_draft(context: RunContext, draft_id: str) -> str:
    """
    Sends a specified Gmail draft using the Gmail API.

    :param service: An authorized Gmail API service instance.
    :param draft_id: The ID of the draft to send.
    :return: The ID of the sent message or an error message.
    """
    print("\n[send_gmail_draft]\n")
    try:
        service = get_gmail_service()
        if service is None:
            return "Authentication failed. Please re-authenticate Gmail."
        sent_message = service.users().drafts().send(
            userId='me',
            body={'id': draft_id}
        ).execute()

        message_id = sent_message.get('id')
        logging.info(f"Draft with ID {draft_id} sent successfully. Message ID: {message_id}")
        return f"Draft sent successfully. Message ID: {message_id}"
    except Exception as error:
        logging.error(f"Failed to send draft: {error}")
        return f"Failed to send draft: {error}"

@function_tool()
async def update_gmail_draft(context: RunContext, draft_id: str, to: str, subject: str, message_text: str) -> str:
    """
    Updates the content of an existing Gmail draft.

    :param service: An authorized Gmail API service instance.
    :param draft_id: The ID of the draft to update.
    :param to: The recipient's email address.
    :param subject: The subject of the email.
    :param message_text: The plain text content of the email.
    :return: The ID of the updated draft or an error message.
    """
    print("\n[update_gmail_draft]\n")
    try:
        service = get_gmail_service()
        if service is None:
            return "Authentication failed. Please re-authenticate Gmail."
        # Create the updated MIME message
        message = MIMEText(message_text)
        message['to'] = to
        message['from'] = 'me'
        message['subject'] = subject
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        # Update the draft
        updated_draft = service.users().drafts().update(
            userId='me',
            id=draft_id,
            body={'message': {'raw': raw_message}}
        ).execute()

        updated_draft_id = updated_draft.get('id')
        logging.info(f"Draft updated successfully. Draft ID: {updated_draft_id}")
        return f"Draft updated successfully. ID: {updated_draft_id}"
    except Exception as error:
        logging.error(f"Failed to update draft: {error}")
        return f"Failed to update draft: {error}"

# Background Gmail retrieval
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

@function_tool()
async def fetch_unread_recent_emails(max_results: int):

    """
    Fetches the most recent unread emails from the user's Gmail account.

    :param max_results: The maximum number of emails to fetch 
    :return: A list of emails
    """

    creds = Credentials(
        token=os.getenv("ACCESS_TOKEN"),
        refresh_token=os.getenv("REFRESH_TOKEN"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.getenv("GOOGLE_WEB_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET")
    )

    # Automatically refresh token if expired
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())

    # Build the Gmail API client
    service = build('gmail', 'v1', credentials=creds)

    # Fetch most recent unread messages using query "is:unread"
    results = service.users().messages().list(
        userId='me',
        maxResults=max_results,
        q='is:unread',
        labelIds=['INBOX']
    ).execute()

    messages = results.get('messages', [])

    emails = []

    for msg in messages:
        msg_data = service.users().messages().get(userId='me', id=msg['id']).execute()
        headers = msg_data.get('payload', {}).get('headers', [])
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '(No Subject)')
        from_email = next((h['value'] for h in headers if h['name'] == 'From'), '(No Sender)')
        snippet = msg_data.get('snippet', '')

        emails.append({
            'subject': subject,
            'from': from_email,
            'snippet': snippet
        })

    return emails
    
@function_tool()
async def get_current_address(context: RunContext) -> str:
    """
    Converts the user's current coordinates into a human-readable address using Google Geocoding API.
    """

    print("\n[get_current_address]\n")

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return "Google Maps API key not found."

    # Get current location from location manager
    current_location = location_manager.get_current_location()
    if not current_location:
        return "Current location not available. Please ensure location sharing is enabled."

    lat = current_location["latitude"]
    lon = current_location["longitude"]
    last_updated = current_location["last_updated"]

    # Call Geocoding API to reverse-geocode lat/lon
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "latlng": f"{lat},{lon}",
        "key": api_key
    }

    try:
        res = requests.get(url, params=params)
        data = res.json()

        if data.get("status") != "OK":
            return f"Google API error: {data.get('status')}"

        address = data["results"][0]["formatted_address"]

        return (
            f"You are near: {address}\n"
            f"Coordinates: {lat}, {lon} (Last updated: {last_updated.strftime('%Y-%m-%d %H:%M:%S')})"
        )

    except Exception as e:
        return f"Error retrieving address: {e}"

# Google Maps function_tools
@function_tool()
async def get_current_location(context: RunContext) -> str:
    """
    Gets the user's current location if available.
    
    :return: Current location information or error message
    """
    print("\n[get_current_location]\n")
    
    current_location = location_manager.get_current_location()
    if not current_location:
        return "Current location not available. Please ensure location sharing is enabled."
    
    latitude = current_location['latitude']
    longitude = current_location['longitude']
    last_updated = current_location['last_updated']
    
    return f"Current location: {latitude}, {longitude} (Last updated: {last_updated.strftime('%Y-%m-%d %H:%M:%S')})"

@function_tool()
async def find_place(context: RunContext, query: str) -> str:
    return find_place_from_text(query)

@function_tool()
async def get_travel_time(
    context: RunContext,
    destination: str,
    mode: str = "driving"
) -> str:
    """
    Calculates travel time from the user's current location to a destination using Google Directions API.
    Let the user know that this might take a few seconds.
    
    :param destination: Destination address or place name
    :param mode: Mode of travel: driving, walking, bicycling, or transit
    :return: Travel time and route information
    """
    print("\n[get_travel_time]\n")
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return "Google Maps API key not found."
    
    # Get current location
    current_location = location_manager.get_current_location()
    if not current_location:
        return "Current location not available. Please ensure location sharing is enabled."
    
    origin_str = f"{current_location['latitude']},{current_location['longitude']}"
    url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        "origin": origin_str,
        "destination": destination,
        "mode": mode,
        "key": api_key,
        "departure_time": "now"
    }

    try:
        res = requests.get(url, params=params)
        data = res.json()

        if data.get("status") != "OK":
            return f"Google API error: {data.get('status')}"

        leg = data["routes"][0]["legs"][0]
        duration = leg["duration"]["text"]
        start = leg["start_address"]
        end = leg["end_address"]

        return f"Travel time from your current location to {end} is {duration} by {mode}."

    except Exception as e:
        return f"Error retrieving travel time: {e}"
    
@function_tool()
async def get_distance_between_places(
    context: RunContext,
    origin: str,
    destination: str,
    mode: str = "driving"
) -> str:
    """
    Uses the Google Distance Matrix API to calculate distance and duration between two places.
    
    :param origin: Starting location (address or lat,lng)
    :param destination: Destination (address or lat,lng)
    :param mode: Mode of travel: driving, walking, bicycling, or transit
    :return: A short sentence with the distance and estimated duration
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return "Google Maps API key not found."

    url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {
        "origins": origin,
        "destinations": destination,
        "mode": mode,
        "key": api_key
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()

        if data.get("status") != "OK":
            return f"API Error: {data.get('status')}"

        element = data["rows"][0]["elements"][0]
        if element.get("status") != "OK":
            return f"Route error: {element.get('status')}"

        distance = element["distance"]["text"]
        duration = element["duration"]["text"]

        return f"Distance from {origin} to {destination} is {distance}, taking about {duration} by {mode}."
    except Exception as e:
        return f"Error retrieving distance: {e}"

@function_tool()
async def find_places_nearby_current_location(
    context: RunContext,
    keyword: str,
    radius: int = 1000
) -> str:
    """
    Searches for places of a given type/keyword near the user's current location using the Google Places API.

    :param keyword: What to search for (e.g., 'coffee', 'atm', 'museum')
    :param radius: Search radius in meters (default 1000)
    :return: A list of nearby places
    """
    print("\n[find_places_nearby_current_location]\n")
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return "Google Maps API key not found."
    
    # Get current location
    current_location = location_manager.get_current_location()
    if not current_location:
        return "Current location not available. Please ensure location sharing is enabled."

    latitude = current_location['latitude']
    longitude = current_location['longitude']

    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": f"{latitude},{longitude}",
        "radius": radius,
        "keyword": keyword,
        "key": api_key
    }

    try:
        res = requests.get(url, params=params)
        data = res.json()

        if data.get("status") != "OK":
            return f"Google Places API error: {data.get('status')}"

        results = data.get("results", [])
        if not results:
            return f"No places found for '{keyword}' nearby."

        top_places = results[:5]
        places_list = [
            f"{idx + 1}. {place['name']} — {place.get('vicinity', 'No address')}"
            for idx, place in enumerate(top_places)
        ]

        return f"Top places for '{keyword}' near your current location:\n" + "\n".join(places_list)

    except Exception as e:
        return f"Error finding nearby places: {e}"

@function_tool()
async def find_places_nearby(
    context: RunContext,
    latitude: float,
    longitude: float,
    keyword: str,
    radius: int = 1000
) -> str:
    """
    Searches for places of a given type/keyword near the specified location using the Google Places API.

    :param latitude: User's latitude
    :param longitude: User's longitude
    :param keyword: What to search for (e.g., 'coffee', 'atm', 'museum')
    :param radius: Search radius in meters (default 1000)
    :return: A list of nearby places
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return "Google Maps API key not found."

    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": f"{latitude},{longitude}",
        "radius": radius,
        "keyword": keyword,
        "key": api_key
    }

    try:
        res = requests.get(url, params=params)
        data = res.json()

        if data.get("status") != "OK":
            return f"Google Places API error: {data.get('status')}"

        results = data.get("results", [])
        if not results:
            return f"No places found for '{keyword}' nearby."

        top_places = results[:5]
        places_list = [
            f"{idx + 1}. {place['name']} — {place.get('vicinity', 'No address')}"
            for idx, place in enumerate(top_places)
        ]

        return f"Top places for '{keyword}' near you:\n" + "\n".join(places_list)

    except Exception as e:
        return f"Error finding nearby places: {e}"
    
@function_tool()
async def get_directions_from_current_location(
    context: RunContext,
    destination_query: str,
    mode: str = "driving"
) -> str:
    """
    Returns step-by-step directions from the user's current location to a destination using Google Directions API.

    :param destination_query: Destination (text, e.g., "Empire State Building")
    :param mode: Travel mode ('driving', 'walking', 'bicycling', 'transit')
    :return: Turn-by-turn directions in plain text
    """
    print("\n[get_directions_from_current_location]\n")
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return "Google Maps API key not found."
    
    # Get current location
    current_location = location_manager.get_current_location()
    if not current_location:
        return "Current location not available. Please ensure location sharing is enabled."

    # Use your existing place resolver for destination
    destination_info = find_place_from_text(destination_query, api_key)

    # Parse lat/lng from response string
    def extract_coords(info: str) -> str:
        try:
            lat = info.split("lat:")[1].split(",")[0].strip()
            lng = info.split("lng:")[1].split(")")[0].strip()
            return f"{lat},{lng}"
        except Exception:
            return ""

    origin = f"{current_location['latitude']},{current_location['longitude']}"
    destination = extract_coords(destination_info)

    if not destination:
        return "Could not resolve destination coordinates."

    url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        "origin": origin,
        "destination": destination,
        "mode": mode,
        "key": api_key
    }

    try:
        res = requests.get(url, params=params)
        data = res.json()

        if data.get("status") != "OK":
            return f"Google Directions API error: {data.get('status')}"

        steps = data["routes"][0]["legs"][0]["steps"]
        directions = []

        for i, step in enumerate(steps, start=1):
            instruction = step["html_instructions"]
            text_only = re.sub(r"<[^>]+>", "", instruction)
            distance = step["distance"]["text"]
            directions.append(f"{i}. {text_only} ({distance})")

        return "Here are your directions from your current location:\n" + "\n".join(directions)

    except Exception as e:
        return f"Error retrieving directions: {e}"

@function_tool()
async def find_directions(context: RunContext, query: str) -> str:
    """
    Finds a location from a query and gets directions to it.
    
    Publishes a message like:
    {"topic": "going_to", "location": "<resolved_place_name>"}
    """
    print("\n[announce_destination]\n")

    # Step 1: Resolve place
    location = find_place_from_text(query)
    if not location:
        return f"Could not resolve location for query: '{query}'"

    # Step 2: Send over LiveKit
    try:
        job_context = get_job_context()
        message = {
            "topic": "going_to",
            "location": location
        }
        info = await job_context.room.local_participant.send_text(
            json.dumps(message),
            topic="my-topic"
        )
        print(f"Sent location update with stream ID: {info.stream_id}")
        return f"Announced destination '{location}' with stream ID: {info.stream_id}"
    except Exception as error:
        print(f"Failed to send to room: {error}")
        return f"Failed to send to room: {error}"
    
import requests

JOBBER_API_BASE = "https://api.getjobber.com/api"

import requests
import json
from pydantic import BaseModel

JOBBER_GRAPHQL_ENDPOINT = "https://api.getjobber.com/api/graphql"

class LineItem(BaseModel):
    name: str
    quantity: float
    unitPrice: float

@function_tool
async def create_jobber_quote(line_items: List[LineItem], status: str = "DRAFT", note: str = ""):
    """
    Creates a quote in Jobber for a client.

    Args:
        line_items (List[LineItem]): A list of line items to include in the quote.
            Each line item should specify the name, quantity, and unit price.
        status (str, optional): The status of the quote. Typical values are
            "DRAFT", "SENT", or "APPROVED". Defaults to "DRAFT".
        note (str, optional): An optional note or comment to add to the quote.
            Defaults to an empty string.
    """
    
    # Convert line_items into GraphQL input format
    graphql_items = []
    for item in line_items:
        graphql_items.append(
            f"""{{
                name: "{item.name}",
                quantity: {item.quantity},
                unitPrice: {item.unitPrice}
            }}"""
        )

    graphql_items_str = ",\n".join(graphql_items)

    mutation = f"""
    mutation {{
      quoteCreate(
        attributes: {{
          clientId: "{os.getenv("JOBBER_CLIENT_ID")}",
          lineItems: [
            {graphql_items_str}
          ],
          status: {status},
          note: "{note}"
        }}
      ) {{
        quote {{
          id
          status
          totalPrice
        }}
        userErrors {{
          message
          path
        }}
      }}
    }}
    """

    headers = {
        "Authorization": f"Bearer {os.getenv('JOBBER_ACCESS_TOKEN')}",
        "Content-Type": "application/json",
        "X-JOBBER-GRAPHQL-VERSION": "2023-08-18",
    }

    # response.raise_for_status()
    print("adding data")
    return f"finished sending quote: {mutation}"

    



TOOL_LIST = [get_user_id, send_gmail_message, delete_gmail_message, 
create_gmail_draft, delete_gmail_draft, get_gmail_draft, send_gmail_draft, update_gmail_draft, 
get_current_location, find_place, get_travel_time, get_distance_between_places, 
find_places_nearby, find_places_nearby_current_location, find_directions, 
get_directions_from_current_location, start_google_maps, get_current_address, fetch_unread_recent_emails, send_text_message, auto_send_email, create_jobber_quote]
for tool in INVOICE_TOOLS:
    TOOL_LIST.append(tool)


def refresh_jobber_token(client_id: str, client_secret: str, refresh_token: str):
    url = "https://api.getjobber.com/api/oauth/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }

    response = requests.post(url, headers=headers, data=payload)
    response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)
    tokens = response.json()
    return tokens


# ans = refresh_jobber_token(os.getenv("JOBBER_CLIENT_ID"), os.getenv("JOBBER_SECRET"), os.getenv("JOBBER_REFRESH_TOKEN"))
# print(ans)
import asyncio

async def main():
    # Prepare line items
    line_items: List[LineItem] = [
        LineItem(name="Consultation", quantity=1, unitPrice=100.0),
        LineItem(name="Installation", quantity=2, unitPrice=150.0)
    ]
    
    # Call the async function
    result = await create_jobber_quote(line_items=line_items, status="SENT", note="Urgent client")
    
    print("Jobber quote response:", result)

# Run the async main function
# asyncio.run(main())