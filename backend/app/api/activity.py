from __future__ import annotations

from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from sqlalchemy import or_, select

from app.models import ProductBatch, ProcessingStep, SheepEvent, VerifiableLog

bp = Blueprint('activity', __name__)

MAX_PAGE_SIZE = 100


def _user_scoped_log_query(user_id: int):
    product_batch_ids = select(ProductBatch.id).where(ProductBatch.user_id == user_id)
    processing_step_ids = (
        select(ProcessingStep.id)
        .join(ProductBatch, ProcessingStep.batch_id == ProductBatch.id)
        .where(ProductBatch.user_id == user_id)
    )
    sheep_event_ids = select(SheepEvent.id).where(SheepEvent.user_id == user_id)

    return VerifiableLog.query.filter(
        or_(
            (VerifiableLog.entity_type == 'product_batch')
            & VerifiableLog.entity_id.in_(product_batch_ids),
            (VerifiableLog.entity_type == 'processing_step')
            & VerifiableLog.entity_id.in_(processing_step_ids),
            (VerifiableLog.entity_type == 'sheep_event')
            & VerifiableLog.entity_id.in_(sheep_event_ids),
        )
    )


def _normalise_actor(event_data: dict | None) -> str:
    actor_info = (event_data or {}).get('actor') or {}
    for key in ('username', 'name', 'display_name', 'id'):
        value = actor_info.get(key)
        if value:
            return str(value)
    return '系統'


def _classify_severity(event_data: dict | None) -> str:
    if not event_data:
        return 'info'

    metadata = event_data.get('metadata') or {}
    explicit = (metadata.get('severity') or event_data.get('severity') or '').lower()
    allowed = {'success', 'info', 'warning', 'danger', 'error'}
    if explicit in allowed:
        return 'danger' if explicit == 'error' else explicit

    haystack = ' '.join(
        filter(
            None,
            [
                str(event_data.get('action') or ''),
                str(event_data.get('summary') or ''),
                str(metadata.get('event_type') or ''),
                str(metadata.get('description') or ''),
            ],
        )
    )

    danger_markers = ('刪除', '失敗', '錯誤', '異常')
    if any(marker in haystack for marker in danger_markers):
        return 'danger'

    warning_markers = ('停藥', '警', '注意', '警示', '提醒')
    if any(marker in haystack for marker in warning_markers):
        return 'warning'

    success_markers = ('完成', '成功', '新增', '建立', '已更新')
    if any(marker in haystack for marker in success_markers):
        return 'success'

    if metadata.get('withdrawal_days') or metadata.get('medication'):
        return 'warning'

    return 'info'


def _format_message(event_data: dict | None, fallback: str) -> str:
    if not event_data:
        return fallback
    summary = event_data.get('summary') or fallback
    metadata = event_data.get('metadata') or {}
    description = metadata.get('description')
    if description and description not in summary:
        return f"{summary}｜{description}"
    return summary


def _serialize_entry(entry: VerifiableLog) -> dict:
    event_data = entry.event_data or {}
    message = _format_message(
        event_data,
        fallback=f"{entry.entity_type} #{entry.entity_id}",
    )

    timestamp = entry.timestamp
    if isinstance(timestamp, datetime):
        timestamp_iso = timestamp.isoformat(timespec='seconds')
    else:
        timestamp_iso = str(timestamp)

    return {
        'id': entry.id,
        'timestamp': timestamp_iso,
        'actor': _normalise_actor(event_data),
        'message': message,
        'severity': _classify_severity(event_data),
        'entityType': entry.entity_type,
        'entityId': entry.entity_id,
        'metadata': event_data.get('metadata') or {},
    }


@bp.route('/logs', methods=['GET'])
@login_required
def list_activity_logs():
    page = max(int(request.args.get('page', 1) or 1), 1)
    page_size = int(request.args.get('page_size', 20) or 20)
    page_size = min(max(page_size, 1), MAX_PAGE_SIZE)

    query = _user_scoped_log_query(current_user.id)
    total = query.order_by(None).count()

    entries = (
        query.order_by(VerifiableLog.timestamp.desc(), VerifiableLog.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = [_serialize_entry(entry) for entry in entries]
    has_more = page * page_size < total

    return jsonify(
        {
            'items': items,
            'page': page,
            'page_size': page_size,
            'total': total,
            'has_more': has_more,
        }
    )
