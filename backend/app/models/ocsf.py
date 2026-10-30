"""
OCSF Event models for trace correlation.
Based on OCSF 1.8 schema with Trace profile support.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import String, Text, DateTime, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class OCSFEvent(Base):
    """OCSF event with trace correlation support."""
    __tablename__ = "ocsf_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    class_uid: Mapped[int] = mapped_column(index=True)
    activity_id: Mapped[int]
    category_uid: Mapped[int] = mapped_column(index=True)
    category_name: Mapped[str] = mapped_column(String(100))
    class_name: Mapped[str] = mapped_column(String(100))
    time: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    severity_id: Mapped[int]
    severity: Mapped[str] = mapped_column(String(20))
    status_id: Mapped[int]
    status: Mapped[str] = mapped_column(String(20))

    # Trace correlation (OCSF 1.8 Trace profile)
    trace_uid: Mapped[Optional[str]] = mapped_column(String(32), index=True, nullable=True)
    span_uid: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    trace_profile: Mapped[bool] = mapped_column(default=False)

    # Profiles as JSON array
    profiles: Mapped[List[str]] = mapped_column(JSON, default=list)

    # Full event data as JSON
    event_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_ocsf_trace_time", "trace_uid", "time"),
        Index("ix_ocsf_class_activity", "class_uid", "activity_id"),
    )


class Agent(Base):
    """AI Agent model for evaluation workflows."""
    __tablename__ = "agents"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    model: Mapped[str] = mapped_column(String(100))
    provider: Mapped[str] = mapped_column(String(50))
    configuration: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class Evaluation(Base):
    """Agent evaluation results."""
    __tablename__ = "evaluations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    agent_id: Mapped[int] = mapped_column(index=True)
    # Trace correlation (OCSF 1.8 Trace profile)
    trace_uid: Mapped[Optional[str]] = mapped_column(String(32), index=True, nullable=True)
    span_uid: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    name: Mapped[str] = mapped_column(String(200))
    dataset: Mapped[str] = mapped_column(String(100))
    score: Mapped[float]
    metrics: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    llm_explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        Index("ix_eval_agent_created", "agent_id", "created_at"),
        Index("ix_eval_trace_uid", "trace_uid"),
    )


class AuditLog(Base):
    """Audit log for compliance tracking."""
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(50), index=True)
    resource_type: Mapped[str] = mapped_column(String(50))
    resource_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    details: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, index=True)

    __table_args__ = (
        Index("ix_audit_user_time", "user_id", "created_at"),
        Index("ix_audit_resource", "resource_type", "resource_id"),
    )