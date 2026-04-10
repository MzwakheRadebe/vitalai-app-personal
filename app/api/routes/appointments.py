from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Query, Response, Depends
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from app.db_adapter import get_db
from app.security import get_current_user
from app.doctors import DOCTOR_BY_EMAIL

router = APIRouter(prefix="/appointments")


class AppointmentCreate(BaseModel):
    patient_name: str = Field(min_length=1, max_length=100)
    clinician: str = Field(min_length=1, max_length=100)
    department: Optional[str] = Field(default=None, max_length=100)
    starts_at: str = Field(description="ISO8601 start time")
    ends_at: str = Field(description="ISO8601 end time")
    reason: Optional[str] = Field(default=None, max_length=500)
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "patient_name": "Alice",
            "clinician": "Dr. Smith",
            "department": "General Practice",
            "starts_at": "2025-10-13T09:00:00Z",
            "ends_at": "2025-10-13T09:30:00Z",
            "reason": "Persistent headache"
        }
    })


class AppointmentUpdate(BaseModel):
    patient_name: Optional[str] = Field(default=None, max_length=100)
    clinician: Optional[str] = Field(default=None, max_length=100)
    department: Optional[str] = Field(default=None, max_length=100)
    starts_at: Optional[str] = Field(default=None)
    ends_at: Optional[str] = Field(default=None)
    reason: Optional[str] = Field(default=None, max_length=500)


class Appointment(BaseModel):
    id: int
    patient_name: str
    clinician: str
    department: Optional[str] = None
    starts_at: str
    ends_at: str
    reason: Optional[str] = None


class Slot(BaseModel):
    starts_at: str
    ends_at: str


class Slots(BaseModel):
    slots: list[Slot]


def _row_to_dict(row: tuple) -> dict:
    """Convert a DB tuple (id, patient_name, clinician, department, starts_at, ends_at, reason) to dict."""
    return {
        "id": row[0],
        "patient_name": row[1],
        "clinician": row[2],
        "department": row[3] if len(row) > 3 else None,
        "starts_at": row[4] if len(row) > 4 else row[3],
        "ends_at": row[5] if len(row) > 5 else row[4],
        "reason": row[6] if len(row) > 6 else None,
    }


def _validate_times(starts_at: str, ends_at: str) -> tuple[datetime, datetime]:
    """Parse and validate ISO8601 times. Raises HTTPException on invalid input."""
    try:
        start_dt = datetime.fromisoformat(starts_at.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(ends_at.replace("Z", "+00:00"))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ISO8601 datetime format")

    # Make timezone-aware for comparison (treat naive datetimes as UTC)
    if start_dt.tzinfo is None:
        start_dt = start_dt.replace(tzinfo=timezone.utc)
    if end_dt.tzinfo is None:
        end_dt = end_dt.replace(tzinfo=timezone.utc)

    if start_dt < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Cannot book appointments in the past")
    if end_dt <= start_dt:
        raise HTTPException(status_code=400, detail="End time must be after start time")
    duration_seconds = (end_dt - start_dt).total_seconds()
    if duration_seconds > 7200:  # Max 2 hours
        raise HTTPException(status_code=400, detail="Appointment duration cannot exceed 2 hours")
    return start_dt, end_dt


@router.get("", response_model=list[Appointment])
async def list_appointments(
    clinician: Optional[str] = Query(None, min_length=1),
    start_from: Optional[str] = Query(None),
    end_to: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    response: Response = None,
    current_user: dict = Depends(get_current_user),  # Auth required
):
    """List appointments. Staff see only their own; admins see all."""
    # If the caller is a staff/doctor, automatically scope to their appointments
    effective_clinician = clinician
    role = current_user.get("role", "patient")
    if role == "staff":
        email = current_user.get("sub", "")
        doctor = DOCTOR_BY_EMAIL.get(email)
        if doctor:
            effective_clinician = doctor["name"]

    async with get_db() as db:
        conds: list[str] = []
        filter_params: list = []
        if effective_clinician:
            conds.append("clinician = ?")
            filter_params.append(effective_clinician)
        if start_from:
            conds.append("starts_at >= ?")
            filter_params.append(start_from)
        if end_to:
            conds.append("ends_at <= ?")
            filter_params.append(end_to)

        count_sql = "SELECT COUNT(*) FROM appointments"
        if conds:
            count_sql += " WHERE " + " AND ".join(conds)
        total_row = await db.fetchone(count_sql, filter_params)
        total = total_row[0] if total_row else 0
        if response is not None:
            response.headers["X-Total-Count"] = str(total)

        sql = "SELECT id, patient_name, clinician, department, starts_at, ends_at, reason FROM appointments"
        if conds:
            sql += " WHERE " + " AND ".join(conds)
        sql += " ORDER BY starts_at LIMIT ? OFFSET ?"
        rows = await db.fetchall(sql, filter_params + [limit, offset])
    return [_row_to_dict(r) for r in rows]


@router.post("", response_model=Appointment, status_code=201)
async def create_appointment(
    req: AppointmentCreate,
    _: dict = Depends(get_current_user),  # Auth required
):
    """Create a new appointment. Requires authentication."""
    _validate_times(req.starts_at, req.ends_at)

    async with get_db() as db:
        count_row = await db.fetchone(
            "SELECT COUNT(*) FROM appointments "
            "WHERE clinician = ? AND NOT (ends_at <= ? OR starts_at >= ?)",
            (req.clinician, req.starts_at, req.ends_at),
        )
        if (count_row[0] if count_row else 0) > 0:
            raise HTTPException(status_code=409, detail="Appointment conflicts with existing booking")

        new_id = await db.insert(
            "INSERT INTO appointments (patient_name, clinician, department, starts_at, ends_at, reason) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (req.patient_name, req.clinician, req.department, req.starts_at, req.ends_at, req.reason),
        )
        await db.commit()

        row = await db.fetchone(
            "SELECT id, patient_name, clinician, department, starts_at, ends_at, reason "
            "FROM appointments WHERE id = ?",
            (new_id,)
        )
    return _row_to_dict(row)


@router.get("/id/{appt_id}", response_model=Appointment)
async def get_appointment(
    appt_id: int,
    _: dict = Depends(get_current_user),  # Auth required
):
    """Fetch a single appointment by ID. Requires authentication."""
    async with get_db() as db:
        row = await db.fetchone(
            "SELECT id, patient_name, clinician, department, starts_at, ends_at, reason "
            "FROM appointments WHERE id = ?",
            (appt_id,),
        )
    if not row:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return _row_to_dict(row)


@router.put("/id/{appt_id}", response_model=Appointment)
async def update_appointment(
    appt_id: int,
    req: AppointmentUpdate,
    _: dict = Depends(get_current_user),  # Auth required
):
    """Update an appointment. Requires authentication."""
    async with get_db() as db:
        row = await db.fetchone(
            "SELECT id, patient_name, clinician, department, starts_at, ends_at, reason "
            "FROM appointments WHERE id = ?",
            (appt_id,),
        )
        if not row:
            raise HTTPException(status_code=404, detail="Appointment not found")

        current = _row_to_dict(row)
        data = req.model_dump(exclude_none=True)
        updated = {**current, **data}

        _validate_times(updated["starts_at"], updated["ends_at"])

        count_row = await db.fetchone(
            "SELECT COUNT(*) FROM appointments "
            "WHERE clinician = ? AND id <> ? "
            "AND NOT (ends_at <= ? OR starts_at >= ?)",
            (updated["clinician"], appt_id, updated["starts_at"], updated["ends_at"]),
        )
        if (count_row[0] if count_row else 0) > 0:
            raise HTTPException(status_code=409, detail="Updated appointment conflicts with existing booking")

        await db.execute(
            "UPDATE appointments "
            "SET patient_name = ?, clinician = ?, department = ?, starts_at = ?, ends_at = ?, reason = ? "
            "WHERE id = ?",
            (updated["patient_name"], updated["clinician"], updated["department"],
             updated["starts_at"], updated["ends_at"], updated["reason"], appt_id),
        )
        await db.commit()
    return updated


@router.delete("/id/{appt_id}", response_model=dict)
async def delete_appointment(
    appt_id: int,
    _: dict = Depends(get_current_user),  # Auth required
):
    """Delete an appointment. Requires authentication."""
    async with get_db() as db:
        row = await db.fetchone("SELECT 1 FROM appointments WHERE id = ?", (appt_id,))
        if not row:
            raise HTTPException(status_code=404, detail="Appointment not found")
        await db.execute("DELETE FROM appointments WHERE id = ?", (appt_id,))
        await db.commit()
    return {"status": "deleted", "id": appt_id}


@router.get("/slots", response_model=Slots)
async def slots():
    """Return available appointment slots for the next 7 days (9am–5pm)."""
    now = datetime.now(timezone.utc)
    # Round up to the next half hour
    start_day = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    slot_list = []
    for day_offset in range(7):
        day = start_day + timedelta(days=day_offset)
        # Skip weekends (Mon=0, Sat=5, Sun=6)
        if day.weekday() >= 5:
            continue
        for hour in range(9, 17):  # 09:00 to 16:30
            for minute in (0, 30):
                slot_start = day.replace(hour=hour, minute=minute)
                slot_end = slot_start + timedelta(minutes=30)
                slot_list.append({
                    "starts_at": slot_start.isoformat(),
                    "ends_at": slot_end.isoformat(),
                })
    return {"slots": slot_list}
