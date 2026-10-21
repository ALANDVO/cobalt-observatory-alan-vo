"""
OCSF Events API with trace correlation support.
"""
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload

from app.core.database import get_session
from app.models.ocsf import OCSFEvent
from pydantic import BaseModel, Field


class TraceContext(BaseModel):
    """Trace correlation context (OCSF 1.8 Trace profile)."""
    uid: str = Field(..., pattern=r"^[0-9a-f]{32}$", description="W3C trace ID (32 hex chars)")
    span_id: Optional[str] = Field(None, pattern=r"^[0-9a-f]{16}$", description="W3C span ID (16 hex chars)")


class OCSFEventCreate(BaseModel):
    """Request model for creating OCSF events."""
    class_uid: int = Field(..., ge=1, le=65535)
    activity_id: int = Field(..., ge=0, le=255)
    category_uid: int = Field(..., ge=1, le=65535)
    category_name: str = Field(..., min_length=1, max_length=100)
    class_name: str = Field(..., min_length=1, max_length=100)
    time: datetime
    severity_id: int = Field(..., ge=0, le=10)
    severity: str = Field(..., min_length=1, max_length=20)
    status_id: int = Field(..., ge=0, le=5)
    status: str = Field(..., min_length=1, max_length=20)
    trace_context: Optional[TraceContext] = None
    profiles: List[str] = Field(default_factory=list)
    event_data: Dict[str, Any] = Field(default_factory=dict)


class OCSFEventResponse(BaseModel):
    """Response model for OCSF events."""
    id: int
    class_uid: int
    activity_id: int
    category_uid: int
    category_name: str
    class_name: str
    time: datetime
    severity_id: int
    severity: str
    status_id: int
    status: str
    trace_uid: Optional[str] = None
    span_uid: Optional[str] = None
    trace_profile: bool
    profiles: List[str]
    event_data: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


class PaginatedResponse(BaseModel):
    """Paginated response wrapper."""
    items: List[OCSFEventResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


router = APIRouter()


@router.post("/events", response_model=OCSFEventResponse, status_code=status.HTTP_201_CREATED)
async def create_ocsf_event(
    event: OCSFEventCreate,
    session: AsyncSession = Depends(get_session)
):
    """Create a new OCSF event with optional trace correlation."""
    # Determine trace fields
    trace_uid = None
    span_uid = None
    trace_profile = False
    profiles = list(event.profiles)

    if event.trace_context:
        trace_uid = event.trace_context.uid
        span_uid = event.trace_context.span_id
        trace_profile = True
        if "trace" not in profiles:
            profiles.append("trace")

    # Build full event data
    full_event_data = event.event_data.copy()
    if trace_uid:
        full_event_data["trace"] = {"uid": trace_uid}
        if span_uid:
            full_event_data["trace"]["span"] = {"uid": span_uid}
    if profiles:
        full_event_data.setdefault("metadata", {})["profiles"] = profiles

    db_event = OCSFEvent(
        class_uid=event.class_uid,
        activity_id=event.activity_id,
        category_uid=event.category_uid,
        category_name=event.category_name,
        class_name=event.class_name,
        time=event.time,
        severity_id=event.severity_id,
        severity=event.severity,
        status_id=event.status_id,
        status=event.status,
        trace_uid=trace_uid,
        span_uid=span_uid,
        trace_profile=trace_profile,
        profiles=profiles,
        event_data=full_event_data,
    )

    session.add(db_event)
    await session.commit()
    await session.refresh(db_event)

    return db_event


@router.get("/events", response_model=PaginatedResponse)
async def list_ocsf_events(
    session: AsyncSession = Depends(get_session),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    trace_uid: Optional[str] = Query(None, pattern=r"^[0-9a-f]{32}$"),
    class_uid: Optional[int] = Query(None, ge=1, le=65535),
    activity_id: Optional[int] = Query(None, ge=0, le=255),
    category_uid: Optional[int] = Query(None, ge=1, le=65535),
    severity_id: Optional[int] = Query(None, ge=0, le=10),
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    has_trace: Optional[bool] = None,
):
    """List OCSF events with filtering and pagination."""
    query = select(OCSFEvent)

    if trace_uid:
        query = query.where(OCSFEvent.trace_uid == trace_uid)
    if class_uid:
        query = query.where(OCSFEvent.class_uid == class_uid)
    if activity_id:
        query = query.where(OCSFEvent.activity_id == activity_id)
    if category_uid:
        query = query.where(OCSFEvent.category_uid == category_uid)
    if severity_id:
        query = query.where(OCSFEvent.severity_id == severity_id)
    if start_time:
        query = query.where(OCSFEvent.time >= start_time)
    if end_time:
        query = query.where(OCSFEvent.time <= end_time)
    if has_trace is not None:
        if has_trace:
            query = query.where(OCSFEvent.trace_uid.is_not(None))
        else:
            query = query.where(OCSFEvent.trace_uid.is_(None))

    # Total count
    count_query = select(func.count()).select_from(query.subquery())
    total = await session.scalar(count_query) or 0

    # Pagination
    query = query.order_by(desc(OCSFEvent.time)).offset((page - 1) * page_size).limit(page_size)
    result = await session.execute(query)
    events = result.scalars().all()

    total_pages = (total + page_size - 1) // page_size

    return PaginatedResponse(
        items=events,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/events/{event_id}", response_model=OCSFEventResponse)
async def get_ocsf_event(
    event_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Get a single OCSF event by ID."""
    event = await session.get(OCSFEvent, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.get("/events/trace/{trace_uid}", response_model=List[OCSFEventResponse])
async def get_events_by_trace(
    trace_uid: str,
    session: AsyncSession = Depends(get_session)
):
    """Get all OCSF events correlated to a trace ID."""
    query = select(OCSFEvent).where(OCSFEvent.trace_uid == trace_uid).order_by(OCSFEvent.time)
    result = await session.execute(query)
    events = result.scalars().all()
    return events


@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ocsf_event(
    event_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Delete an OCSF event."""
    event = await session.get(OCSFEvent, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    await session.delete(event)
    await session.commit()