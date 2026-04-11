# Kwiaciarnia Demo Telegram Support Bot

Telegram customer support bot for a Polish flower shop using Gemini, a simple RAG pipeline, and Google Sheets logging.

## Features

- Telegram bot built with `python-telegram-bot`
- Gemini-generated answers in Polish
- Simple RAG over `knowledge_base.txt`
- Conversation memory for the last 5 messages per user
- Google Sheets logging for every interaction
- Escalation flow for low-confidence or human-manager requests
- Typing indicator and production-focused error handling

## Project Structure

- `bot.py` - Telegram bot entry point and conversation logic
- `rag.py` - knowledge base loading, chunking, embeddings, similarity search
- `sheets.py` - Google Sheets logging helper
- `knowledge_base.txt` - Polish flower shop FAQ and operational details
- `.env` - environment variables
- `requirements.txt` - Python dependencies

## Architecture

```text
User on Telegram
      |
      v
python-telegram-bot
      |
      v
   bot.py
  /   |   \
 v    v    v
RAG  Gemini Sheets
 |      |      |
rag.py API   sheets.py
 |
knowledge_base.txt
```

## How It Works

1. User sends a message on Telegram.
2. `bot.py` stores recent conversation memory for that user.
3. `rag.py` loads the local knowledge base, splits it into chunks, embeds them with Gemini, and retrieves the most relevant chunks for the new question.
4. `bot.py` sends the retrieved context plus recent chat history to Gemini.
5. If confidence is too low or the user asks for a human/manager, the bot replies with `Przekazuję do managera ✓` and marks the interaction as escalated.
6. `sheets.py` logs timestamp, user ID, question, answer, and escalation status to Google Sheets.

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment variables

Fill in `.env`:

```env
TELEGRAM_TOKEN=your_telegram_bot_token
GEMINI_API_KEY=your_gemini_api_key
GOOGLE_SHEETS_ID=your_google_sheet_id
MANAGER_CHAT_ID=optional_telegram_chat_id_for_alerts
GEMINI_MODEL=gemini-1.5-flash
```

### 3. Configure Google Sheets credentials

Create a Google service account, download its JSON credentials file, and set:

```bash
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

Share your Google Sheet with the service account email.

### 4. Run the bot

```bash
python bot.py
```

## Logging Schema

The Google Sheet contains these columns:

- `timestamp`
- `user_id`
- `question`
- `answer`
- `escalated`

## Production Notes

- The bot validates required environment variables at startup.
- All major external calls are wrapped with error handling.
- Logging failures do not crash the bot.
- Escalations can optionally notify a manager chat via Telegram.
- For deployment, use a process manager or container runtime and provide secure secrets management.

## Possible Improvements

1. Cache embeddings to disk to avoid recomputing on each restart.
2. Add webhook deployment instead of polling.
3. Add structured confidence scoring from the LLM in addition to embedding similarity.
4. Add tests and monitoring.
