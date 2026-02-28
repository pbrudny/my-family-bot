"""
Twilio WhatsApp webhook endpoint.

POST /webhook/twilio  — called by Twilio on every incoming WhatsApp message.
"""
import logging

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import Response
from twilio.twiml.messaging_response import MessagingResponse

from app.agents.orchestrator import OrchestratorError, process
from app.channels.adapter import from_whatsapp, should_respond, strip_prefix
from app.channels.twilio_webhook import parse_twilio_payload, validate_twilio_signature
from app.db.neo4j_client import run_read_query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["whatsapp"])


async def _lookup_person_by_whatsapp(whatsapp_number: str) -> str | None:
    """Return Person.id for the given WhatsApp number, or None if not mapped."""
    records = await run_read_query(
        "MATCH (p:Person {whatsappId: $wid}) RETURN p.id AS id LIMIT 1",
        {"wid": whatsapp_number},
    )
    if records:
        return records[0].get("id")
    return None


def _twiml(text: str) -> Response:
    resp = MessagingResponse()
    resp.message(text)
    return Response(content=str(resp), media_type="application/xml")


@router.post("/twilio")
async def twilio_webhook(
    request: Request,
    Body: str = Form(default=""),
    From: str = Form(default=""),
) -> Response:
    # --- Signature validation ---
    signature = request.headers.get("X-Twilio-Signature", "")
    url = str(request.url)
    form_data = dict(await request.form())
    form_data_str = {k: str(v) for k, v in form_data.items()}

    if not validate_twilio_signature(url, form_data_str, signature):
        logger.warning("Invalid Twilio signature from %s", From)
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")

    body, from_number = parse_twilio_payload(form_data_str)
    msg = from_whatsapp(body, from_number)

    # --- Bot trigger filter ---
    if not should_respond(msg):
        logger.debug("Ignoring message from %s (no trigger prefix)", from_number)
        return Response(status_code=204)

    # --- Identity lookup ---
    person_id = await _lookup_person_by_whatsapp(from_number)
    if not person_id:
        logger.warning("Unknown WhatsApp number: %s", from_number)
        return _twiml(
            "Sorry, your number is not registered in the family tree. "
            "Please contact the administrator."
        )

    # --- Pipeline ---
    clean_text = strip_prefix(msg)
    try:
        reply = await process(clean_text, person_id)
    except OrchestratorError as exc:
        reply = str(exc)
    except Exception:
        logger.exception("Unexpected error processing WhatsApp message")
        reply = "An error occurred. Please try again later."

    return _twiml(reply)
