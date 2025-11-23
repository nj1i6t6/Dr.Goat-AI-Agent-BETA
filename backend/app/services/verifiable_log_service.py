"""Helpers for managing the verifiable append-only log."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Dict, Iterable, List, Optional, Set

from sqlalchemy import or_, select

try:
    from sqlalchemy.orm.session import SessionTransactionOrigin
except ImportError:  # pragma: no cover - fallback for older SQLAlchemy
    SessionTransactionOrigin = None

from app import db
from app.models import ProductBatch, ProcessingStep, SheepEvent, VerifiableLog
from app.schemas import VerifiableLogEventModel
from app.utils import normalise_json_payload

from .hash_service import HashService


LEDGER_VERIFICATION_BATCH_SIZE = 200


def append_event(
    *,
    entity_type: str,
    entity_id: int,
    event: VerifiableLogEventModel | Dict[str, Any],
) -> VerifiableLog:
    """Append a new log entry for the given entity."""

    event_model = event if isinstance(event, VerifiableLogEventModel) else VerifiableLogEventModel(**event)
    payload = event_model.model_dump()
    payload["metadata"] = normalise_json_payload(payload.get("metadata") or {})

    session = db.session

    def _append() -> VerifiableLog:
        previous_entry = _lock_current_tail()
        timestamp = datetime.utcnow()
        previous_hash = previous_entry.current_hash if previous_entry else None

        hash_payload = {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "event_data": payload,
            "timestamp": timestamp.isoformat(timespec="microseconds"),
        }
        current_hash = HashService.generate_hash(previous_hash, hash_payload)

        entry = VerifiableLog(
            entity_type=entity_type,
            entity_id=entity_id,
            event_data=payload,
            timestamp=timestamp,
            previous_hash=previous_hash,
            current_hash=current_hash,
        )
        session.add(entry)
        session.flush()
        return entry

    get_current_session = getattr(session, "__call__", None)
    if callable(get_current_session):
        try:
            current_session = get_current_session()
        except RuntimeError:
            current_session = None
    else:
        current_session = session

    should_defer_commit = False
    if current_session is not None:
        get_transaction = getattr(current_session, "get_transaction", None)
        current_tx = get_transaction() if callable(get_transaction) else None
        if current_tx is not None:
            origin = getattr(current_tx, "origin", None)
            if SessionTransactionOrigin is not None and origin is not None:
                should_defer_commit = origin is not SessionTransactionOrigin.AUTOBEGIN
            else:
                parent = getattr(current_tx, "parent", None)
                nested = getattr(current_tx, "nested", False)
                if parent is not None or nested:
                    should_defer_commit = True
                else:
                    in_transaction = getattr(current_session, "in_transaction", None)
                    should_defer_commit = callable(in_transaction) and in_transaction()
        else:
            in_transaction = getattr(current_session, "in_transaction", None)
            should_defer_commit = callable(in_transaction) and in_transaction()

    if should_defer_commit:
        return _append()

    try:
        entry = _append()
        session.commit()
    except Exception:
        session.rollback()
        raise

    return entry


def verify_chain(*, start_id: Optional[int] = None, limit: Optional[int] = None) -> Dict[str, Any]:
    """Verify the entire log chain."""

    query = VerifiableLog.query.order_by(VerifiableLog.id.asc())
    if start_id is not None:
        query = query.filter(VerifiableLog.id >= start_id)
    if limit is not None:
        query = query.limit(limit)

    previous_hash: Optional[str] = None
    checked = 0
    broken_at_id: Optional[int] = None
    last_hash: Optional[str] = None

    for entry in query.yield_per(LEDGER_VERIFICATION_BATCH_SIZE):
        if previous_hash is None and start_id is None and entry.previous_hash not in (None, ""):
            broken_at_id = entry.id
            break
        if previous_hash is not None and entry.previous_hash != previous_hash:
            broken_at_id = entry.id
            break

        timestamp_iso = entry.timestamp.isoformat(timespec="microseconds")
        hash_payload = {
            "entity_type": entry.entity_type,
            "entity_id": entry.entity_id,
            "event_data": entry.event_data,
            "timestamp": timestamp_iso,
        }
        computed_hash = HashService.generate_hash(entry.previous_hash, hash_payload)
        if computed_hash != entry.current_hash:
            broken_at_id = entry.id
            break

        previous_hash = entry.current_hash
        last_hash = entry.current_hash
        checked += 1

    integrity = "FAILED" if broken_at_id is not None else "OK"
    return {
        "integrity": integrity,
        "broken_at_id": broken_at_id,
        "checked": checked,
        "last_hash": last_hash,
    }


def list_entity_entries(
    entity_type: str,
    entity_id: int,
    *,
    user_id: int,
) -> Optional[List[Dict[str, Any]]]:
    """Return serialised log entries for a specific entity, scoped to a user."""

    allowed_ids = _owned_ids_for_type(entity_type, {entity_id}, user_id)
    if entity_id not in allowed_ids:
        return None

    entries: Iterable[VerifiableLog] = (
        VerifiableLog.query.filter_by(entity_type=entity_type, entity_id=entity_id)
        .order_by(VerifiableLog.id.asc())
        .all()
    )

    return [serialize_entry(entry) for entry in entries]


def serialize_entry(entry: VerifiableLog) -> Dict[str, Any]:
    """Serialise a log entry for API responses."""

    return {
        "id": entry.id,
        "entity_type": entry.entity_type,
        "entity_id": entry.entity_id,
        "timestamp": entry.timestamp.isoformat(timespec="microseconds"),
        "previous_hash": entry.previous_hash,
        "current_hash": entry.current_hash,
        "event_data": entry.event_data,
    }


def recent_entries(limit: int = 100, *, user_id: int) -> List[Dict[str, Any]]:
    """Return the most recent log entries visible to the user in chronological order."""

    limit = max(limit, 1)

    conditions = []

    product_batch_ids = select(ProductBatch.id).where(ProductBatch.user_id == user_id)
    conditions.append(
        (VerifiableLog.entity_type == "product_batch")
        & VerifiableLog.entity_id.in_(product_batch_ids)
    )

    processing_step_ids = (
        select(ProcessingStep.id)
        .join(ProductBatch, ProcessingStep.batch_id == ProductBatch.id)
        .where(ProductBatch.user_id == user_id)
    )
    conditions.append(
        (VerifiableLog.entity_type == "processing_step")
        & VerifiableLog.entity_id.in_(processing_step_ids)
    )

    sheep_event_ids = select(SheepEvent.id).where(SheepEvent.user_id == user_id)
    conditions.append(
        (VerifiableLog.entity_type == "sheep_event")
        & VerifiableLog.entity_id.in_(sheep_event_ids)
    )

    entries = (
        VerifiableLog.query.filter(or_(*conditions))
        .order_by(VerifiableLog.id.desc())
        .limit(limit)
        .all()
    )

    return [serialize_entry(entry) for entry in reversed(entries)]


def _owned_ids_for_type(entity_type: str, entity_ids: Iterable[int], user_id: int) -> Set[int]:
    ids = {int(entity_id) for entity_id in entity_ids if entity_id is not None}
    if not ids:
        return set()

    query_factory = OWNERSHIP_QUERY_FACTORIES.get(entity_type)
    if query_factory is None:
        return set()

    rows = query_factory(ids, user_id).all()
    return {row[0] for row in rows}


def _lock_current_tail() -> Optional[VerifiableLog]:
    """以行級鎖鎖定並取得當前尾端條目。需在交易中呼叫以序列化 append 操作。"""

    return (
        VerifiableLog.query.order_by(VerifiableLog.id.desc()).with_for_update().first()
    )


def _product_batch_ownership_query(entity_ids: Set[int], user_id: int):
    return (
        ProductBatch.query.with_entities(ProductBatch.id)
        .filter(ProductBatch.id.in_(entity_ids), ProductBatch.user_id == user_id)
    )


def _processing_step_ownership_query(entity_ids: Set[int], user_id: int):
    return (
        ProcessingStep.query.with_entities(ProcessingStep.id)
        .join(ProductBatch, ProcessingStep.batch_id == ProductBatch.id)
        .filter(ProcessingStep.id.in_(entity_ids), ProductBatch.user_id == user_id)
    )


def _sheep_event_ownership_query(entity_ids: Set[int], user_id: int):
    return (
        SheepEvent.query.with_entities(SheepEvent.id)
        .filter(SheepEvent.id.in_(entity_ids), SheepEvent.user_id == user_id)
    )


OWNERSHIP_QUERY_FACTORIES: Dict[str, Callable[[Set[int], int], Any]] = {
    "product_batch": _product_batch_ownership_query,
    "processing_step": _processing_step_ownership_query,
    "sheep_event": _sheep_event_ownership_query,
}
