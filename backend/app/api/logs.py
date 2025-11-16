from __future__ import annotations

from fastapi import APIRouter

from engine.logging import log_store

from ..models.schemas import LogRecordModel

router = APIRouter(prefix="/api/logs")


@router.get("/", response_model=list[LogRecordModel])
def list_logs(limit: int = 200):
    return [LogRecordModel(**record.__dict__) for record in log_store.list_recent(limit=limit)]
