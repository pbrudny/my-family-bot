"""
Admin endpoints (protected by API key).

POST /admin/upload-gedcom     — import a GEDCOM file into Neo4j
POST /admin/map-whatsapp      — link a WhatsApp number to a Person node
GET  /admin/persons           — list all Person nodes
"""
import logging
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.security import APIKeyHeader

from app.config import settings
from app.db.gedcom_importer import import_gedcom
from app.db.neo4j_client import run_read_query, run_write_query
from app.models.schemas import GedcomImportResponse, MapWhatsAppRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])

_api_key_header = APIKeyHeader(name="X-Admin-Key", auto_error=False)


async def require_admin_key(api_key: str | None = Depends(_api_key_header)) -> None:
    if not api_key or api_key != settings.admin_api_key:
        raise HTTPException(status_code=403, detail="Invalid or missing admin API key")


@router.post(
    "/upload-gedcom",
    response_model=GedcomImportResponse,
    dependencies=[Depends(require_admin_key)],
)
async def upload_gedcom(file: UploadFile = File(...)) -> GedcomImportResponse:
    """Upload and import a GEDCOM (.ged) file into the Neo4j graph."""
    if not file.filename or not file.filename.lower().endswith(".ged"):
        raise HTTPException(status_code=400, detail="File must have a .ged extension")

    contents = await file.read()
    with tempfile.NamedTemporaryFile(suffix=".ged", delete=False) as tmp:
        tmp.write(contents)
        tmp_path = Path(tmp.name)

    try:
        result = await import_gedcom(tmp_path)
    except Exception as exc:
        logger.exception("GEDCOM import failed")
        raise HTTPException(status_code=500, detail=f"Import failed: {exc}")
    finally:
        tmp_path.unlink(missing_ok=True)

    return GedcomImportResponse(**result)


@router.post(
    "/map-whatsapp",
    dependencies=[Depends(require_admin_key)],
)
async def map_whatsapp(body: MapWhatsAppRequest) -> dict[str, str]:
    """Link a WhatsApp number to an existing Person node."""
    records = await run_read_query(
        "MATCH (p:Person {id: $id}) RETURN p.id AS id LIMIT 1",
        {"id": body.person_id},
    )
    if not records:
        raise HTTPException(status_code=404, detail=f"Person {body.person_id} not found")

    await run_write_query(
        "MATCH (p:Person {id: $id}) SET p.whatsappId = $wid",
        {"id": body.person_id, "wid": body.whatsapp_id},
    )
    logger.info("Mapped WhatsApp %s → Person %s", body.whatsapp_id, body.person_id)
    return {"status": "ok", "personId": body.person_id, "whatsappId": body.whatsapp_id}


@router.get(
    "/persons",
    dependencies=[Depends(require_admin_key)],
)
async def list_persons() -> list[dict]:
    """Return all Person nodes (id, firstName, lastName, whatsappId)."""
    return await run_read_query(
        "MATCH (p:Person) RETURN p.id AS id, p.firstName AS firstName, "
        "p.lastName AS lastName, p.whatsappId AS whatsappId "
        "ORDER BY p.lastName, p.firstName"
    )
