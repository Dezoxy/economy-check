#!/usr/bin/env python3
"""SMTP email delivery — stdlib smtplib. Secrets from .env:
SMTP_HOST, SMTP_PORT (465 SSL or 587 STARTTLS), SMTP_USER, SMTP_PASS,
EMAIL_FROM, EMAIL_TO (comma-separated allowed)."""
import os
import smtplib
import ssl
from email.message import EmailMessage


class DeliveryError(Exception):
    pass


def send_report(env, subject, body_text, attachments=()):
    host = env.get("SMTP_HOST")
    port = int(env.get("SMTP_PORT", "465"))
    user, password = env.get("SMTP_USER"), env.get("SMTP_PASS")
    sender = env.get("EMAIL_FROM", user)
    to = [a.strip() for a in env.get("EMAIL_TO", "").split(",") if a.strip()]
    if not host or not user or not password or not to:
        raise DeliveryError("SMTP_HOST/SMTP_USER/SMTP_PASS/EMAIL_TO missing from .env")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = ", ".join(to)
    msg.set_content(body_text)
    for path in attachments:
        with open(path, "rb") as f:
            data = f.read()
        maintype, subtype = ("text", "markdown") if path.endswith(".md") else \
                            ("application", "octet-stream")
        if path.endswith(".html"):
            maintype, subtype = "text", "html"
        if path.endswith(".png"):
            maintype, subtype = "image", "png"
        msg.add_attachment(data, maintype=maintype, subtype=subtype,
                           filename=os.path.basename(path))
    try:
        if port == 465:
            with smtplib.SMTP_SSL(host, port, context=ssl.create_default_context(),
                                  timeout=30) as s:
                s.login(user, password)
                s.send_message(msg)
        else:
            with smtplib.SMTP(host, port, timeout=30) as s:
                s.starttls(context=ssl.create_default_context())
                s.login(user, password)
                s.send_message(msg)
    except (smtplib.SMTPException, OSError) as e:
        raise DeliveryError("SMTP send failed: %s" % e)
