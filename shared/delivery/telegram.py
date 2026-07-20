#!/usr/bin/env python3
"""Telegram delivery — Bot API via stdlib urllib. Secrets from .env:
TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID."""
import json
import mimetypes
import os
import urllib.request
import uuid

API = "https://api.telegram.org"


class DeliveryError(Exception):
    pass


def _call(token, method, payload):
    url = "%s/bot%s/%s" % (API, token, method)
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            out = json.loads(resp.read())
    except Exception as e:
        raise DeliveryError("telegram %s failed: %s" % (method, e))
    if not out.get("ok"):
        raise DeliveryError("telegram %s: %s" % (method, out.get("description")))
    return out


def send_message(env, text):
    token, chat = env.get("TELEGRAM_BOT_TOKEN"), env.get("TELEGRAM_CHAT_ID")
    if not token or not chat:
        raise DeliveryError("TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID missing from .env")
    # Telegram caps messages at 4096 chars; long reports go as documents.
    return _call(token, "sendMessage", {
        "chat_id": chat, "text": text[:4000], "disable_web_page_preview": True})


def send_document(env, path, caption=""):
    token, chat = env.get("TELEGRAM_BOT_TOKEN"), env.get("TELEGRAM_CHAT_ID")
    if not token or not chat:
        raise DeliveryError("TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID missing from .env")
    boundary = uuid.uuid4().hex
    fname = os.path.basename(path)
    ctype = mimetypes.guess_type(fname)[0] or "application/octet-stream"
    with open(path, "rb") as f:
        blob = f.read()
    parts = []
    for name, value in (("chat_id", chat), ("caption", caption[:1000])):
        parts.append(("--%s\r\nContent-Disposition: form-data; name=\"%s\"\r\n\r\n%s\r\n"
                      % (boundary, name, value)).encode())
    parts.append(("--%s\r\nContent-Disposition: form-data; name=\"document\"; "
                  "filename=\"%s\"\r\nContent-Type: %s\r\n\r\n"
                  % (boundary, fname, ctype)).encode())
    parts.append(blob)
    parts.append(("\r\n--%s--\r\n" % boundary).encode())
    body = b"".join(parts)
    req = urllib.request.Request(
        "%s/bot%s/sendDocument" % (API, token), data=body,
        headers={"Content-Type": "multipart/form-data; boundary=%s" % boundary})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            out = json.loads(resp.read())
    except Exception as e:
        raise DeliveryError("telegram sendDocument failed: %s" % e)
    if not out.get("ok"):
        raise DeliveryError("telegram sendDocument: %s" % out.get("description"))
    return out
