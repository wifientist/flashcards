"""Bulk import / export of cards (CSV and JSON).

Export streams a downloadable file. Import accepts the file *text* in a JSON
body (no multipart, so no extra dependency) and bulk-creates cards.
"""
import csv
import io
import json
import re
import unicodedata
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from database import get_db
from db_models import Card, Deck
from models import ImportRequest
from roles import require_authenticated, require_roles
from routes.cards import _visible_cards_stmt

router = APIRouter()

# Labels are multi-valued; join with "|" inside a single CSV cell to avoid
# colliding with the field comma.
LABELS_SEP = "|"

# Control characters (minus tab/newline/CR) and the Unicode replacement char,
# which is what shows up when a file was previously mis-decoded. We replace these
# with spaces rather than reject the whole import.
_GARBAGE_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f�]")


def _clean_text(s: str) -> str:
    """Make imported text safe to store: normalize and replace garbage chars
    with spaces. Legitimate Unicode (em-dashes, accents, emoji) is preserved."""
    if not s:
        return s
    s = unicodedata.normalize("NFC", s)
    return _GARBAGE_RE.sub(" ", s)


def _normalize_labels(value) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    # string form: split on the labels separator (and tolerate commas)
    parts = str(value).replace(",", LABELS_SEP).split(LABELS_SEP)
    return [p.strip() for p in parts if p.strip()]


def _parse_content(fmt: str, content: str) -> List[dict]:
    fmt = fmt.lower()
    if fmt == "json":
        data = json.loads(content)
        items = data.get("cards", data) if isinstance(data, dict) else data
        if not isinstance(items, list):
            raise ValueError("JSON must be a list of cards or {\"cards\": [...]}")
        return items
    if fmt == "csv":
        reader = csv.DictReader(io.StringIO(content))
        if not reader.fieldnames or "front" not in reader.fieldnames or "back" not in reader.fieldnames:
            raise ValueError("CSV must have a header row with at least 'front' and 'back'")
        return list(reader)
    raise ValueError("format must be 'csv' or 'json'")


@router.get("/export/cards")
def export_cards(format: str = "json", deck_id: Optional[str] = None,
                 db: Session = Depends(get_db),
                 payload=Depends(require_authenticated)):
    """Download cards (optionally one deck) as JSON or CSV."""
    fmt = format.lower()
    if fmt not in ("json", "csv"):
        raise HTTPException(status_code=400, detail="format must be 'csv' or 'json'")

    stmt = select(Card)
    if deck_id:
        stmt = stmt.where(Card.deck_id == deck_id)
    # Only export cards the caller may see (public + own; admins see all).
    stmt = _visible_cards_stmt(stmt, payload)
    cards = list(db.scalars(stmt))
    rows = [{"front": c.front, "back": c.back, "labels": list(c.labels or [])} for c in cards]

    if fmt == "json":
        body = json.dumps({"cards": rows}, indent=2, ensure_ascii=False)
        media, filename = "application/json", "cards.json"
    else:
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["front", "back", "labels"])
        for r in rows:
            writer.writerow([r["front"], r["back"], LABELS_SEP.join(r["labels"])])
        body, media, filename = buf.getvalue(), "text/csv", "cards.csv"

    return Response(
        content=body,
        media_type=media,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/import/cards")
def import_cards(req: ImportRequest, db: Session = Depends(get_db),
                 payload=Depends(require_roles(["admin"]))):
    """Bulk-create cards from CSV/JSON text. Admin only."""
    if req.deck_id:
        deck = db.get(Deck, req.deck_id)
        if not deck:
            raise HTTPException(status_code=400, detail="Deck not found")
        # Imported cards are public; they can only go into a public deck.
        if deck.owner_id is not None:
            raise HTTPException(status_code=400, detail="Can only import into public decks")

    try:
        items = _parse_content(req.format, req.content)
    except (ValueError, json.JSONDecodeError) as e:
        raise HTTPException(status_code=400, detail=f"Could not parse {req.format}: {e}")

    imported = 0
    skipped = 0
    for item in items:
        front = _clean_text(str(item.get("front") or "").strip())
        back = _clean_text(str(item.get("back") or "").strip())
        if not front or not back:
            skipped += 1
            continue
        labels = [_clean_text(l) for l in _normalize_labels(item.get("labels"))]
        db.add(Card(
            front=front,
            back=back,
            labels=labels,
            deck_id=req.deck_id,
            created_by=payload["user_id"],
        ))
        imported += 1

    try:
        db.commit()
    except (SQLAlchemyError, UnicodeError):
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Import failed while saving. The file may contain characters "
                   "the database can't store — try re-exporting it as UTF-8.",
        )
    return {"imported": imported, "skipped": skipped}
