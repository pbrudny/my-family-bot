"""
Twilio WhatsApp webhook utilities.

Validates the Twilio request signature and extracts message fields.
"""
import logging
from urllib.request import Request

from twilio.request_validator import RequestValidator

from app.config import settings

logger = logging.getLogger(__name__)

_validator: RequestValidator | None = None


def get_validator() -> RequestValidator:
    global _validator
    if _validator is None:
        _validator = RequestValidator(settings.twilio_auth_token)
    return _validator


def validate_twilio_signature(
    url: str,
    form_data: dict[str, str],
    signature: str,
) -> bool:
    """
    Return True if the Twilio-Signature header matches the computed signature.
    Always returns True when auth_token is empty (dev/test mode).
    """
    if not settings.twilio_auth_token:
        logger.warning("Twilio auth token not set — skipping signature validation")
        return True
    return get_validator().validate(url, form_data, signature)


def parse_twilio_payload(form_data: dict[str, str]) -> tuple[str, str]:
    """
    Extract (body, from_number) from Twilio webhook form data.
    from_number format: 'whatsapp:+48123456789'
    """
    body = form_data.get("Body", "").strip()
    from_number = form_data.get("From", "").strip()
    return body, from_number
