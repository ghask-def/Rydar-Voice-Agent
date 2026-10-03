import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from datetime import datetime
import os
import json
import datetime
from collections import defaultdict
from config import creds

# Gmail API scopes
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose", 
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify"
]

def get_gmail_service():
    print("\n[get_gmail_service]\n")
    
    # Load existing token
    # if os.path.exists("token.json"):
    #     creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no valid credentials available, refresh or re-authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Token expired, refreshing...")
            try:
                creds.refresh(Request())
                print("Token refreshed successfully")
            except Exception as e:
                print(f"Failed to refresh token: {e}")
                print("You need to re-authenticate")
                return None
        else:
            print("No valid credentials found. You need to re-authenticate")
            return None
        
        # Save the refreshed credentials
        # with open("token.json", "w") as token:
        #     token.write(creds.to_json())
    
    return build("gmail", "v1", credentials=creds)


import datetime
from collections import defaultdict
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import base64
import re
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv
from uuid import uuid4
from config import supa, driver, qdrant, client, model
from qdrant_client.http.models import PointStruct, VectorParams, Distance
from services.neo4j_graph_services import extract_neo4j_relations
from transformers import AutoTokenizer
from qdrant_client import QdrantClient, models




REQUIRED_SCOPE = "https://www.googleapis.com/auth/gmail.modify"
CLIENT_ID = os.getenv("GOOGLE_WEB_CLIENT_ID")
print(CLIENT_ID)
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
print(CLIENT_SECRET)
COLLECTION_NAME="email_history"

if not qdrant.collection_exists(COLLECTION_NAME):
    qdrant.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=384, distance=Distance.COSINE)
    )



def strip_html(html_content):
    """Remove HTML tags from content."""
    soup = BeautifulSoup(html_content, "html.parser")
    return soup.get_text(separator=' ', strip=True)

def clean_and_truncate(text, word_limit=200):
    words = re.findall(r'\S+', text)
    return ' '.join(words[:word_limit])

def get_email_body(payload):
    """Extract clean, truncated email body (max 200 words), excluding attachments."""
    def decode_part(part):
        data = part.get("body", {}).get("data")
        if data:
            decoded = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
            if part.get("mimeType") == "text/html":
                return strip_html(decoded)
            return decoded
        return ""

    if payload.get("body", {}).get("data"):
        return clean_and_truncate(decode_part(payload))

    if "parts" in payload:
        for part in payload["parts"]:
            if part.get("filename"):  # skip attachments
                continue
            if part.get("mimeType") == "text/plain":
                return clean_and_truncate(decode_part(part))
        for part in payload["parts"]:
            if part.get("filename"):
                continue
            if part.get("mimeType") == "text/html":
                return clean_and_truncate(decode_part(part))

    return ""


def scrape_user_gmail(user_id: str, user_email: str, access_token: str, refresh_token: str, scopes: list):
    REQUIRED_SCOPE = "https://www.googleapis.com/auth/gmail.modify"
    if REQUIRED_SCOPE not in scopes:
        raise ValueError("Gmail access scope too limited. Required: gmail.modify")
    
    print(access_token)
    print(refresh_token)
    print(scopes)

    creds = Credentials(
        token=access_token,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=CLIENT_ID,
        client_secret = CLIENT_SECRET,
        scopes=scopes
    )

    if not creds.valid and creds.expired and creds.refresh_token:
        print("problem with creds")
        creds.refresh(Request())

    service = build("gmail", "v1", credentials=creds)

    queries = [
        "is:starred",
        "-from:no-reply -from:notifications is:important",
        "from:me -from:no-reply -from:notifications"
    ]

    all_messages = []
    for query in queries:
        results = service.users().messages().list(userId="me", q=query, maxResults=50).execute()
        all_messages.extend(results.get("messages", []))

    thread_map = defaultdict(list)
    seen_ids = set()

    for msg in all_messages:
        msg_id = msg["id"]
        if msg_id in seen_ids:
            continue
        seen_ids.add(msg_id)

        msg_detail = service.users().messages().get(userId="me", id=msg_id).execute()
        thread_id = msg_detail.get("threadId")
        thread_map[thread_id].append(msg_detail)

    email_threads = []

    for thread_id, thread_msgs in thread_map.items():
        thread_msgs_sorted = sorted(thread_msgs, key=lambda x: int(x.get("internalDate", "0")))
        messages_summary = []

        for msg_detail in thread_msgs_sorted:
            headers = {h["name"]: h["value"] for h in msg_detail.get("payload", {}).get("headers", [])}
            subject = headers.get("Subject", "(No Subject)")
            sender = headers.get("From", "")
            recipient = headers.get("To", "")
            date = headers.get("Date", datetime.datetime.now().isoformat())
            body = get_email_body(msg_detail.get("payload", {}))

            messages_summary.append({
                "subject": subject,
                "sender": sender,
                "recipient": recipient,
                "date": date,
                "body": body
            })

        email_threads.append({
            "user_id": user_id,
            "gmail_thread_id": thread_id,
            "message_count": len(messages_summary),
            "messages": messages_summary,
            "source": "gmail"
        })


    # Return top 25 threads sorted by first message date
    sorted_threads = sorted(
        email_threads,
        key=lambda x: x["messages"][0]["date"]
    )


    return sorted_threads



def process_emails(user_email, email_threads, access_token, user_id):
    processed = []
    known_labels = set()

    for thread in email_threads:
        # thread is a list of message dicts
        if len(thread) == 1:
            # Single message thread - summarize_and_label_email
            msg = thread["messages"][0]
            full_text = msg["body"]
            date = msg["date"]
            sender = msg["sender"]
            recipient = msg["recipient"]
            email_id = str(uuid4())
            qdrant_id = str(uuid4())


            result = summarize_and_label_email(full_text, user_email, sender, recipient, list(known_labels), date)

        elif len(thread) > 1:
            # Multi-message thread - summarize_and_label_thread
            # Concatenate all message snippets or bodies for the thread summary
            combined_text = ""
            for msg in thread["messages"]:
                print(msg)
                msg_text = f"Sender: {msg['sender']}\nRecipient: {msg['recipient']}\n Date: {msg['date']}\n Content: {msg['body']}\n\n"
                combined_text += msg_text
            email_id = str(uuid4())
            qdrant_id = str(uuid4())

            result = summarize_and_label_thread(combined_text, user_email, list(known_labels))

        # embedding = model.encode(summary, convert_to_numpy=True)


        # Store full email in Supabase
        tasks = result.get("tasks")
        for task in tasks:
            supa.table("tasks").upsert({
                "user_id": user_id,
                "deadline": task.get("deadline"),
                "task": task.get("task")
            }).execute()

        # Store relations in Neo4j
        # with driver.session() as session:
        #     session.write_transaction(
        #         extract_neo4j_relations,
        #         user_id=user_id,
        #         user_email=user_email,
        #         relations=result.get("relations", [])
        #     )

        # processed.append({
        #     "email_id": email_id,
        #     "summary": summary,
        #     "label": label,
        #     # "sender": sender,
        #     # "recipient": recipient,
        #     "relations": result.get("relations", [])
        # })
    print(processed)
    return processed


def summarize_and_label_email(email_text, user_email, sender, recipient, existing_labels, date):
    # prompt = (
    #         f"""
    #         You are analyzing an email for knowledge graph construction and high-level summarization. You are working as
    #         the personal agent for the user with email: {user_email}

    #         Today's date is: {datetime.datetime.now().strftime("%Y-%m-%d")}  
    #         This email was sent from: {sender}  
    #         To: {recipient}  
    #         The email was sent at this date: {date}
    #         The users own email address (the person you care most about) is: {user_email}  

    #         Email content:

    #         {email_text}


    #         Instructions:

    #         1. **Summary**: 
    #         - Write a clear and concise summary of the email with key information from the email.
    #         - Include that this is an email from {sender} to {recipient}. And include their names if applicable (highlighting which is the user)
    #         - Resolve any vague or relative time expressions (e.g., “next Thursday”, "tomorrow") to an absolute date based on todays date ({datetime.datetime.now().strftime("%Y-%m-%d")}).

    #         2. **Label**:
    #         - Assign a broad topical label.

    #         3. **merge_with**:
    #         - If the label overlaps semantically with any of these known labels: {existing_labels}, suggest a matching label from that list via the `merge_with` field. Otherwise, return null.

    #         4. **relations** (knowledge graph facts):
    #         - Only extract a relation if the email clearly expresses a **strong, factual** relationship or attribute about the user or someone the user interacts with.
    #         - Examples include:
    #             - "reports_to": "Jane Doe"
    #             - "works_at": "OpenAI"
    #             - "meeting_with": "John Smith"
    #             - "project": "Product Launch"
    #         - Do not extract weak or speculative associations.
    #         - Prefer relations centered around the user ({user_email}).
    #         - Keep the array empty if no meaningful relations are present.

    #         5. Output JSON only. Do not include commentary or explanations.
    #         """
    #     )
    prompt = (
        f"""
            You are analyzing an email for extracting precise to-do list and scheduling information. You are working as
            the personal agent for the user with email: {user_email} so only extract things the user John Doe has to do.

            Today's date is: {datetime.datetime.now().strftime("%Y-%m-%d")}  
            This email was sent from: {sender}  
            To: {recipient}  
            The email was sent at this date: {date}
            The users own email address (the person you care most about) is: {user_email}  

            Email content:

            {email_text}


            Respond in valid JSON format like this:
            {{
                "tasks": [
                    {{"task:" "string", "deadline": "string"}}
                    ...
                ]
            }}

            Instructions:

            1. **Tasks**: 
            - Write clear and concise tasks the user has to do and the deadline they have to do them by
            - Only include tasks if they are relevant to the user with email {user_email} (it is something the user has to do)
            - Resolve any vague or relative time expressions (e.g., “next Thursday”, "tomorrow") to an absolute date based on the date the email was sent (July 29, 2025).

            2. Output JSON only. Do not include commentary or explanations.
            """
    )
    messages = [
        {"role": "system", "content": "You are an assistant that summarizes emails and extracts knowledge graph relations."},
        {"role": "user", "content": prompt}
    ]
    response = client.chat.completions.create(
        model="gpt-4.1-nano",
        messages=messages,
        temperature=0.3
    )
    result = response.choices[0].message.content
    print(result)
    return json.loads(result)


def summarize_and_label_thread(email_text, user_email, existing_labels):
    # prompt = (
    #         f"""
    #         You are analyzing an email conversation for knowledge graph construction and high-level summarization. You are working as
    #         the personal agent for the user with email: {user_email}

    #         Today's date is: {datetime.datetime.now().strftime("%Y-%m-%d")}  
    #         The users own email address (the person you care most about) is: {user_email}  

    #         Email conversation messages:

    #         {email_text}

    #         Instructions:

    #         1. **Summary**: 
    #         - Write a clear and concise summary of the conversation with key information from the conversation.
    #         - Include emails/names when applicable, emphasizing which is the user or when the user says something
    #         - Resolve any vague or relative time expressions (e.g., “next Thursday”) to an absolute date based on todays date ({datetime.datetime.now().strftime("%Y-%m-%d")}).

    #         2. **Label**:
    #         - Assign a broad topical label for the conversation.

    #         3. **merge_with**:
    #         - If the label overlaps semantically with any of these known labels: {existing_labels}, suggest a matching label from that list via the `merge_with` field. Otherwise, return null.

    #         4. **relations** (knowledge graph facts):
    #         - Only extract a relation if the email clearly expresses a **strong, factual** relationship or attribute about the user or someone the user interacts with.
    #         - Examples include:
    #             - "reports_to": "Jane Doe"
    #             - "works_at": "OpenAI"
    #             - "meeting_with": "John Smith"
    #             - "project": "Product Launch"
    #         - Do not extract weak or speculative associations.
    #         - Prefer relations centered around the user ({user_email}).
    #         - Keep the array empty if no meaningful relations are present.

    #         5. Output JSON only. Do not include commentary or explanations.
    #         """
    #     )
    prompt = (
    f"""
        You are analyzing an email conversation for extracting precise to-do list and scheduling information. You are working as
        the personal agent for the user with email: {user_email} so only extract things the user John Doe has to do.

        Today's date is: {datetime.datetime.now().strftime("%Y-%m-%d")}  
        The email conversation was sent on July 30th, 2025
        The users own email address (the person you care most about) is: {user_email}  

        Email content:

        {email_text}


        Respond in valid JSON format like this:
        {{
            "tasks": [
                {{"task:" "string", "deadline": "string"}}
                ...
            ]
        }}

        Instructions:

        1. **Tasks**: 
        - Write clear and concise tasks the user has to do and the deadline they have to do them by
        - Only include tasks if they are relevant to the user with email {user_email} (it is something the user has to do)
        - Resolve any vague or relative time expressions (e.g., “next Thursday”, "tomorrow") to an absolute date based on the date the email was sent: July 29, 2025 (and today is July 30, 2025)
        2. Output JSON only. Do not include commentary or explanations.
        """
    )
    messages = [
        {"role": "system", "content": "You are an assistant that summarizes emails and extracts knowledge graph relations."},
        {"role": "user", "content": prompt}
    ]
    response = client.chat.completions.create(
        model="gpt-4.1-nano",
        messages=messages,
        temperature=0.3
    )
    result = response.choices[0].message.content
    print(result)
    return json.loads(result)




def get_clean_email_body(payload):
    """Extract plain text body without attachments. Fallback to HTML if needed."""
    def decode(part):
        data = part.get("body", {}).get("data")
        if not data:
            return ""
        decoded = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
        if part.get("mimeType") == "text/html":
            return BeautifulSoup(decoded, "html.parser").get_text(separator=' ', strip=True)
        return decoded

    if payload.get("body", {}).get("data"):
        return decode(payload)

    if "parts" in payload:
        for part in payload["parts"]:
            if part.get("filename"):
                continue  # skip attachments
            if part.get("mimeType") == "text/plain":
                return decode(part)
        for part in payload["parts"]:
            if part.get("filename"):
                continue
            if part.get("mimeType") == "text/html":
                return decode(part)

    return ""

def sample_sent_emails_and_store(user_id: str, user_email: str, access_token: str, refresh_token: str, scopes: list):
    creds = Credentials(
        token=access_token,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=CLIENT_ID,
        client_secret = CLIENT_SECRET,
        scopes=scopes
    )

    if not creds.valid and creds.expired and creds.refresh_token:
        creds.refresh(Request())

    service = build("gmail", "v1", credentials=creds)

    query = "from:me -to:me"
    response = service.users().messages().list(userId="me", q=query, maxResults=100).execute()
    messages = response.get("messages", [])

    samples_by_recipient = {}
    user_email = None

    for msg in messages:
        msg_detail = service.users().messages().get(userId="me", id=msg["id"]).execute()
        headers = {h["name"]: h["value"] for h in msg_detail.get("payload", {}).get("headers", [])}
        recipient = headers.get("To")
        sender = headers.get("From")
        date = headers.get("Date", datetime.datetime.now().isoformat())


        # Only store one sample per unique recipient
        if not recipient or recipient in samples_by_recipient:
            continue

        if user_email is None:
            user_email = sender  # Set sender once, it's the user

        body = get_clean_email_body(msg_detail.get("payload", {})).strip()
        if not body:
            continue

        samples_by_recipient[recipient] = {
            "user_id": user_id,
            "user_email": user_email,
            "recipient": recipient,
            "content": body,
            "send_date": date
        }

        if len(samples_by_recipient) >= 5:
            break

    # Save to Supabase
    if samples_by_recipient:
        records = list(samples_by_recipient.values())
        supa.table("email_samples").upsert(records).execute()
        return {"saved": len(records), "status": "success"}
    
    return {"saved": 0, "status": "no_valid_emails_found"}