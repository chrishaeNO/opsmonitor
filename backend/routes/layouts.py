"""Layouts API – lagre dashboards per organisasjon."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend import models_db
from backend.schemas import LayoutOut, LayoutCreate, LayoutUpdate, LayoutConfig
from backend.auth import get_current_user

router = APIRouter(prefix="/layouts", tags=["layouts"])


@router.get("", response_model=list[LayoutOut])
def list_layouts(
    db: Session = Depends(get_db),
    current_user: models_db.User = Depends(get_current_user),
):
    rows = (
        db.query(models_db.Layout)
        .filter(models_db.Layout.organization_id == current_user.organization_id)
        .order_by(models_db.Layout.created_at.asc())
        .all()
    )
    return [
        LayoutOut(
            id=row.id,
            name=row.name,
            config=LayoutConfig(**row.config),
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
        for row in rows
    ]


@router.post("", response_model=LayoutOut, status_code=status.HTTP_201_CREATED)
def create_layout(
    payload: LayoutCreate,
    db: Session = Depends(get_db),
    current_user: models_db.User = Depends(get_current_user),
):
    row = models_db.Layout(
        organization_id=current_user.organization_id,
        name=payload.name,
        config=payload.config.dict(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return LayoutOut(
        id=row.id,
        name=row.name,
        config=LayoutConfig(**row.config),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.put("/{layout_id}", response_model=LayoutOut)
def update_layout(
    layout_id: int,
    payload: LayoutUpdate,
    db: Session = Depends(get_db),
    current_user: models_db.User = Depends(get_current_user),
):
    row = (
        db.query(models_db.Layout)
        .filter(
            models_db.Layout.id == layout_id,
            models_db.Layout.organization_id == current_user.organization_id,
        )
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Layout ikke funnet")
    if payload.name is not None:
        row.name = payload.name
    if payload.config is not None:
        row.config = payload.config.dict()
    db.commit()
    db.refresh(row)
    return LayoutOut(
        id=row.id,
        name=row.name,
        config=LayoutConfig(**row.config),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.delete("/{layout_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_layout(
    layout_id: int,
    db: Session = Depends(get_db),
    current_user: models_db.User = Depends(get_current_user),
):
    row = (
        db.query(models_db.Layout)
        .filter(
            models_db.Layout.id == layout_id,
            models_db.Layout.organization_id == current_user.organization_id,
        )
        .first()
    )
    if not row:
        return
    db.delete(row)
    db.commit()

