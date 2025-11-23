from datetime import datetime, date
from typing import Any, Dict, List

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from pydantic import ValidationError
from app.models import (
    db,
    ProductBatch,
    ProcessingStep,
    BatchSheepAssociation,
    Sheep,
    SheepEvent,
    SheepHistoricalData,
    VerifiableLog,
)
from app.schemas import (
    ProductBatchCreateModel,
    ProductBatchUpdateModel,
    ProcessingStepCreateModel,
    ProcessingStepUpdateModel,
    BatchSheepLinkModel,
    create_error_response,
)
from app.services.verifiable_log_service import append_event, serialize_entry
from app.utils import normalise_json_payload

bp = Blueprint('traceability', __name__)


def _ensure_authenticated_response():
    if not current_user.is_authenticated:
        return jsonify(error='Login required'), 401
    return None
def _log_traceability_event(
    entity_type: str,
    entity_id: int,
    action: str,
    summary: str,
    metadata: Dict[str, Any] | None = None,
):
    actor = None
    if current_user.is_authenticated:
        actor = {
            'id': getattr(current_user, 'id', None),
            'username': getattr(current_user, 'username', None),
        }
    append_event(
        entity_type=entity_type,
        entity_id=entity_id,
        event={
            'action': action,
            'summary': summary,
            'actor': actor,
            'metadata': normalise_json_payload(metadata or {}),
        },
    )


def _load_step_fingerprints(step_ids: List[int]) -> Dict[int, List[Dict[str, Any]]]:
    if not step_ids:
        return {}
    entries = (
        VerifiableLog.query.filter(
            VerifiableLog.entity_type == 'processing_step',
            VerifiableLog.entity_id.in_(step_ids),
        )
        .order_by(VerifiableLog.entity_id.asc(), VerifiableLog.id.asc())
        .all()
    )
    mapping: Dict[int, List[Dict[str, Any]]] = {step_id: [] for step_id in step_ids}
    for entry in entries:
        mapping.setdefault(entry.entity_id, []).append(serialize_entry(entry))
    return mapping


def _serialize_batch(batch: ProductBatch, include_relationships: bool = False):
    data = batch.to_dict(include_relationships=include_relationships)
    if include_relationships:
        steps = sorted(batch.steps, key=lambda s: (s.sequence_order or 0, s.id))
        step_fingerprints = _load_step_fingerprints([step.id for step in steps])
        enriched_steps = []
        for step in steps:
            payload = step.to_dict()
            payload['fingerprints'] = step_fingerprints.get(step.id, [])
            enriched_steps.append(payload)
        data['steps'] = enriched_steps
        links_payload = []
        for link in batch.sheep_links:
            payload = link.to_dict(include_sheep=True)
            if 'sheep' in payload:
                sheep_payload = payload['sheep']
                # 移除內部欄位
                sheep_payload.pop('user_id', None)
                sheep_payload.pop('last_updated', None)
                payload['sheep'] = sheep_payload
            links_payload.append(payload)
        data['sheep_links'] = links_payload
    return data


def _ensure_batch_ownership(batch_id: int) -> ProductBatch:
    batch = ProductBatch.query.filter_by(id=batch_id, user_id=current_user.id).first()
    return batch


def _validate_sheep_links(user_id: int, link_models):
    sheep_ids = [link.sheep_id for link in link_models]
    if not sheep_ids:
        return {}
    sheep_records = Sheep.query.filter(Sheep.user_id == user_id, Sheep.id.in_(sheep_ids)).all()
    found_ids = {sheep.id for sheep in sheep_records}
    missing = set(sheep_ids) - found_ids
    if missing:
        raise ValueError(f"找不到以下羊隻或您沒有權限: {', '.join(map(str, missing))}")
    return {sheep.id: sheep for sheep in sheep_records}


def _upsert_sheep_links(batch: ProductBatch, link_models, sheep_lookup):
    existing_links = {link.sheep_id: link for link in batch.sheep_links}
    processed_ids = set()

    for link_model in link_models:
        payload = {
            'contribution_type': link_model.contribution_type,
            'quantity': link_model.quantity,
            'quantity_unit': link_model.quantity_unit,
            'role': link_model.role,
            'notes': link_model.notes,
        }
        if link_model.sheep_id in existing_links:
            link = existing_links[link_model.sheep_id]
            for key, value in payload.items():
                setattr(link, key, value)
        else:
            link = BatchSheepAssociation(batch=batch, sheep=sheep_lookup[link_model.sheep_id], **payload)
            db.session.add(link)
        processed_ids.add(link_model.sheep_id)

    # 刪除未出現在新陣列中的舊關聯
    for sheep_id, link in existing_links.items():
        if sheep_id not in processed_ids:
            db.session.delete(link)


def _build_public_story(batch: ProductBatch):
    steps = sorted(batch.steps, key=lambda s: (s.sequence_order or 0, s.started_at or datetime.min))
    step_fingerprints = _load_step_fingerprints([step.id for step in steps])
    timeline = []
    for step in steps:
        timeline.append({
            'title': step.title,
            'description': step.description,
            'sequence_order': step.sequence_order,
            'started_at': step.started_at.isoformat() if step.started_at else None,
            'completed_at': step.completed_at.isoformat() if step.completed_at else None,
            'evidence_url': step.evidence_url,
            'fingerprints': step_fingerprints.get(step.id, []),
        })

    sheep_details = []
    for link in batch.sheep_links:
        sheep = link.sheep
        if not sheep:
            continue
        events = SheepEvent.query.filter_by(sheep_id=sheep.id).order_by(SheepEvent.event_date.desc()).limit(10).all()
        history_records = SheepHistoricalData.query.filter_by(sheep_id=sheep.id).order_by(SheepHistoricalData.record_date.desc()).limit(10).all()

        sheep_payload = sheep.to_dict()
        sheep_payload.pop('user_id', None)
        sheep_payload.pop('last_updated', None)

        link_payload = {
            'role': link.role,
            'contribution_type': link.contribution_type,
            'quantity': link.quantity,
            'quantity_unit': link.quantity_unit,
            'notes': link.notes,
        }

        sheep_details.append({
            'link': link_payload,
            'sheep': sheep_payload,
            'recent_events': [
                {
                    'event_date': event.event_date,
                    'event_type': event.event_type,
                    'description': event.description,
                    'notes': event.notes,
                    'medication': event.medication,
                    'withdrawal_days': event.withdrawal_days,
                }
                for event in events
            ],
            'recent_history': [
                {
                    'record_date': record.record_date,
                    'record_type': record.record_type,
                    'value': record.value,
                    'notes': record.notes,
                }
                for record in history_records
            ],
        })

    batch_payload = {
        'batch_number': batch.batch_number,
        'product_name': batch.product_name,
        'product_type': batch.product_type,
        'description': batch.description,
        'esg_highlights': batch.esg_highlights,
        'production_date': batch.production_date.isoformat() if batch.production_date else None,
        'expiration_date': batch.expiration_date.isoformat() if batch.expiration_date else None,
        'origin_story': batch.origin_story,
        'is_public': batch.is_public,
        'last_updated': batch.updated_at.isoformat() if batch.updated_at else None,
    }

    story = {
        'batch': batch_payload,
        'processing_timeline': timeline,
        'sheep_details': sheep_details,
    }

    return story


@bp.route('/batches', methods=['GET'])
@login_required
def list_batches():
    if (unauth := _ensure_authenticated_response()) is not None:
        return unauth
    include_details = request.args.get('include_details', 'false').lower() == 'true'
    batches = ProductBatch.query.filter_by(user_id=current_user.id).order_by(ProductBatch.created_at.desc()).all()
    return jsonify([_serialize_batch(batch, include_relationships=include_details) for batch in batches])


@bp.route('/batches', methods=['POST'])
@login_required
def create_batch():
    if (unauth := _ensure_authenticated_response()) is not None:
        return unauth
    if not request.is_json:
        return jsonify(error='請求必須為 JSON'), 400

    try:
        payload = ProductBatchCreateModel(**request.get_json())
    except ValidationError as e:
        return jsonify(create_error_response('資料驗證失敗', e.errors())), 400

    batch = ProductBatch(
        user_id=current_user.id,
        batch_number=payload.batch_number,
        product_name=payload.product_name,
        product_type=payload.product_type,
        description=payload.description,
        esg_highlights=payload.esg_highlights,
        production_date=payload.production_date,
        expiration_date=payload.expiration_date,
        origin_story=payload.origin_story,
        is_public=payload.is_public,
    )

    if payload.processing_steps:
        for index, step_model in enumerate(payload.processing_steps, start=1):
            sequence = step_model.sequence_order or index
            step = ProcessingStep(
                title=step_model.title,
                description=step_model.description,
                sequence_order=sequence,
                started_at=step_model.started_at,
                completed_at=step_model.completed_at,
                evidence_url=step_model.evidence_url,
            )
            batch.steps.append(step)

    try:
        db.session.add(batch)
        db.session.flush()

        _log_traceability_event(
            'product_batch',
            batch.id,
            'create',
            f'建立批次 {batch.batch_number}',
            {
                'batch_number': batch.batch_number,
                'product_name': batch.product_name,
                'is_public': batch.is_public,
            },
        )

        if batch.steps:
            for step in batch.steps:
                _log_traceability_event(
                    'processing_step',
                    step.id,
                    'create',
                    f'建立加工步驟 {step.title}',
                    {
                        'batch_id': batch.id,
                        'sequence_order': step.sequence_order,
                        'evidence_url': step.evidence_url,
                    },
                )

        if payload.sheep_links:
            sheep_lookup = _validate_sheep_links(current_user.id, payload.sheep_links)
            _upsert_sheep_links(batch, payload.sheep_links, sheep_lookup)
            _log_traceability_event(
                'product_batch',
                batch.id,
                'link',
                f'批次 {batch.batch_number} 設定羊隻關聯',
                {
                    'linked_sheep_ids': [link.sheep_id for link in batch.sheep_links],
                },
            )

        db.session.commit()
        return jsonify(_serialize_batch(batch, include_relationships=True)), 201
    except IntegrityError as e:
        db.session.rollback()
        return jsonify(error='批次號需保持唯一，請使用其他批次號'), 409
    except ValueError as e:
        db.session.rollback()
        return jsonify(error=str(e)), 400
    except Exception as e:
        db.session.rollback()
        return jsonify(error=f'建立批次失敗: {e}'), 500


@bp.route('/batches/<int:batch_id>', methods=['GET'])
@login_required
def get_batch(batch_id):
    if (unauth := _ensure_authenticated_response()) is not None:
        return unauth
    batch = _ensure_batch_ownership(batch_id)
    if not batch:
        return jsonify(error='找不到批次或您沒有權限'), 404
    return jsonify(_serialize_batch(batch, include_relationships=True))


@bp.route('/batches/<int:batch_id>', methods=['PUT'])
@login_required
def update_batch(batch_id):
    if (unauth := _ensure_authenticated_response()) is not None:
        return unauth
    if not request.is_json:
        return jsonify(error='請求必須為 JSON'), 400

    batch = _ensure_batch_ownership(batch_id)
    if not batch:
        return jsonify(error='找不到批次或您沒有權限'), 404

    try:
        payload = ProductBatchUpdateModel(**request.get_json())
    except ValidationError as e:
        return jsonify(create_error_response('資料驗證失敗', e.errors())), 400

    tracked_fields = ['product_name', 'product_type', 'description', 'esg_highlights', 'production_date', 'expiration_date', 'origin_story', 'is_public']
    original_state = {field: getattr(batch, field) for field in tracked_fields}

    for field in tracked_fields:
        value = getattr(payload, field)
        if value is not None:
            setattr(batch, field, value)

    try:
        metadata: Dict[str, Any] = {}
        changed_fields = {}
        for field in tracked_fields:
            previous = original_state[field]
            current = getattr(batch, field)
            if previous != current:
                changed_fields[field] = {
                    'old': normalise_json_payload(previous),
                    'new': normalise_json_payload(current),
                }

        if payload.sheep_links is not None:
            sheep_lookup = _validate_sheep_links(current_user.id, payload.sheep_links)
            _upsert_sheep_links(batch, payload.sheep_links, sheep_lookup)
            metadata['linked_sheep_ids'] = [link.sheep_id for link in batch.sheep_links]

        if changed_fields:
            metadata['changed_fields'] = changed_fields

        if metadata:
            _log_traceability_event(
                'product_batch',
                batch.id,
                'update',
                f'更新批次 {batch.batch_number}',
                metadata,
            )

        db.session.commit()
        return jsonify(_serialize_batch(batch, include_relationships=True))
    except ValueError as e:
        db.session.rollback()
        return jsonify(error=str(e)), 400
    except Exception as e:
        db.session.rollback()
        return jsonify(error=f'更新批次失敗: {e}'), 500


@bp.route('/batches/<int:batch_id>', methods=['DELETE'])
@login_required
def delete_batch(batch_id):
    if (unauth := _ensure_authenticated_response()) is not None:
        return unauth
    batch = _ensure_batch_ownership(batch_id)
    if not batch:
        return jsonify(error='找不到批次或您沒有權限'), 404
    try:
        _log_traceability_event(
            'product_batch',
            batch.id,
            'delete',
            f'刪除批次 {batch.batch_number}',
            {
                'batch_number': batch.batch_number,
                'total_steps': len(batch.steps),
                'linked_sheep_ids': [link.sheep_id for link in batch.sheep_links],
            },
        )
        db.session.delete(batch)
        db.session.commit()
        return jsonify(success=True, message='批次已刪除')
    except Exception as e:
        db.session.rollback()
        return jsonify(error=f'刪除批次失敗: {e}'), 500


@bp.route('/batches/<int:batch_id>/steps', methods=['POST'])
@login_required
def add_step(batch_id):
    if (unauth := _ensure_authenticated_response()) is not None:
        return unauth
    if not request.is_json:
        return jsonify(error='請求必須為 JSON'), 400

    batch = _ensure_batch_ownership(batch_id)
    if not batch:
        return jsonify(error='找不到批次或您沒有權限'), 404

    try:
        payload = ProcessingStepCreateModel(**request.get_json())
    except ValidationError as e:
        return jsonify(create_error_response('資料驗證失敗', e.errors())), 400

    sequence = payload.sequence_order or (batch.steps[-1].sequence_order + 1 if batch.steps else 1)
    step = ProcessingStep(
        batch=batch,
        title=payload.title,
        description=payload.description,
        sequence_order=sequence,
        started_at=payload.started_at,
        completed_at=payload.completed_at,
        evidence_url=payload.evidence_url,
    )
    try:
        db.session.add(step)
        db.session.flush()
        _log_traceability_event(
            'processing_step',
            step.id,
            'create',
            f'批次 {batch.batch_number} 新增步驟 {step.title}',
            {
                'batch_id': batch.id,
                'sequence_order': step.sequence_order,
                'evidence_url': step.evidence_url,
            },
        )
        db.session.commit()
        return jsonify(step.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify(error=f'新增步驟失敗: {e}'), 500


@bp.route('/steps/<int:step_id>', methods=['PUT'])
@login_required
def update_step(step_id):
    if (unauth := _ensure_authenticated_response()) is not None:
        return unauth
    if not request.is_json:
        return jsonify(error='請求必須為 JSON'), 400

    step = ProcessingStep.query.options(joinedload(ProcessingStep.batch)).filter_by(id=step_id).first()
    if not step or step.batch.user_id != current_user.id:
        return jsonify(error='找不到步驟或您沒有權限'), 404

    try:
        payload = ProcessingStepUpdateModel(**request.get_json())
    except ValidationError as e:
        return jsonify(create_error_response('資料驗證失敗', e.errors())), 400

    tracked_fields = ['title', 'description', 'sequence_order', 'started_at', 'completed_at', 'evidence_url']
    original_state = {field: getattr(step, field) for field in tracked_fields}

    for field in tracked_fields:
        value = getattr(payload, field)
        if value is not None:
            setattr(step, field, value)

    try:
        changed_fields = {}
        for field in tracked_fields:
            previous = original_state[field]
            current = getattr(step, field)
            if previous != current:
                changed_fields[field] = {
                    'old': normalise_json_payload(previous),
                    'new': normalise_json_payload(current),
                }

        if changed_fields:
            _log_traceability_event(
                'processing_step',
                step.id,
                'update',
                f'更新步驟 {step.title}',
                {
                    'batch_id': step.batch_id,
                    'changed_fields': changed_fields,
                },
            )

        db.session.commit()
        return jsonify(step.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify(error=f'更新步驟失敗: {e}'), 500


@bp.route('/steps/<int:step_id>', methods=['DELETE'])
@login_required
def delete_step(step_id):
    if (unauth := _ensure_authenticated_response()) is not None:
        return unauth
    step = ProcessingStep.query.options(joinedload(ProcessingStep.batch)).filter_by(id=step_id).first()
    if not step or step.batch.user_id != current_user.id:
        return jsonify(error='找不到步驟或您沒有權限'), 404
    try:
        _log_traceability_event(
            'processing_step',
            step.id,
            'delete',
            f'刪除步驟 {step.title}',
            {
                'batch_id': step.batch_id,
                'sequence_order': step.sequence_order,
            },
        )
        db.session.delete(step)
        db.session.commit()
        return jsonify(success=True, message='步驟已刪除')
    except Exception as e:
        db.session.rollback()
        return jsonify(error=f'刪除步驟失敗: {e}'), 500


@bp.route('/batches/<int:batch_id>/sheep', methods=['POST'])
@login_required
def replace_sheep_links(batch_id):
    if (unauth := _ensure_authenticated_response()) is not None:
        return unauth
    if not request.is_json:
        return jsonify(error='請求必須為 JSON'), 400

    batch = _ensure_batch_ownership(batch_id)
    if not batch:
        return jsonify(error='找不到批次或您沒有權限'), 404

    data = request.get_json()
    sheep_links_data = data.get('sheep_links')
    if sheep_links_data is None:
        return jsonify(error='請提供 sheep_links 陣列'), 400

    try:
        link_models = [BatchSheepLinkModel(**item) for item in sheep_links_data]
        sheep_lookup = _validate_sheep_links(current_user.id, link_models)
        _upsert_sheep_links(batch, link_models, sheep_lookup)
        _log_traceability_event(
            'product_batch',
            batch.id,
            'link',
            f'批次 {batch.batch_number} 更新羊隻關聯',
            {
                'linked_sheep_ids': [link.sheep_id for link in batch.sheep_links],
                'total_links': len(batch.sheep_links),
            },
        )
        db.session.commit()
        return jsonify(_serialize_batch(batch, include_relationships=True))
    except ValidationError as e:
        return jsonify(create_error_response('資料驗證失敗', e.errors())), 400
    except ValueError as e:
        db.session.rollback()
        return jsonify(error=str(e)), 400
    except Exception as e:
        db.session.rollback()
        return jsonify(error=f'更新羊隻關聯失敗: {e}'), 500


@bp.route('/batches/<int:batch_id>/sheep/<int:sheep_id>', methods=['DELETE'])
@login_required
def remove_sheep_link(batch_id, sheep_id):
    if (unauth := _ensure_authenticated_response()) is not None:
        return unauth
    batch = _ensure_batch_ownership(batch_id)
    if not batch:
        return jsonify(error='找不到批次或您沒有權限'), 404

    link = BatchSheepAssociation.query.filter_by(batch_id=batch_id, sheep_id=sheep_id).first()
    if not link:
        return jsonify(error='找不到指定羊隻關聯'), 404
    try:
        _log_traceability_event(
            'product_batch',
            batch.id,
            'link',
            f'批次 {batch.batch_number} 移除羊隻 {sheep_id}',
            {
                'removed_sheep_id': sheep_id,
                'remaining_sheep_ids': [association.sheep_id for association in batch.sheep_links if association.sheep_id != sheep_id],
            },
        )
        db.session.delete(link)
        db.session.commit()
        return jsonify(success=True, message='羊隻已移除')
    except Exception as e:
        db.session.rollback()
        return jsonify(error=f'移除羊隻失敗: {e}'), 500


@bp.route('/public/<string:batch_number>', methods=['GET'])
def public_trace(batch_number):
    batch = ProductBatch.query.options(
        joinedload(ProductBatch.steps),
        joinedload(ProductBatch.sheep_links).joinedload(BatchSheepAssociation.sheep),
    ).filter_by(batch_number=batch_number).first()

    if not batch or not batch.is_public:
        return jsonify(error='找不到對應的批次資訊'), 404

    story = _build_public_story(batch)
    return jsonify(story)
