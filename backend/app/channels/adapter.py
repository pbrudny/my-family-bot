"""
Channel Adapter

Normalises input from Web and WhatsApp into a common ChannelMessage dataclass.
Applies WhatsApp bot-trigger filtering.
"""
from dataclasses import dataclass
from enum import StrEnum

from app.config import settings


class Channel(StrEnum):
    WEB = "web"
    WHATSAPP = "whatsapp"


@dataclass
class ChannelMessage:
    text: str
    sender_id: str        # Person.id (web) or WhatsApp phone number
    channel: Channel
    raw_sender: str = ""  # Original WhatsApp ID before lookup


def from_web(message: str, user_id: str) -> ChannelMessage:
    """Create a normalised message from a web chat request."""
    return ChannelMessage(
        text=message.strip(),
        sender_id=user_id,
        channel=Channel.WEB,
    )


def from_whatsapp(body: str, from_number: str) -> ChannelMessage:
    """Create a normalised message from a Twilio WhatsApp webhook payload."""
    return ChannelMessage(
        text=body.strip(),
        sender_id=from_number,
        channel=Channel.WHATSAPP,
        raw_sender=from_number,
    )


def should_respond(msg: ChannelMessage) -> bool:
    """
    Returns True if the bot should respond to this message.

    For WhatsApp: only if message starts with a trigger prefix or mentions the bot name.
    For Web: always True.
    """
    if msg.channel == Channel.WEB:
        return True

    text = msg.text
    for prefix in settings.bot_prefixes:
        if text.startswith(prefix):
            return True

    if settings.bot_name.lower() in text.lower():
        return True

    return False


def strip_prefix(msg: ChannelMessage) -> str:
    """Return message text with leading trigger prefix removed."""
    text = msg.text
    for prefix in settings.bot_prefixes:
        if text.startswith(prefix):
            return text[len(prefix):].strip()
    return text.strip()
