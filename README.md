# Telegram Support Agent

AI-powered Telegram bot for automated customer support with RAG (Retrieval-Augmented Generation), Google Gemini embeddings, and Google Sheets logging.

```
┌─────────────────────────────────────────────────────────┐
│                    Telegram                              │
│                    User                                  │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│              python-telegram-bot                         │
│           (Message Handler / Router)                     │
│                                                          │
│    ┌──────────────┐    ┌─────────────────────────┐      │
│    │  start /     │    │   handle_message()       │      │
│    │  help cmds   │    │   (text / intent)        │      │
│    └──────────────┘    └───────────┬─────────────┘      │
└────────────────────────────────────┼────────────────────┘
                                     │
          ┌──────────────────────────┼──────────────┐
          │                          │              │
          ▼                          ▼              │
┌──────────────────┐     ┌────────────────────┐     │
│   SimpleRAG      │     │  Gemini LLM        │     │
│  (Embeddings /   │◄────│  (Response Gen)    │     │
│   Cosine Search) │     └─────────┬──────────┘     │
│                  │               │                │
│ knowledge_base   │               │                │
│ .txt (chunks)    │               │                │
└──────────────────┘               │                │
                                   │                │
                                   ▼                ▼
                         ┌────────────────────────────┐
                         │    Google Sheets Logger    │
                         │  (Interaction log + stats) │
                         └────────────────────────────┘
```

## Features

- **RAG-powered responses** — semantic search over a knowledge base using Google Gemini embeddings and cosine similarity
- **Human escalation** — detects when a user asks for a human operator and forwards the conversation to a manager
- **Conversation memory** — last 10 messages per user maintained in-memory for context
- **Google Sheets logging** — every interaction (question, answer, escalation) logged to a spreadsheet
- **Manager alerts** — automatic Telegram notifications to a manager chat when escalation is triggered
- **Confidence threshold** — falls back to human when semantic confidence drops below 55%
- **Polish language** — built for a Polish flower shop ("Kwiaciarnia Demo")

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/beresneuegor-design/telegram-support-agent.git
cd telegram-support-agent

python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### 2. Set environment variables

```bash
cp .env.example .env
# Edit .env with your keys (see .env.example for format)
```

### 3. Run the bot

```bash
python bot.py
```

## Tech Stack

| Component            | Technology                        |
|----------------------|-----------------------------------|
| Bot framework        | python-telegram-bot 21.x          |
| LLM / Embeddings     | Google Gemini (gemini-1.5-flash)  |
| RAG search           | Cosine similarity on embeddings  |
| Logging              | Google Sheets (gspread)           |
| Language             | Python 3.10+                      |

## Environment Variables

| Variable              | Description                        |
|-----------------------|------------------------------------|
| `TELEGRAM_TOKEN`      | Bot token from @BotFather          |
| `GEMINI_API_KEY`      | Google Gemini API key              |
| `GOOGLE_SHEETS_ID`    | Google Sheets spreadsheet ID       |
| `MANAGER_CHAT_ID`     | Telegram chat ID for alerts        |
| `GEMINI_MODEL`        | Gemini model name (optional)       |

## License

MIT
