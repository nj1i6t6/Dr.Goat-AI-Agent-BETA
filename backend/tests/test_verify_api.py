from werkzeug.security import generate_password_hash

from app import db
from app.models import ProductBatch, User
from app.services.verifiable_log_service import append_event


def _event(summary: str):
    return {
        'action': 'create',
        'summary': summary,
        'metadata': {'summary': summary},
    }


def test_verify_chain_endpoint_returns_ok(authenticated_client, app):
    with app.app_context():
        user = User.query.filter_by(username='testuser').first()

        batch = ProductBatch(
            user_id=user.id,
            batch_number='TEST-BATCH-001',
            product_name='Test Product',
        )
        db.session.add(batch)

        other_user = User(
            username='otheruser',
            password_hash=generate_password_hash('otherpass'),
        )
        db.session.add(other_user)
        db.session.flush()

        other_batch = ProductBatch(
            user_id=other_user.id,
            batch_number='TEST-BATCH-OTHER',
            product_name='Other Product',
        )
        db.session.add(other_batch)
        db.session.commit()

        append_event(entity_type='product_batch', entity_id=batch.id, event=_event('first'))
        db.session.commit()
        append_event(entity_type='product_batch', entity_id=batch.id, event=_event('second'))
        db.session.commit()
        append_event(entity_type='product_batch', entity_id=other_batch.id, event=_event('intruder'))
        db.session.commit()

    response = authenticated_client.get('/api/verify/chain')
    assert response.status_code == 200
    payload = response.get_json()
    assert payload['integrity'] == 'OK'
    assert payload['checked'] >= 2

    response_with_entries = authenticated_client.get('/api/verify/chain?include_entries=true&limit=5')
    assert response_with_entries.status_code == 200
    data = response_with_entries.get_json()
    assert isinstance(data.get('entries'), list)
    assert len(data['entries']) == 2
    summaries = [entry['event_data']['summary'] for entry in data['entries']]
    assert summaries == ['first', 'second']


def test_verify_chain_entity_access_control(authenticated_client, app):
    with app.app_context():
        user = User.query.filter_by(username='testuser').first()
        foreign_user = User(
            username='foreign',
            password_hash=generate_password_hash('foreignpass'),
        )
        db.session.add(foreign_user)
        db.session.commit()

        foreign_batch = ProductBatch(
            user_id=foreign_user.id,
            batch_number='FOREIGN-BATCH-001',
            product_name='Foreign Product',
        )
        db.session.add(foreign_batch)
        db.session.commit()

        append_event(
            entity_type='product_batch',
            entity_id=foreign_batch.id,
            event=_event('foreign'),
        )
        db.session.commit()

        accessible_batch = ProductBatch(
            user_id=user.id,
            batch_number='USER-BATCH-002',
            product_name='User Batch',
        )
        db.session.add(accessible_batch)
        db.session.commit()
        append_event(
            entity_type='product_batch',
            entity_id=accessible_batch.id,
            event=_event('user'),
        )
        db.session.commit()

        foreign_batch_id = foreign_batch.id

    response = authenticated_client.get(f'/api/verify/chain?entity_type=product_batch&entity_id={foreign_batch_id}')
    assert response.status_code == 404

    recent_response = authenticated_client.get('/api/verify/chain?include_entries=true&limit=5')
    assert recent_response.status_code == 200
    entries = recent_response.get_json().get('entries', [])
    assert all(entry['event_data']['summary'] != 'foreign' for entry in entries)
