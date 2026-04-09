from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
import aiosqlite
from app.config import get_settings

router = APIRouter(prefix="/appointments")


class AppointmentCreate(BaseModel):
    """Request model to create a new appointment.

    Times are ISO8601 strings (e.g., 2025-10-13T09:00:00Z). We store them as
    TEXT in SQLite; ISO8601 compares correctly lexicographically.
    """
    patient_name: str = Field(min_length=1, max_length=100)
    clinician: str = Field(min_length=1, max_length=100)
    starts_at: str = Field(description="ISO8601 start time")
    ends_at: str = Field(description="ISO8601 end time")
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "patient_name": "Alice",
            "clinician": "DR.B",
            "starts_at": "2025-10-13T09:00:00Z",
            "ends_at": "2025-10-13T09:30:00Z"
        }
    })


class AppointmentUpdate(BaseModel):
    """Partial update model. Any field can be provided.

    We apply updates, then re-check conflict rules before saving.
    """
    patient_name: Optional[str] = Field(default=None)
    clinician: Optional[str] = Field(default=None)
    starts_at: Optional[str] = Field(default=None)
    ends_at: Optional[str] = Field(default=None)
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "patient_name": "Alice",
            "clinician": "DR.B",
            "starts_at": "2025-10-13T10:00:00Z",
            "ends_at": "2025-10-13T10:30:00Z"
        }
    })


class Appointment(BaseModel):
    id: int
    patient_name: str
    clinician: str
    starts_at: str
    ends_at: str
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "id": 2,
            "patient_name": "Alice",
            "clinician": "DR.B",
            "starts_at": "2025-10-13T09:00:00Z",
            "ends_at": "2025-10-13T09:30:00Z"
        }
    })


class Slot(BaseModel):
    starts_at: str
    ends_at: str
    model_config = ConfigDict(json_schema_extra={
        "example": {"starts_at": "2025-10-13T09:00:00Z", "ends_at": "2025-10-13T09:30:00Z"}
    })


class Slots(BaseModel):
    slots: list[Slot]
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "slots": [
                {"starts_at": "2025-10-13T09:00:00Z", "ends_at": "2025-10-13T09:30:00Z"},
                {"starts_at": "2025-10-13T10:00:00Z", "ends_at": "2025-10-13T10:30:00Z"}
            ]
        }
    })


def _row_to_dict(row: aiosqlite.Row) -> dict:
    """Convert a SQLite row to a plain dict."""
    return {
        "id": row[0],
        "patient_name": row[1],
        "clinician": row[2],
        "starts_at": row[3],
        "ends_at": row[4],
    }


@router.get(
    "",
    response_model=list[Appointment],
    responses={
        200: {
            "description": "List of appointments",
            "headers": {
                "X-Total-Count": {
                    "description": "Total appointments matching filters",
                    "schema": {"type": "integer"},
                    "example": 42,
                }
            },
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 1,
                            "patient": "Jane Doe",
                            "clinician": "Dr. Smith",
                            "starts_at": "2024-04-01T09:00:00Z",
                            "ends_at": "2024-04-01T09:30:00Z",
                            "notes": "Follow-up"
                        }
                    ]
                }
            },
        }
    },
)
async def list_appointments(
    clinician: Optional[str] = Query(None, min_length=1, description="Filter by clinician"),
    start_from: Optional[str] = Query(None, description="Filter appointments starting at or after ISO8601"),
    end_to: Optional[str] = Query(None, description="Filter appointments ending at or before ISO8601"),
    limit: int = Query(20, ge=1, le=100, description="Max items to return"),
    offset: int = Query(0, ge=0, description="Items to skip"),
    response: Response = None,
):
    settings = get_settings()
    async with aiosqlite.connect(settings.sqlite_path) as db:
        db.row_factory = aiosqlite.Row
        conds: list[str] = []
        filter_params: list = []
        if clinician:
            conds.append("clinician = ?")
            filter_params.append(clinician)
        if start_from:
            conds.append("starts_at >= ?")
            filter_params.append(start_from)
        if end_to:
            conds.append("ends_at <= ?")
            filter_params.append(end_to)

        count_sql = "SELECT COUNT(*) FROM appointments"
        if conds:
            count_sql += " WHERE " + " AND ".join(conds)
        async with db.execute(count_sql, filter_params) as cur:
            (total,) = await cur.fetchone()
        if response is not None:
            response.headers["X-Total-Count"] = str(total)

        sql = "SELECT id, patient, clinician, starts_at, ends_at, notes FROM appointments"
        if conds:
            sql += " WHERE " + " AND ".join(conds)
        sql += " ORDER BY starts_at LIMIT ? OFFSET ?"
        params = filter_params + [limit, offset]
        async with db.execute(sql, params) as cur:
            rows = await cur.fetchall()
    return [
        {
            "id": r[0],
            "patient": r[1],
            "clinician": r[2],
            "starts_at": r[3],
            "ends_at": r[4],
            "notes": r[5],
        }
        for r in rows
    ]


@router.post(
    "",
    response_model=Appointment,
    responses={
        200: {
            "description": "Created appointment",
            "content": {"application/json": {"example": {"id": 3, "patient_name": "Alice", "clinician": "DR.B", "starts_at": "2025-10-13T09:00:00Z", "ends_at": "2025-10-13T09:30:00Z"}}},
        }
    },
)
async def create_appointment(req: AppointmentCreate):
    """Create a new appointment with simple conflict checks.

    Conflict rule: For the same clinician, times must not overlap. We flag a
    409 if any existing appointment overlaps the requested interval.
    """
    settings = get_settings()
    async with aiosqlite.connect(settings.sqlite_path) as db:
        # Check for overlap: NOT (existing.ends_at <= starts OR existing.starts_at >= ends)
        async with db.execute(
            "SELECT COUNT(*) FROM appointments\n"
            "WHERE clinician = ?\n"
            "AND NOT (ends_at <= ? OR starts_at >= ?)",
            (req.clinician, req.starts_at, req.ends_at),
        ) as cur:
            (count,) = await cur.fetchone()
        if count > 0:
            raise HTTPException(status_code=409, detail="Appointment conflicts with existing booking")

        await db.execute(
            "INSERT INTO appointments (patient_name, clinician, starts_at, ends_at)\n"
            "VALUES (?, ?, ?, ?)",
            (req.patient_name, req.clinician, req.starts_at, req.ends_at),
        )
        await db.commit()

        # Return the newly created record
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT id, patient_name, clinician, starts_at, ends_at\n"
            "FROM appointments\n"
            "WHERE rowid = last_insert_rowid()"
        ) as cur:
            row = await cur.fetchone()
    return _row_to_dict(row)


@router.get(
    "/id/{appt_id}",
    response_model=Appointment,
    responses={
        200: {
            "description": "Single appointment",
            "content": {"application/json": {"example": {"id": 2, "patient_name": "Alice", "clinician": "DR.B", "starts_at": "2025-10-13T09:00:00Z", "ends_at": "2025-10-13T09:30:00Z"}}},
        }
    },
)
async def get_appointment(appt_id: int):
    """Fetch a single appointment by ID."""
    settings = get_settings()
    async with aiosqlite.connect(settings.sqlite_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT id, patient_name, clinician, starts_at, ends_at\n"
            "FROM appointments WHERE id = ?",
            (appt_id,),
        ) as cur:
            row = await cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return _row_to_dict(row)


@router.put(
    "/id/{appt_id}",
    response_model=Appointment,
    responses={
        200: {
            "description": "Updated appointment",
            "content": {"application/json": {"example": {"id": 2, "patient_name": "Alice", "clinician": "DR.B", "starts_at": "2025-10-13T10:00:00Z", "ends_at": "2025-10-13T10:30:00Z"}}},
        }
    },
)
async def update_appointment(appt_id: int, req: AppointmentUpdate):
    """Update an appointment with conflict checks."""
    settings = get_settings()
    async with aiosqlite.connect(settings.sqlite_path) as db:
        db.row_factory = aiosqlite.Row

        # Load existing appointment
        async with db.execute(
            "SELECT id, patient_name, clinician, starts_at, ends_at\n"
            "FROM appointments WHERE id = ?",
            (appt_id,),
        ) as cur:
            row = await cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Appointment not found")

        current = _row_to_dict(row)
        data = req.model_dump(exclude_none=True)
        updated = {**current, **data}

        # Conflict check against other appointments for same clinician
        async with db.execute(
            "SELECT COUNT(*) FROM appointments\n"
            "WHERE clinician = ? AND id <> ?\n"
            "AND NOT (ends_at <= ? OR starts_at >= ?)",
            (updated["clinician"], appt_id, updated["starts_at"], updated["ends_at"]),
        ) as cur:
            (count,) = await cur.fetchone()
        if count > 0:
            raise HTTPException(status_code=409, detail="Updated appointment conflicts with existing booking")

        await db.execute(
            "UPDATE appointments\n"
            "SET patient_name = ?, clinician = ?, starts_at = ?, ends_at = ?\n"
            "WHERE id = ?",
            (
                updated["patient_name"],
                updated["clinician"],
                updated["starts_at"],
                updated["ends_at"],
                appt_id,
            ),
        )
        await db.commit()
    return updated


@router.delete(
    "/id/{appt_id}",
    response_model=dict,
    responses={
        200: {
            "description": "Delete confirmation",
            "content": {"application/json": {"example": {"status": "deleted", "id": 2}}},
        }
    },
)
async def delete_appointment(appt_id: int):
    """Delete an appointment by ID."""
    settings = get_settings()
    async with aiosqlite.connect(settings.sqlite_path) as db:
        # Check existence first
        async with db.execute("SELECT 1 FROM appointments WHERE id = ?", (appt_id,)) as cur:
            row = await cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Appointment not found")

        # Perform delete
        await db.execute("DELETE FROM appointments WHERE id = ?", (appt_id,))
        await db.commit()
    return {"status": "deleted", "id": appt_id}


@router.get(
    "/slots",
    response_model=Slots,
    responses={
        200: {
            "description": "Available slots",
            "content": {
                "application/json": {
                    "example": {
                        "slots": [
                            {"starts_at": "2025-10-13T09:00:00Z", "ends_at": "2025-10-13T09:30:00Z"},
                            {"starts_at": "2025-10-13T10:00:00Z", "ends_at": "2025-10-13T10:30:00Z"}
                        ]
                    }
                }
            },
        }
    },
)
async def slots():
    # Stub availability endpoint, returns a simple block of free slots.
    return {
        "slots": [
            {"starts_at": "2025-10-13T09:00:00Z", "ends_at": "2025-10-13T09:30:00Z"},
            {"starts_at": "2025-10-13T10:00:00Z", "ends_at": "2025-10-13T10:30:00Z"},
            {"starts_at": "2025-10-13T11:00:00Z", "ends_at": "2025-10-13T11:30:00Z"},
        ]
    }