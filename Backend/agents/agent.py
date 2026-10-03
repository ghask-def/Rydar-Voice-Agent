from dotenv import load_dotenv

from livekit import agents, rtc
from livekit.rtc import RpcInvocationData
from livekit.agents import AgentSession, Agent, RoomInputOptions, ChatContext, ChatMessage, JobProcess
from livekit.plugins import (
    deepgram,
    openai,
    noise_cancellation,
    silero,
    elevenlabs,
)
import requests
from config import NAME
from livekit.plugins.turn_detector.multilingual import MultilingualModel
# from livekit.plugins import google
from prompts import AGENT_INSTRUCTION
import logging
from text_message import send_text_message, auto_send_email

import httpx


logging.basicConfig(
    level=logging.INFO,
    filename='my_log_file.log',  # your desired log file path
    filemode='a',                # 'a' for append (default), 'w' to overwrite
    format='%(asctime)s - %(levelname)s - %(message)s'
)# from sentence_transformers import SentenceTransformer


from agents.function_tools import TOOL_LIST, get_travel_time, create_jobber_quote
from agents.invoice_tools import INVOICE_TOOLS



tool_dict = {func.__name__: func for func in TOOL_LIST}


# from agents.function_tools import (get_travel_time)
# from utils.retriever_local import query_qdrant
import time

# (get_user_id, send_gmail_message, delete_gmail_message, 
# create_gmail_draft, delete_gmail_draft, get_gmail_draft, send_gmail_draft, update_gmail_draft, 
# get_current_location, find_place, get_travel_time, get_distance_between_places, 
# find_places_nearby, find_places_nearby_current_location, find_directions,
# get_directions_from_current_location, start_google_maps, get_current_address, fetch_unread_recent_emails)
# from agents.invoice_tools import INVOICE_TOOLS
from agents.location_manager import location_manager

import json
import asyncio
# from utils.retriever import hybrid_retrieve

load_dotenv()

# tools=[get_user_id, send_gmail_message, delete_gmail_message, 
# create_gmail_draft, delete_gmail_draft, get_gmail_draft, send_gmail_draft, update_gmail_draft, 
# get_recent_emails_in_thread, get_current_location, find_place, get_travel_time, get_distance_between_places, 
# find_places_nearby, find_places_nearby_current_location, find_directions, 
# get_directions_from_current_location, start_google_maps, get_current_address]

class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=AGENT_INSTRUCTION,
                         tools= [send_text_message, auto_send_email, get_travel_time, create_jobber_quote] + INVOICE_TOOLS)

    async def on_user_turn_completed(
        self, turn_ctx: ChatContext, new_message: ChatMessage,
    ) -> None:
        
        # model: SentenceTransformer = self.session.ctx.proc.userdata["embedder"]

        # print(f"starting rag for query: {new_message.text_content}")

        # embedding = model.encode(new_message.text_content, "testUser")
        # rag_content = await query_qdrant(new_message.text_content, "testUser")
        
        # # rag_content = await hybrid_retrieve(new_message.text_content, "testUser")
        # # rag_inject = rag_content[0]
        # # injection = ""
        # # for content in rag_inject:
        # #     injection += content[0] + "\n"
        # injection =""
        # count = 0
        # for content in rag_content:
        #     injection += f"""Email {count} between the user with email {content[1]} and the recipient with email {content[2]}:
        #                     {content[0]} \n"""
        # turn_ctx.add_message(
        #     role="assistant", 
        #     content=f"Some additional background information potentially relevant to the user's next message. Use it simply to enhance your answer with more info if the info is relevant: {injection}"
        # )
        # # self.update_tools(rag_content[1])
        # print(injection)

        print("new message:" + new_message.text_content)

        url = "http://localhost:8000/hybrid_retrieve"  # Your FastAPI backend URL

        payload = {
            "user_query": new_message.text_content,  # must match the type in FastAPI (vector list or string)
            "user_id": "JohnDoe"
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)

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

        turn_ctx.add_message(
            role="assistant", 
            content=(
                "Some additional background information potentially relevant to the user's next message. "
                "Use it simply to enhance your answer with more info if the info is relevant: "
                f"{injection}"
            )
        )
        print(injection)

        # Assuming rag_content[1] is a list of (label, something) tuples
        function_tools = [tool_dict[label] for label, _ in rag_content[1] if label in tool_dict]
        print(f"rag functions: {rag_content[1]}")
        print("function_tools:")
        print(function_tools)
        # await self.update_tools(function_tools)
        print(self.tools)



                         



async def entrypoint(ctx: agents.JobContext):
    print("\n[The agent has entered]\n")
    print("STARTING")
    vad: silero.VAD = ctx.proc.userdata["vad"]

    # Store active tasks to prevent garbage collection (from reciever.py)
    _active_tasks = set()


    # IMPORTANT: Register data handler BEFORE session starts to avoid race conditions
    @ctx.room.on("data_received")
    def on_data_received(data: rtc.DataPacket):
        print(f"[LiveKit] received data from {data.participant.identity}: {data.data}")
        print(f"[LiveKit] data length: {len(data.data)} bytes")
        
        try:
            message = json.loads(data.data.decode())
            print(f"[LiveKit] parsed message: {message}")
            
            if message.get("type") == "locationUpdate":
                latitude = message.get("latitude")
                longitude = message.get("longitude")
                print(f"[LiveKit] Processing location update: lat={latitude}, lon={longitude}")
                if latitude is not None and longitude is not None:
                    # Create async task to update location
                    asyncio.create_task(location_manager.update_location(latitude, longitude))
                    print(f"[LiveKit] Location updated: {latitude}, {longitude}")
                else:
                    print("[LiveKit] Invalid location update: missing latitude or longitude")
            elif message.get("type") == "directions":
                route = message.get("route", {})
                print(f"[LiveKit] Directions received: Turn {route.get('turn')} in {route.get('distance')}")
            else:
                print(f"[LiveKit] Unrecognized message type: {message.get('type')}")
                
        except Exception as e:
            print(f"[LiveKit] Error processing data message: {e}")
            print(f"[LiveKit] Raw data: {data.data}")
            import traceback
            traceback.print_exc()

    async def async_handle_text_stream(reader, participant_identity):
        info = reader.info

        print(
            f'Text stream received from {participant_identity}\n'
            f'  Topic: {info.topic}\n'
            f'  Timestamp: {info.timestamp}\n'
            f'  ID: {info.id}\n'
            f'  Size: {info.size}'  # Optional, only available if the stream was sent with `send_text`
        )

        # Option 1: Process the stream incrementally using an async for loop.
        async for chunk in reader:
            print(f"Next chunk: {chunk}")

        # Option 2: Get the entire text after the stream completes.
        text = await reader.read_all()
        print(f"Received text: {text}")
      
    def handle_text_stream(reader, participant_identity):
        task = asyncio.create_task(async_handle_text_stream(reader, participant_identity))
        _active_tasks.add(task)
        task.add_done_callback(lambda t: _active_tasks.remove(t))
    
    session = AgentSession(
        stt=deepgram.STT(model="nova-3", language="multi"),
        llm=openai.LLM(model="gpt-4o-mini", temperature=0.1),
        tts=elevenlabs.TTS(
            voice_id="3jR9BuQAOPMWUjWpi0ll",
            model="eleven_multilingual_v2"
        ),
        vad=vad,
        turn_detection=MultilingualModel(),
    )

    await session.start(
        room=ctx.room,
        agent=Assistant(),
        room_input_options=RoomInputOptions(
            # LiveKit Cloud enhanced noise cancellation
            # - If self-hosting, omit this parameter
            # - For telephony applications, use `BVCTelephony` for best results
            video_enabled=False,
            noise_cancellation=noise_cancellation.BVC(), 
        ),
    )

    await ctx.connect()

    for identity, participant in ctx.room.remote_participants.items():
        print(f"Participant: {identity}")
        print(f"Participant type: {participant.kind}")
        for track in participant.track_publications.values():
            print(f"name: {track.name}, kind: {track.kind}")



    text = 'Lorem ipsum dolor sit amet...'
    info = await ctx.room.local_participant.send_text(text,topic='my-topic')
    print(f"Sent text with stream ID: {info.stream_id}")

    # Register text stream handler
    ctx.room.register_text_stream_handler(
        "my-topic",
        handle_text_stream
    )

    @ctx.room.local_participant.register_rpc_method("greet")
    async def handle_greet(data: RpcInvocationData):
        await session.generate_reply(
            instructions = f"Say hello to the user {NAME} and ask him what you can do for him."
        )
        print("generated welcome reply")
        


def prewarm_fnc(proc: JobProcess):
    # load silero weights and store to process userdata
    proc.userdata["vad"] = silero.VAD.load()

    # my_model = SentenceTransformer("all-MiniLM-L6-v2")
    # # Perform a dummy inference to initialize caches, tokenizers, graphs, etc.
    # _ = my_model.encode(["warm up"]).tolist()
    # proc.userdata["embedder"] = my_model


# async def main():
#     print("starting rag timer")


#     start = time.perf_counter()
#     # Your code here

#     rag_content = await hybrid_retrieve("Should I get a protonVPN subscription", "testUser")

    
#     end = time.perf_counter()

#     print(f"content: {rag_content}")
#     print(f"Elapsed time total: {end - start:.6f} seconds")

if __name__ == "__main__":

    # asyncio.run(main())
    agents.cli.run_app(agents.WorkerOptions(
        entrypoint_fnc=entrypoint,
        prewarm_fnc = prewarm_fnc,
        agent_name="rydar-agent",
    ))