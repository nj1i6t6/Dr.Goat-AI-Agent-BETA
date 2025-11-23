from datetime import datetime, timedelta

from app import db
from app.models import CostEntry, RevenueEntry


def test_create_and_list_costs(authenticated_client, test_sheep):
    payload = {
        'recorded_at': datetime.utcnow().isoformat(),
        'category': 'feed',
        'label': '乾草',
        'amount': 320.5,
        'currency': 'TWD',
        'sheep_id': test_sheep.id,
        'breed': test_sheep.Breed,
        'lactation_number': 2,
        'production_stage': '泌乳期',
        'extra_metadata': {'supplier': 'local-coop'},
    }

    resp = authenticated_client.post('/api/finance/costs', json=payload)
    assert resp.status_code == 201
    cost_id = resp.get_json()['id']

    list_resp = authenticated_client.get('/api/finance/costs')
    data = list_resp.get_json()
    assert data['total'] == 1
    assert data['items'][0]['id'] == cost_id
    assert data['items'][0]['category'] == 'feed'
    assert data['items'][0]['breed'] == test_sheep.Breed

    update_resp = authenticated_client.put(f'/api/finance/costs/{cost_id}', json={'amount': 450})
    assert update_resp.status_code == 200
    assert update_resp.get_json()['amount'] == 450.0

    delete_resp = authenticated_client.delete(f'/api/finance/costs/{cost_id}')
    assert delete_resp.status_code == 200
    assert db.session.get(CostEntry, cost_id) is None


def test_bulk_import_revenues(authenticated_client, test_sheep):
    now = datetime.utcnow()
    entries = [
        {
            'recorded_at': (now - timedelta(days=1)).isoformat(),
            'category': 'milk',
            'amount': 880,
            'sheep_id': test_sheep.id,
        },
        {
            'recorded_at': now.isoformat(),
            'category': 'kids',
            'amount': 1320.75,
            'breed': '波爾羊',
        },
    ]

    resp = authenticated_client.post('/api/finance/revenues/bulk-import', json={'entries': entries})
    assert resp.status_code == 201
    payload = resp.get_json()
    assert len(payload['items']) == 2

    list_resp = authenticated_client.get('/api/finance/revenues', query_string={'category': 'milk'})
    assert list_resp.status_code == 200
    list_data = list_resp.get_json()
    assert list_data['total'] == 1
    assert list_data['items'][0]['category'] == 'milk'
    assert list_data['items'][0]['amount'] == 880.0

    # cleanup
    for item in payload['items']:
        entry = db.session.get(RevenueEntry, item['id'])
        db.session.delete(entry)
    db.session.commit()
