"""
GEDCOM → Neo4j importer.

Parses a .ged file and upserts Person nodes + PARENT_OF / MARRIED_TO relationships.
All operations are idempotent (MERGE-based) so re-importing the same file is safe.
"""
import logging
from pathlib import Path

from gedcom.element.family import FamilyElement
from gedcom.element.individual import IndividualElement
from gedcom.parser import Parser

from app.db.neo4j_client import run_write_query

logger = logging.getLogger(__name__)


def _parse_date(raw: str) -> str:
    """Return raw date string as-is (GEDCOM dates vary widely)."""
    return raw.strip() if raw else ""


async def import_gedcom(file_path: str | Path) -> dict[str, int]:
    parser = Parser()
    parser.parse_file(str(file_path))

    root_elements = parser.get_root_child_elements()

    persons_created = 0
    relations_created = 0

    # --- Phase 1: Individuals → Person nodes ---
    for element in root_elements:
        if not isinstance(element, IndividualElement):
            continue

        pointer = element.get_pointer()          # e.g. @I1@
        person_id = pointer.strip("@")

        (first, last) = element.get_name()
        gender = element.get_gender()            # M / F / U
        birth_data = element.get_birth_data()
        death_data = element.get_death_data()

        birth_date = _parse_date(birth_data[0]) if birth_data else ""
        birth_place = birth_data[1] if birth_data and len(birth_data) > 1 else ""
        death_date = _parse_date(death_data[0]) if death_data else ""

        cypher = """
MERGE (p:Person {id: $id})
SET p.firstName = $firstName,
    p.lastName  = $lastName,
    p.gender    = $gender,
    p.birthDate = $birthDate,
    p.birthPlace= $birthPlace,
    p.deathDate = $deathDate
"""
        await run_write_query(
            cypher,
            {
                "id": person_id,
                "firstName": first.strip(),
                "lastName": last.strip(),
                "gender": gender,
                "birthDate": birth_date,
                "birthPlace": birth_place,
                "deathDate": death_date,
            },
        )
        persons_created += 1
        logger.debug("Upserted Person %s %s (%s)", first, last, person_id)

    # --- Phase 2: Families → PARENT_OF + MARRIED_TO ---
    for element in root_elements:
        if not isinstance(element, FamilyElement):
            continue

        husband_id = None
        wife_id = None
        child_ids: list[str] = []

        for child in element.get_child_elements():
            tag = child.get_tag()
            value = child.get_value().strip("@").strip()
            if tag == "HUSB":
                husband_id = value
            elif tag == "WIFE":
                wife_id = value
            elif tag == "CHIL":
                child_ids.append(value)

        # MARRIED_TO (bidirectional stored as two directed edges)
        if husband_id and wife_id:
            await run_write_query(
                """
MATCH (h:Person {id: $hId}), (w:Person {id: $wId})
MERGE (h)-[:MARRIED_TO]->(w)
MERGE (w)-[:MARRIED_TO]->(h)
""",
                {"hId": husband_id, "wId": wife_id},
            )
            relations_created += 2

        # PARENT_OF
        for parent_id in [p for p in [husband_id, wife_id] if p]:
            for child_id in child_ids:
                await run_write_query(
                    """
MATCH (parent:Person {id: $parentId}), (child:Person {id: $childId})
MERGE (parent)-[:PARENT_OF]->(child)
""",
                    {"parentId": parent_id, "childId": child_id},
                )
                relations_created += 1

    logger.info(
        "GEDCOM import complete: %d persons, %d relationships", persons_created, relations_created
    )
    return {"persons": persons_created, "relationships": relations_created}
