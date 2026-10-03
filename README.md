# Rydar

**A voice-first AI assistant for independent contractors.**

Contractors spend their days on job sites and in the truck, not at a desk. Rydar lets them run the business side of their work (email, invoices, quotes, scheduling, directions) by talking to their phone. Ask Rydar to draft a reply to a client, build an invoice from what you just described, or tell you how long it will take to reach the next job. It handles the busywork while your hands stay free.

---

## Features

- **Hands-free voice agent.** Real-time conversation over LiveKit, with speech-to-text, an LLM, and natural text-to-speech.
- **Email management (Gmail).** Read recent unread mail, then draft, edit, send or delete messages and drafts. Rydar can also write emails in your own voice, using samples of your sent mail.
- **Voice invoicing (QuickBooks).** Build an invoice one line at a time by talking: set the customer, add or edit line items, set a due date, review it, then push it to QuickBooks. You can also create new customers or turn a spoken job description into an invoice.
- **Quotes (Jobber).** Create Jobber quotes from conversation.
- **Location & navigation.** Get your current address, find places nearby, check travel time and distance between jobs, and open Google Maps directions.
- **SMS to-do lists.** Text yourself a short to-do list built from your upcoming schedule.
- **Long-term memory.** Hybrid retrieval combines a Qdrant vector store with a Neo4j knowledge graph, so the agent remembers your clients, jobs, and preferences.

## Architecture

```
┌─────────────────────┐        LiveKit (WebRTC)        ┌──────────────────────────┐
│   iOS app (SwiftUI) │ ◀────────────────────────────▶ │  Voice agent (LiveKit    │
│                     │                                │  Agents, Python)         │
│  • Firebase Auth    │                                │  • Deepgram STT          │
│  • Google Sign-In   │        HTTP (FastAPI)          │  • OpenAI LLM            │
│  • Location updates │ ◀────────────────────────────▶ │  • ElevenLabs TTS        │
└─────────────────────┘                                │  • Function tools        │
                                                       └────────────┬─────────────┘
                                                                    │
            ┌──────────────┬──────────────┬──────────────┬─────────┴────┬──────────────┐
            ▼              ▼              ▼              ▼              ▼              ▼
         Gmail API     QuickBooks      Jobber      Google Maps     Supabase     Qdrant + Neo4j
                                                                  (users/creds)    (memory)
```

| Layer | Tech |
|---|---|
| iOS client | Swift, SwiftUI, LiveKit Swift SDK, Firebase Auth, Google Sign-In, Supabase Swift |
| Voice agent | LiveKit Agents, Deepgram Nova-3, OpenAI `gpt-4o-mini`, ElevenLabs, Silero VAD, multilingual turn detection |
| API server | FastAPI (LiveKit token minting, Gmail OAuth, session + retrieval endpoints) |
| Data | Supabase (Postgres), Qdrant (vectors), Neo4j (graph), `sentence-transformers` embeddings |
| Integrations | Gmail, QuickBooks Online, Jobber, Google Maps, Vonage SMS |

## Repository layout

```
Backend/
├── main.py                 # FastAPI app (token, auth, session, retrieval routes)
├── config.py               # Env loading, shared clients (Supabase, Neo4j, OpenAI)
├── prompts.py              # Agent system prompt
├── text_message.py         # SMS + auto-email tools
├── agents/
│   ├── agent.py            # LiveKit voice agent entrypoint
│   ├── function_tools.py   # Gmail, maps/location, Jobber tools
│   ├── invoice_tools.py    # Voice invoicing tools
│   ├── invoice_manager.py  # Invoice session state
│   └── location_manager.py # Live device location
├── api/routes/             # FastAPI routers (LiveKit token, Gmail OAuth, sessions)
├── services/               # Gmail, QuickBooks, Supabase, Qdrant, Neo4j, memory
├── utils/                  # Hybrid retriever, session helpers
└── .env.example            # Required environment variables

Frontend/
├── Frontend.xcodeproj
└── Frontend/               # SwiftUI app (sign-in, home, services, history, voice session)
```

## Getting started

### Prerequisites

- macOS with Xcode 16+ (iOS 18.2 deployment target)
- Python 3.11+
- Accounts/keys for: LiveKit Cloud, OpenAI, Deepgram, ElevenLabs, Supabase, Firebase, Google Cloud (Gmail + Maps APIs), Qdrant, Neo4j Aura, and optionally QuickBooks, Jobber and Vonage

### 1. Backend

```bash
cd Backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
pip install livekit-plugins-elevenlabs firebase-admin vonage uvicorn

cp .env.example .env    # then fill in your keys
```

Add these credential files to `Backend/`. They are gitignored, so they won't be committed:

- `firebase-service-account.json`: Firebase Admin service account key
- `credentials.json`: Google OAuth client, used by `gmailAuth.py`

Run the API server and the voice agent in separate terminals:

```bash
# API server
uvicorn main:app --reload --port 8000

# Voice agent worker
python -m agents.agent dev
```

To connect QuickBooks, run `python quickbooksAuth.py` once to finish the OAuth flow. It writes `quickbooks_token.json` locally.

### 2. iOS app

1. Open `Frontend/Frontend.xcodeproj` in Xcode.
2. Download `GoogleService-Info.plist` from your Firebase project and add it to `Frontend/Frontend/`.
3. Replace the `YOUR_...` placeholders with your own values:

   | File | Value |
   |---|---|
   | `SupabaseManager.swift` | Supabase project URL and anon key |
   | `GmailOAuthManager.swift` | Google OAuth client ID (iOS client) |
   | `Info.plist` | Reversed client IDs for the Gmail OAuth client and your Firebase app (`REVERSED_CLIENT_ID` from `GoogleService-Info.plist`) |
   | `ConnectButtonView.swift` | LiveKit server URL. Access tokens come from the backend's `/token/getToken` endpoint. |
   - `RoomContext.swift`, `SessionManager.swift`, `WebSocketManager.swift`: the backend URL (`localhost` works in the simulator; use your machine's LAN IP on a physical device)
4. Build and run on an iOS 18.2+ simulator or device.

## Status

Rydar is an early-stage prototype built as a startup project. Some flows still use placeholder user IDs and local URLs, and parts of the codebase are experimental.

## Author

Gabriel Haskell
