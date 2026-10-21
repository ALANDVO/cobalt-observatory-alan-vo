from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from pydantic import BaseModel, Field

from app.core.database import get_session
from app.models.ocsf import Agent



class AgentCreate(BaseModel):
    """Request model for creating an agent."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    model: str = Field(..., min_length=1, max_length=100)
    provider: str = Field(..., min_length=1, max_length=50)
    configuration: Dict[str, Any] = Field(default_factory=dict)


class AgentUpdate(BaseModel):
    """Request model for updating an agent."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    model: Optional[str] = Field(None, min_length=1, max_length=100)
    provider: Optional[str] = Field(None, min_length=1, max_length=50)
    configuration: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class AgentResponse(BaseModel):
    """Response model for agents."""
    id: int
    name: str
    description: Optional[str]
    model: str
    provider: str
    configuration: Dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaginatedAgentResponse(BaseModel):
    """Paginated agent response."""
    items: List[AgentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


router = APIRouter()


@router.post("", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    agent: AgentCreate,
    session: AsyncSession = Depends(get_session)
):
    """Create a new agent."""
    # Check for duplicate name
    existing = await session.execute(select(Agent).where(Agent.name == agent.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Agent with this name already exists")

    db_agent = Agent(
        name=agent.name,
        description=agent.description,
        model=agent.model,
        provider=agent.provider,
        configuration=agent.configuration,
    )
    session.add(db_agent)
    await session.commit()
    await session.refresh(db_agent)
    return db_agent


@router.get("", response_model=PaginatedAgentResponse)
async def list_agents(
    session: AsyncSession = Depends(get_session),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_active: Optional[bool] = None,
    provider: Optional[str] = None,
):
    """List agents with filtering and pagination."""
    query = select(Agent)

    if is_active is not None:
        query = query.where(Agent.is_active == is_active)
    if provider:
        query = query.where(Agent.provider == provider)

    count_query = select(func.count()).select_from(query.subquery())
    total = await session.scalar(count_query) or 0

    query = query.order_by(desc(Agent.created_at)).offset((page - 1) * page_size).limit(page_size)
    result = await session.execute(query)
    agents = result.scalars().all()

    total_pages = (total + page_size - 1) // page_size

    return PaginatedAgentResponse(
        items=agents,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Get an agent by ID."""
    agent = await session.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.patch("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: int,
    agent_update: AgentUpdate,
    session: AsyncSession = Depends(get_session)
):
    """Update an agent."""
    agent = await session.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    update_data = agent_update.model_dump(exclude_unset=True)
    if "name" in update_data:
        existing = await session.execute(select(Agent).where(Agent.name == update_data["name"], Agent.id != agent_id))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Agent with this name already exists")

    for field, value in update_data.items():
        setattr(agent, field, value)

    await session.commit()
    await session.refresh(agent)
    return agent


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Delete an agent."""
    agent = await session.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    await session.delete(agent)
    await session.commit()