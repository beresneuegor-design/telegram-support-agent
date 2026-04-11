from __future__ import annotations

import logging
import os
from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Deque

from dotenv import load_dotenv
import google.generativeai as genai
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from rag import SearchResult, SimpleRAG
from sheets import SheetsLogger


logging.basicConfig(
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GOOGLE_SHEETS_ID = os.getenv("GOOGLE_SHEETS_ID", "")
MANAGER_CHAT_ID = os.getenv("MANAGER_CHAT_ID", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

HUMAN_KEYWORDS = {
    "manager",
    "czlowiek",
    "człowiek",
    "konsultant",
    "pracownik",
    "osoba",
    "human",
    "agent",
}

ESCALATION_MESSAGE = "Przekazuję do managera ✓"


@dataclass
class BotServices:
    rag: SimpleRAG
    sheets: SheetsLogger
    model: genai.GenerativeModel


conversation_memory: dict[int, Deque[str]] = defaultdict(lambda: deque(maxlen=10))


def requires_escalation(user_text: str, result: SearchResult) -> bool:
    lowered = user_text.lower()
    asks_human = any(keyword in lowered for keyword in HUMAN_KEYWORDS)
    return asks_human or result.confidence < 0.55


def build_prompt(user_text: str, memory: Deque[str], result: SearchResult) -> str:
    history = "\n".join(memory) if memory else "Brak wcześniejszej historii rozmowy."
    context = "\n\n".join(result.chunks) if result.chunks else "Brak trafionych fragmentów wiedzy."
    return f"""
Jesteś asystentem obsługi klienta kwiaciarni "Kwiaciarnia Demo" w Polsce.

Zasady:
- Odpowiadaj po polsku.
- Bądź uprzejmy, konkretny i pomocny.
- Odpowiadaj wyłącznie na podstawie kontekstu i historii rozmowy.
- Jeśli brakuje pewności lub informacji, napisz krótko, że sprawa zostanie przekazana do managera.
- Nie wymyślaj informacji spoza kontekstu.

Historia rozmowy:
{history}

Kontekst z bazy wiedzy:
{context}

Pytanie klienta:
{user_text}

Przygotuj krótką odpowiedź pomocową dla klienta.
""".strip()


def extract_response_text(response: object) -> str:
    text = getattr(response, "text", "")
    if text:
        return str(text).strip()

    candidates = getattr(response, "candidates", None) or []
    for candidate in candidates:
        content = getattr(candidate, "content", None)
        parts = getattr(content, "parts", None) or []
        collected = [getattr(part, "text", "") for part in parts if getattr(part, "text", "")]
        if collected:
            return "\n".join(collected).strip()

    return ""


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return
    await update.message.reply_text(
        "Czesc! Tu Kwiaciarnia Demo. Pomoge w sprawie bukietow, dostawy, cen i zamowien."
    )


async def send_manager_alert(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user_text: str,
) -> None:
    if not MANAGER_CHAT_ID or update.effective_user is None:
        return

    alert = (
        "Nowe przekazanie do managera\n"
        f"user_id: {update.effective_user.id}\n"
        f"username: @{update.effective_user.username or 'brak'}\n"
        f"wiadomosc: {user_text}"
    )
    try:
        await context.bot.send_message(chat_id=MANAGER_CHAT_ID, text=alert)
    except Exception:
        logger.exception("Failed to send manager alert")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None or update.effective_user is None:
        return

    text = (update.message.text or "").strip()
    if not text:
        return

    services: BotServices = context.application.bot_data["services"]
    user_id = update.effective_user.id
    memory = conversation_memory[user_id]

    try:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

        result = services.rag.search(text)
        escalated = requires_escalation(text, result)

        if escalated:
            answer = ESCALATION_MESSAGE
            await update.message.reply_text(answer)
            await send_manager_alert(update, context, text)
        else:
            prompt = build_prompt(text, memory, result)
            response = services.model.generate_content(prompt)
            answer = extract_response_text(response) or "Przepraszam, chwilowo nie moge przygotowac odpowiedzi."
            await update.message.reply_text(answer)

        memory.append(f"Klient: {text}")
        memory.append(f"Bot: {answer}")
        services.sheets.log_interaction(
            user_id=user_id,
            question=text,
            answer=answer,
            escalated=escalated,
        )
    except Exception:
        logger.exception("Unexpected error while handling message")
        fallback = "Przepraszam, wystapil blad. Sprobuj ponownie za chwile."
        await update.message.reply_text(fallback)
        try:
            services.sheets.log_interaction(
                user_id=user_id,
                question=text,
                answer=fallback,
                escalated=True,
            )
        except Exception:
            logger.exception("Failed to log fallback interaction")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.exception("Telegram application error", exc_info=context.error)


def validate_environment() -> None:
    missing = [
        key
        for key, value in {
            "TELEGRAM_TOKEN": TELEGRAM_TOKEN,
            "GEMINI_API_KEY": GEMINI_API_KEY,
            "GOOGLE_SHEETS_ID": GOOGLE_SHEETS_ID,
        }.items()
        if not value
    ]
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")


def create_services() -> BotServices:
    genai.configure(api_key=GEMINI_API_KEY)
    base_dir = Path(__file__).resolve().parent
    rag = SimpleRAG(
        knowledge_base_path=str(base_dir / "knowledge_base.txt"),
        embedding_model="models/text-embedding-004",
    )
    sheets = SheetsLogger(sheet_id=GOOGLE_SHEETS_ID)
    model = genai.GenerativeModel(GEMINI_MODEL)
    return BotServices(rag=rag, sheets=sheets, model=model)


def main() -> None:
    validate_environment()
    services = create_services()

    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.bot_data["services"] = services

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)

    logger.info("Starting Kwiaciarnia Demo bot")
    application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
