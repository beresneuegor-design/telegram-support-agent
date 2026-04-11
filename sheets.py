from __future__ import annotations

import logging
from typing import Any
from datetime import datetime, timezone

import gspread
from google.auth.exceptions import DefaultCredentialsError


logger = logging.getLogger(__name__)


class SheetsLogger:
    def __init__(self, sheet_id: str, worksheet_name: str = "Logs") -> None:
        self.sheet_id = sheet_id
        self.worksheet_name = worksheet_name
        self.worksheet = self._connect()
        self._ensure_header()

    def _connect(self) -> Any:
        try:
            client = gspread.service_account()
            spreadsheet = client.open_by_key(self.sheet_id)
            try:
                return spreadsheet.worksheet(self.worksheet_name)
            except gspread.WorksheetNotFound:
                return spreadsheet.add_worksheet(title=self.worksheet_name, rows=1000, cols=5)
        except DefaultCredentialsError as exc:
            raise RuntimeError(
                "Google credentials not found. Set GOOGLE_APPLICATION_CREDENTIALS to your service account JSON file."
            ) from exc
        except Exception as exc:
            raise RuntimeError("Failed to connect to Google Sheets.") from exc

    def _ensure_header(self) -> None:
        try:
            existing = self.worksheet.row_values(1)
            if existing:
                return
            self.worksheet.append_row(["timestamp", "user_id", "question", "answer", "escalated"])
        except Exception:
            logger.exception("Failed to ensure Google Sheets header")

    def log_interaction(self, user_id: int, question: str, answer: str, escalated: bool) -> None:
        row = [
            datetime.now(timezone.utc).isoformat(),
            str(user_id),
            question,
            answer,
            str(escalated),
        ]
        try:
            self.worksheet.append_row(row)
        except Exception:
            logger.exception("Failed to append log row to Google Sheets")
