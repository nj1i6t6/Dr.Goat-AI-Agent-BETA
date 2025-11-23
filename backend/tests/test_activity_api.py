from datetime import datetime

from app import db
from app.models import Sheep, SheepEvent, User
from app.services.verifiable_log_service import append_event


def test_activity_logs_returns_entries(authenticated_client, app, test_sheep):
    with app.app_context():
        user = User.query.filter_by(username='testuser').first()
        sheep = Sheep.query.filter_by(user_id=user.id).first()

        event = SheepEvent(
            user_id=user.id,
            sheep_id=sheep.id,
            event_date='2024-01-05',
            event_type='疫苗接種',
            description='口蹄疫加強針',
            notes='定期免疫',
            recorded_at=datetime.utcnow(),
        )
        db.session.add(event)
        db.session.commit()

        append_event(
            entity_type='sheep_event',
            entity_id=event.id,
            event={
                'action': 'create',
                'summary': f'羊隻 {sheep.EarNum} 事件 {event.event_type}',
                'actor': {'username': 'testuser'},
                'metadata': {
                    'description': event.description,
                    'event_type': event.event_type,
                    'severity': 'warning',
                    'medication': '疫苗',
                },
            },
        )

    response = authenticated_client.get('/api/activity/logs?page=1&page_size=10')
    assert response.status_code == 200
    data = response.get_json()

    assert data['page'] == 1
    assert data['page_size'] == 10
    assert data['total'] == 1
    assert data['has_more'] is False

    items = data['items']
    assert isinstance(items, list)
    assert len(items) == 1

    entry = items[0]
    assert entry['actor'] == 'testuser'
    assert '疫苗接種' in entry['message']
    assert entry['severity'] == 'warning'
    assert entry['entityType'] == 'sheep_event'
    assert entry['metadata']['event_type'] == '疫苗接種'


def test_activity_logs_reflects_recent_append_event(authenticated_client, app, test_sheep):
    with app.app_context():
        user = User.query.filter_by(username='testuser').first()
        sheep = Sheep.query.filter_by(user_id=user.id).first()

        event = SheepEvent(
            user_id=user.id,
            sheep_id=sheep.id,
            event_date='2024-01-10',
            event_type='補給記錄',
            description='新增維生素補給',
            notes='自動化測試事件',
            recorded_at=datetime.utcnow(),
        )
        db.session.add(event)
        db.session.flush()

        append_event(
            entity_type='sheep_event',
            entity_id=event.id,
            event={
                'action': 'create',
                'summary': f'羊隻 {sheep.EarNum} 事件 {event.event_type}',
                'actor': {'username': 'testuser'},
                'metadata': {
                    'description': event.description,
                    'event_type': event.event_type,
                },
            },
        )
        db.session.commit()

    response = authenticated_client.get('/api/activity/logs?page=1&page_size=5')
    assert response.status_code == 200
    data = response.get_json()

    assert data['total'] > 0
    assert any('補給記錄' in item['message'] for item in data['items'])


def test_activity_logs_empty_response(authenticated_client):
    response = authenticated_client.get('/api/activity/logs?page=1&page_size=5')
    assert response.status_code == 200
    data = response.get_json()

    assert data['items'] == []
    assert data['total'] == 0
    assert data['has_more'] is False
