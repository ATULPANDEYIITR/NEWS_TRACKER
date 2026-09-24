from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.source import Source
from app.schemas.source import SourceCreate, SourceResponse


router = APIRouter(
    prefix="/sources",
    tags=["Sources"],
)


@router.post(
    "",
    response_model=SourceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_source(
    source_data: SourceCreate,
    db: Session = Depends(get_db),
) -> Source:
    existing_source = db.scalar(
        select(Source).where(Source.name == source_data.name)
    )

    if existing_source:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A source with this name already exists.",
        )

    source = Source(**source_data.model_dump())

    db.add(source)
    db.commit()
    db.refresh(source)

    return source


@router.get(
    "",
    response_model=list[SourceResponse],
)
def list_sources(
    db: Session = Depends(get_db),
) -> list[Source]:
    statement = (
        select(Source)
        .order_by(Source.name.asc())
    )

    return list(db.scalars(statement).all())


@router.get(
    "/{source_id}",
    response_model=SourceResponse,
)
def get_source(
    source_id: int,
    db: Session = Depends(get_db),
) -> Source:
    source = db.get(Source, source_id)

    if source is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source not found.",
        )

    return source
