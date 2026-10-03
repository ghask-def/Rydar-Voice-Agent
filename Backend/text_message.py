import vonage
from vonage import Vonage, Auth
from vonage_sms import SmsMessage
from openai import OpenAI

import openai
from dotenv import load_dotenv
import os
import asyncio
import time
from config import  supa, client, refresh_tokens, update_creds
from uuid import uuid4
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import base64
from email.mime.text import MIMEText
from livekit.agents import function_tool
import requests
import httpx




# Create an Auth instance
auth_vonage = Auth(api_key=os.getenv("VONAGE_API_KEY"), api_secret=os.getenv("VONAGE_API_SECRET"))

# Create HttpClientOptions instance
# (not required unless you want to change options from the defaults)

# Create a Vonage instance
client_vonage = Vonage(auth=auth_vonage)

# if you want to manage your secret, please do so by visiting your API Settings page in your dashboard




@function_tool
async def send_text_message():
    """
    This function_tool is used to send a text message consisting of the user's to do list.
    to a pre-set number, and takes no parameters.
    
    Let the user know this might take a second
    """
    # print(response.model_dump_json(exclude_unset=True))

    url = "http://localhost:8000/hybrid_retrieve"  # Your FastAPI backend URL

    payload = {
        "user_query": "send a quick text message with my schedule over the next few days",  # must match the type in FastAPI (vector list or string)
        "user_id": "JohnDoe"
    }

    print("starting text message")
    async with httpx.AsyncClient() as httpxClient:
        response = await httpxClient.post(url, json=payload)

    if response.status_code == 200:
        rag_content_json = response.json()
        rag_content = rag_content_json["results"]
        print(f"rag_content arrived: {rag_content}")
    else:
        print(f"Error {response.status_code}: {response.text}")
        return  # Stop early if error

    # Assuming rag_content[0] is a list of email tuples
    rag_inject = rag_content[0]
    injection = ""
    for count, content in enumerate(rag_inject):
        injection += f"""Email {count} between the user with email {content[1]} and the recipient with email {content[2]}:
            {content[0]} \n"""

    content = f"""
        You are an agent that sends a concise text message with a detailed to do list for your client John Doe.
        
        Below is a list of valuable info to make the to do list:

    """
    response = supa.table("tasks").select("*").execute()
    for row in response.data:
        content += f"Task: {row.get('task')} \nDeadline: {row.get('deadline')}\n"


    content += f"\n\nSome additional information from emails John recieved:\n{injection}\n"
    content += "return a string containing a concice to do list style list all of the tasks and deadlines John has to do. Make it text friendly (do not include emojis and only include characters sendable over text message). Do not include '"
    print(content)
    messages = [
        {"role": "system", "content": "You are an assistant that creates concise to do lists that you can send in a text message"},
        {"role": "user", "content": content}
    ]
    response = client.chat.completions.create(
        model="gpt-4.1-nano",
        messages=messages,
        temperature=0.3
    )
    result = response.choices[0].message.content
    clean_string = result.replace("’", "'")
    print(clean_string)
    message = SmsMessage(to=os.getenv("SMS_TO_NUMBER"), from_=os.getenv("SMS_FROM_NUMBER"), text=clean_string)
    response = client_vonage.sms.send(message)
    return "The message has been sent to your phone with the to do list"


@function_tool()
async def auto_send_email(userQuery: str, recipientName: str, recipientEmail: str) -> str:
    """
    Generates an email for sending given the user's instruction and the recipient's name.
    Let the user know that you've generated the email and will let them know when it's sent.
    Parameters:
        userQuery: the user's instruction for what to put in the email
        recipientName: the name of the recipient
        recipientEmail: the email of the recipient
    """
    creds = Credentials(
        token=os.getenv("ACCESS_TOKEN"),
        refresh_token=os.getenv("REFRESH_TOKEN"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.getenv("GOOGLE_WEB_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET")
    )
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())

    
    response = supa.table("email_samples").select("content").limit(1).execute()
    sample_email_text = response.data[0]["content"] if response.data else "Hi there, hope you're well!"
    print(sample_email_text)
    gmail = build('gmail', 'v1', credentials=creds)

    prompt = f"""
        You are an assistant that writes emails in the same style of sample emails. You work for John Doe
        Here is a sample email of his.

        {sample_email_text}

        John Doe wants you to draft an email given that John gave you these instructions: {userQuery}
        Write an email according to the user's request addressed to {recipientName} that matches the writing and grammar style of the sample.
        """

    messages = [
        {"role": "system", "content": "You are an email writing assistant that writes emails similar to its user"},
        {"role": "user", "content": prompt}
    ]
    response = client.chat.completions.create(
        model="gpt-4.1-nano",
        messages=messages,
        temperature=0.3
    )
    result = response.choices[0].message.content

    print(result)

    
    # Create the MIME email
    message = MIMEText(result)
    message['to'] = recipientEmail
    message['subject'] = "A Message from Your Assistant"
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    # Create the draft
    gmail.users().messages().send(
            userId="me",
            body={"raw": raw_message}
        ).execute()

    return {"status": "Email sent", "to": recipientEmail}
