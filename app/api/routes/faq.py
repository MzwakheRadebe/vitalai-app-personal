from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from app.config import get_settings
from app.db_adapter import get_db

router = APIRouter(prefix="/faq")


class FAQCreate(BaseModel):
    question: str = Field(min_length=1, max_length=255)
    answer: str = Field(min_length=1)
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "question": "What are your business hours?",
            "answer": "We are open Monday to Friday, 9am–5pm."
        }
    })


class FAQUpdate(BaseModel):
    question: Optional[str] = Field(default=None)
    answer: Optional[str] = Field(default=None)
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "question": "Do you accept walk-ins?",
            "answer": "Yes, but appointments are preferred."
        }
    })


class FAQ(BaseModel):
    id: int
    question: str
    answer: str
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "id": 1,
            "question": "What are your business hours?",
            "answer": "We are open Monday to Friday, 9am–5pm."
        }
    })


def _row_to_dict(row: tuple) -> dict:
    """Convert a DB tuple `(id, question, answer)` into a response dict."""
    return {
        "id": row[0],
        "question": row[1],
        "answer": row[2],
    }


@router.get(
    "",
    response_model=list[FAQ],
    responses={
        200: {
            "description": "List of FAQs",
            "headers": {
                "X-Total-Count": {
                    "description": "Total FAQs matching filters",
                    "schema": {"type": "integer"},
                    "example": 2,
                }
            },
            "content": {
                "application/json": {
                    "example": [
                        {"id": 1, "question": "What are your business hours?", "answer": "We are open Monday to Friday, 9am–5pm."},
                        {"id": 2, "question": "Do you accept walk-ins?", "answer": "Yes, but appointments are preferred."}
                    ]
                }
            },
        }
    },
)
async def list_faq(
    q: Optional[str] = Query(None, min_length=1, description="Search question/answer"),
    limit: int = Query(20, ge=1, le=100, description="Max items to return"),
    offset: int = Query(0, ge=0, description="Items to skip"),
    response: Response = None,
):
    """List FAQs with optional text search and pagination.

    - Filters by `q` across `question` and `answer` using `LIKE`.
    - Sets `X-Total-Count` header for UI pagination.
    """
    settings = get_settings()
    conds: list[str] = []
    filter_params: list = []
    if q:
        conds.append("(question LIKE ? OR answer LIKE ?)")
        like = f"%{q}%"
        filter_params.extend([like, like])

    count_sql = "SELECT COUNT(*) FROM faq"
    if conds:
        count_sql += " WHERE " + " AND ".join(conds)

    async with get_db() as db:
        row = await db.fetchone(count_sql, filter_params)
        total = row[0] if row else 0
        if response is not None:
            response.headers["X-Total-Count"] = str(total)

        sql = "SELECT id, question, answer FROM faq"
        if conds:
            sql += " WHERE " + " AND ".join(conds)
        sql += " ORDER BY id LIMIT ? OFFSET ?"
        params = filter_params + [limit, offset]
        rows = await db.fetchall(sql, params)
    return [_row_to_dict(r) for r in rows]


@router.get(
    "/id/{faq_id}",
    response_model=FAQ,
    responses={
        200: {
            "description": "Single FAQ",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "question": "What are your business hours?",
                        "answer": "We are open Monday to Friday, 9am–5pm."
                    }
                }
            },
        }
    },
)
async def get_faq(faq_id: int):
    """Fetch a single FAQ by numeric ID; 404 if missing."""
    settings = get_settings()
    async with get_db() as db:
        row = await db.fetchone(
            "SELECT id, question, answer FROM faq WHERE id = ?",
            (faq_id,),
        )
    if not row:
        raise HTTPException(status_code=404, detail="FAQ not found")
    return _row_to_dict(row)


@router.post(
    "",
    response_model=FAQ,
    responses={
        200: {
            "description": "Created FAQ",
            "content": {
                "application/json": {
                    "example": {
                        "id": 3,
                        "question": "Is parking available?",
                        "answer": "Yes, there is a parking lot behind the building."
                    }
                }
            },
        }
    },
)
async def create_faq(req: FAQCreate):
    """Create a FAQ entry and return the persisted record."""
    settings = get_settings()
    async with get_db() as db:
        new_id = await db.insert(
            "INSERT INTO faq (question, answer) VALUES (?, ?)",
            (req.question, req.answer),
        )
        await db.commit()
        row = await db.fetchone(
            "SELECT id, question, answer FROM faq WHERE id = ?",
            (new_id,),
        )
    return _row_to_dict(row)


@router.put(
    "/id/{faq_id}",
    response_model=FAQ,
    responses={
        200: {
            "description": "Updated FAQ",
            "content": {
                "application/json": {
                    "example": {
                        "id": 2,
                        "question": "Do you accept walk-ins?",
                        "answer": "Yes, but appointments are preferred."
                    }
                }
            },
        }
    },
)
async def update_faq(faq_id: int, req: FAQUpdate):
    """Update a FAQ entry; partial updates supported via Pydantic model."""
    settings = get_settings()
    async with get_db() as db:
        row = await db.fetchone(
            "SELECT id, question, answer FROM faq WHERE id = ?",
            (faq_id,),
        )
        if not row:
            raise HTTPException(status_code=404, detail="FAQ not found")

        current = _row_to_dict(row)
        data = req.model_dump(exclude_none=True)
        updated = {**current, **data}

        await db.execute(
            "UPDATE faq SET question = ?, answer = ? WHERE id = ?",
            (updated["question"], updated["answer"], faq_id),
        )
        await db.commit()
    return updated


@router.delete(
    "/id/{faq_id}",
    response_model=dict,
    responses={
        200: {
            "description": "Delete confirmation",
            "content": {
                "application/json": {
                    "example": {"status": "deleted", "id": 2}
                }
            },
        }
    },
)
async def delete_faq(faq_id: int):
    """Delete a FAQ by ID; returns a simple confirmation payload."""
    settings = get_settings()
    async with get_db() as db:
        row = await db.fetchone("SELECT 1 FROM faq WHERE id = ?", (faq_id,))
        if not row:
            raise HTTPException(status_code=404, detail="FAQ not found")

        await db.execute("DELETE FROM faq WHERE id = ?", (faq_id,))
        await db.commit()
    return {"status": "deleted", "id": faq_id}