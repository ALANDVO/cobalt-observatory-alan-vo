"""
Evaluations API for AI agent evaluation workflows.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from pydantic import BaseModel, Field

from app.core.database import get_session
from app.models.ocsf import Evaluation, Agent


class EvaluationCreate(BaseModel):
    """Request model for creating an evaluation."""
    agent_id: int
    name: str = Field(..., min_length=1, max_length=200)
    dataset: str = Field(..., min_length=1, max_length=100)
    score: float = Field(..., ge=0.0, le=1.0)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    details: Optional[str] = None
    llm_explanation: Optional[str] = None
    # Trace correlation (OCSF 1.8 Trace profile)
    trace_uid: Optional[str] = Field(None, pattern=r"^[0-9a-f]{32}$", description="W3C trace ID (32 hex chars)")
    span_uid: Optional[str] = Field(None, pattern=r"^[0-9a-f]{16}$", description="W3C span ID (16 hex chars)")


class EvaluationResponse(BaseModel):
    """Response model for evaluations."""
    id: int
    agent_id: int
    name: str
    dataset: str
    score: float
    metrics: Dict[str, Any]
    details: Optional[str]
    llm_explanation: Optional[str]
    created_at: datetime
    # Trace correlation
    trace_uid: Optional[str] = None
    span_uid: Optional[str] = None

    class Config:
        from_attributes = True




class PaginatedEvaluationResponse(BaseModel):
    """Paginated evaluation response."""
    items: List[EvaluationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class EvaluationSummary(BaseModel):
    """Summary statistics for evaluations."""
    total_evaluations: int
    average_score: float
    best_score: float
    worst_score: float
    by_dataset: Dict[str, Dict[str, Any]]


router = APIRouter()


@router.post("", response_model=EvaluationResponse, status_code=status.HTTP_201_CREATED)
async def create_evaluation(
    evaluation: EvaluationCreate,
    session: AsyncSession = Depends(get_session)
):
    """Create a new evaluation."""
    # Verify agent exists
    agent = await session.get(Agent, evaluation.agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    db_evaluation = Evaluation(
        agent_id=evaluation.agent_id,
        trace_uid=evaluation.trace_uid,
        span_uid=evaluation.span_uid,
        name=evaluation.name,
        dataset=evaluation.dataset,
        score=evaluation.score,
        metrics=evaluation.metrics,
        details=evaluation.details,
        llm_explanation=evaluation.llm_explanation,
    )
    session.add(db_evaluation)
    await session.commit()
    await session.refresh(db_evaluation)
    return db_evaluation


@router.get("", response_model=PaginatedEvaluationResponse)
async def list_evaluations(
    session: AsyncSession = Depends(get_session),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    agent_id: Optional[int] = None,
    dataset: Optional[str] = None,
    min_score: Optional[float] = Query(None, ge=0.0, le=1.0),
    max_score: Optional[float] = Query(None, ge=0.0, le=1.0),
    trace_uid: Optional[str] = Query(None, pattern=r"^[0-9a-f]{32}$"),
):
    """List evaluations with filtering and pagination."""
    query = select(Evaluation)

    if agent_id:
        query = query.where(Evaluation.agent_id == agent_id)
    if dataset:
        query = query.where(Evaluation.dataset == dataset)
    if min_score is not None:
        query = query.where(Evaluation.score >= min_score)
    if max_score is not None:
        query = query.where(Evaluation.score <= max_score)
    if trace_uid:
        query = query.where(Evaluation.trace_uid == trace_uid)

    count_query = select(func.count()).select_from(query.subquery())
    total = await session.scalar(count_query) or 0

    query = query.order_by(desc(Evaluation.created_at)).offset((page - 1) * page_size).limit(page_size)
    result = await session.execute(query)
    evaluations = result.scalars().all()

    total_pages = (total + page_size - 1) // page_size

    return PaginatedEvaluationResponse(
        items=evaluations,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/summary", response_model=EvaluationSummary)
async def get_evaluation_summary(
    session: AsyncSession = Depends(get_session),
    agent_id: Optional[int] = None,
):
    """Get evaluation summary statistics."""
    query = select(Evaluation)
    if agent_id:
        query = query.where(Evaluation.agent_id == agent_id)

    result = await session.execute(query)
    evaluations = result.scalars().all()

    if not evaluations:
        return EvaluationSummary(
            total_evaluations=0,
            average_score=0.0,
            best_score=0.0,
            worst_score=0.0,
            by_dataset={},
        )

    scores = [e.score for e in evaluations]
    by_dataset = {}
    for e in evaluations:
        if e.dataset not in by_dataset:
            by_dataset[e.dataset] = {"count": 0, "scores": []}
        by_dataset[e.dataset]["count"] += 1
        by_dataset[e.dataset]["scores"].append(e.score)

    dataset_stats = {}
    for ds, data in by_dataset.items():
        ds_scores = data["scores"]
        dataset_stats[ds] = {
            "count": data["count"],
            "average": sum(ds_scores) / len(ds_scores),
            "best": max(ds_scores),
            "worst": min(ds_scores),
        }

    return EvaluationSummary(
        total_evaluations=len(evaluations),
        average_score=sum(scores) / len(scores),
        best_score=max(scores),
        worst_score=min(scores),
        by_dataset=dataset_stats,
    )


@router.get("/{evaluation_id}", response_model=EvaluationResponse)
async def get_evaluation(
    evaluation_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Get an evaluation by ID."""
    evaluation = await session.get(Evaluation, evaluation_id)
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    return evaluation


@router.delete("/{evaluation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_evaluation(
    evaluation_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Delete an evaluation."""
    evaluation = await session.get(Evaluation, evaluation_id)
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    await session.delete(evaluation)
    await session.commit()