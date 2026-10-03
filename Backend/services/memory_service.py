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


COLLECTION_NAME="long_term_memory"

qdrant.recreate_collection(
    collection_name=COLLECTION_NAME,
    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
)


def process_emails(transcript, user_id):
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

            label = result.get("merge_with") or result.get("label")
            known_labels.add(label)
            summary = result["summary"]

        elif len(thread) > 1:
            # Multi-message thread - summarize_and_label_thread
            # Concatenate all message snippets or bodies for the thread summary
            combined_text = ""
            for msg in thread["messages"]:
                print(msg)
                msg_text = f"Sender: {msg["sender"]}\nRecipient: {msg["recipient"]}\n Date: {msg["date"]}\n Content: {msg["body"]}\n\n"
                combined_text += msg_text
            email_id = str(uuid4())
            qdrant_id = str(uuid4())

            result = summarize_and_label_thread(combined_text, user_email, list(known_labels))

            label = result.get("merge_with") or result.get("label")
            known_labels.add(label)
            summary = result["summary"]

        # Embed summary
        embedding = model.encode(summary, convert_to_numpy=True)


        # Store in QDrant
        qdrant.upsert(
            collection_name=COLLECTION_NAME,
            points=[
                PointStruct(
                    id=qdrant_id,
                    vector=embedding,
                    payload={
                        "user_id": user_id,
                        "email_id": email_id,
                        "label": label,
                        "summary": summary
                    }
                )
            ]
        )

        # Store relations in Neo4j
        with driver.session() as session:
            session.write_transaction(
                extract_neo4j_relations,
                user_id=user_id,
                user_email=user_email,
                relations=result.get("relations", [])
            )

        processed.append({
            "email_id": email_id,
            "summary": summary,
            "label": label,
            # "sender": sender,
            # "recipient": recipient,
            "relations": result.get("relations", [])
        })
    print(processed)
    return processed


def summarize_and_label_email(email_text, user_email, sender, recipient, existing_labels, date):
    prompt = (
            f"""
            You are analyzing an email for knowledge graph construction and high-level summarization. You are working as
            the personal agent for the user with email: {user_email}

            Today's date is: {datetime.datetime.now().strftime("%Y-%m-%d")}  
            This email was sent from: {sender}  
            To: {recipient}  
            The email was sent at this date: {date}
            The users own email address (the person you care most about) is: {user_email}  

            Email content:

            {email_text}


            Respond in valid JSON format like this:
            {{
                "summary": "string",
                "label": "string",
                "merge_with": "string or null",
                "relations": [
                    {{"type": "string", "target": "string"}}
                    ...
                ]
            }}

            Instructions:

            1. **Summary**: 
            - Write a clear and concise summary of the email with key information from the email.
            - Include that this is an email from {sender} to {recipient}. And include their names if applicable (highlighting which is the user)
            - Resolve any vague or relative time expressions (e.g., “next Thursday”) to an absolute date based on todays date ({datetime.datetime.now().strftime("%Y-%m-%d")}).

            2. **Label**:
            - Assign a broad topical label.

            3. **merge_with**:
            - If the label overlaps semantically with any of these known labels: {existing_labels}, suggest a matching label from that list via the `merge_with` field. Otherwise, return null.

            4. **relations** (knowledge graph facts):
            - Only extract a relation if the email clearly expresses a **strong, factual** relationship or attribute about the user or someone the user interacts with.
            - Examples include:
                - "reports_to": "Jane Doe"
                - "works_at": "OpenAI"
                - "meeting_with": "John Smith"
                - "project": "Product Launch"
            - Do not extract weak or speculative associations.
            - Prefer relations centered around the user ({user_email}).
            - Keep the array empty if no meaningful relations are present.

            5. Output JSON only. Do not include commentary or explanations.
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
    prompt = (
            f"""
            You are analyzing an email conversation for knowledge graph construction and high-level summarization. You are working as
            the personal agent for the user with email: {user_email}

            Today's date is: {datetime.datetime.now().strftime("%Y-%m-%d")}  
            The users own email address (the person you care most about) is: {user_email}  

            Email conversation messages:

            {email_text}

            Respond in valid JSON format like this:
            {{
                "summary": "string",
                "label": "string",
                "merge_with": "string or null",
                "relations": [
                    {{"type": "string", "target": "string"}}
                    ...
                ]
            }}

            Instructions:

            1. **Summary**: 
            - Write a clear and concise summary of the conversation with key information from the conversation.
            - Include emails/names when applicable, emphasizing which is the user or when the user says something
            - Resolve any vague or relative time expressions (e.g., “next Thursday”) to an absolute date based on todays date ({datetime.datetime.now().strftime("%Y-%m-%d")}).

            2. **Label**:
            - Assign a broad topical label for the conversation.

            3. **merge_with**:
            - If the label overlaps semantically with any of these known labels: {existing_labels}, suggest a matching label from that list via the `merge_with` field. Otherwise, return null.

            4. **relations** (knowledge graph facts):
            - Only extract a relation if the email clearly expresses a **strong, factual** relationship or attribute about the user or someone the user interacts with.
            - Examples include:
                - "reports_to": "Jane Doe"
                - "works_at": "OpenAI"
                - "meeting_with": "John Smith"
                - "project": "Product Launch"
            - Do not extract weak or speculative associations.
            - Prefer relations centered around the user ({user_email}).
            - Keep the array empty if no meaningful relations are present.

            5. Output JSON only. Do not include commentary or explanations.
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