from __future__ import annotations

import asyncio
import smtplib
from email.message import EmailMessage

from core.config.settings import get_settings


class SMTPEmailClient:
    async def send_message(self, recipient: str, subject: str, body: str) -> None:
        settings = get_settings()

        def _send() -> None:
            if not settings.smtp_username or not settings.smtp_password:
                raise RuntimeError("SMTP credentials are not configured.")
            message = EmailMessage()
            message["From"] = settings.from_email
            message["To"] = recipient
            message["Subject"] = subject
            message.set_content(body)

            with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
                server.starttls()
                server.login(settings.smtp_username, settings.smtp_password)
                server.send_message(message)

        await asyncio.to_thread(_send)


email_client = SMTPEmailClient()
