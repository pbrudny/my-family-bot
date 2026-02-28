from pydantic import BaseModel, Field


# --- Chat ---

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    user_id: str = Field(..., alias="userId")

    model_config = {"populate_by_name": True}


class ChatResponse(BaseModel):
    reply: str


# --- Admin ---

class MapWhatsAppRequest(BaseModel):
    person_id: str = Field(..., alias="personId")
    whatsapp_id: str = Field(..., alias="whatsappId")

    model_config = {"populate_by_name": True}


class GedcomImportResponse(BaseModel):
    persons: int
    relationships: int
    message: str = "Import complete"


# --- WhatsApp / Twilio ---

class TwilioWebhookResponse(BaseModel):
    """TwiML XML is returned directly — this is just for documentation."""
    twiml: str
