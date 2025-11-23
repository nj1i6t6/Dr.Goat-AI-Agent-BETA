from app import db
from app import db
from app.models import VerifiableLog
from app.services.verifiable_log_service import append_event, verify_chain


def _base_event(summary: str):
    return {
        'action': 'create',
        'summary': summary,
        'metadata': {'detail': summary},
    }


def test_append_event_builds_hash_chain(app):
    with app.app_context():
        first = append_event(entity_type='test_entity', entity_id=1, event=_base_event('first'))
        db.session.commit()
        second = append_event(entity_type='test_entity', entity_id=1, event=_base_event('second'))
        db.session.commit()

        assert first.current_hash != second.current_hash
        assert second.previous_hash == first.current_hash

        result = verify_chain()
        assert result['integrity'] == 'OK'
        assert result['checked'] >= 2


def test_verify_chain_detects_tampering(app):
    with app.app_context():
        entry = append_event(entity_type='tamper', entity_id=99, event=_base_event('original'))
        db.session.commit()

        db.session.execute(
            VerifiableLog.__table__.update()
            .where(VerifiableLog.id == entry.id)
            .values(
                event_data={
                    'action': 'create',
                    'summary': 'original',
                    'metadata': {'detail': 'tampered'},
                }
            )
        )
        db.session.commit()

        result = verify_chain()
        assert result['integrity'] == 'FAILED'
        assert result['broken_at_id'] == entry.id
