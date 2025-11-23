from datetime import datetime, timedelta
from decimal import Decimal

from app import db
from app.models import CostEntry, RevenueEntry


def _create_finance_entries(user_id, sheep, days_offset=0):
    base_time = datetime.utcnow() - timedelta(days=days_offset)
    cost = CostEntry(
        user_id=user_id,
        sheep_id=sheep.id,
        recorded_at=base_time,
        category='feed',
        amount=Decimal('150.50'),
        breed=sheep.Breed,
        lactation_number=1,
        production_stage='泌乳期',
    )
    revenue = RevenueEntry(
        user_id=user_id,
        sheep_id=sheep.id,
        recorded_at=base_time,
        category='milk',
        amount=Decimal('320.0'),
        breed=sheep.Breed,
        lactation_number=1,
        production_stage='泌乳期',
    )
    db.session.add(cost)
    db.session.add(revenue)


def test_cohort_analysis_endpoint(app, authenticated_client, multiple_test_sheep):
    with app.app_context():
        user_id = multiple_test_sheep[0].user_id
        for index, sheep in enumerate(multiple_test_sheep):
            sheep.Body_Weight_kg = 42 + index
            sheep.milk_yield_kg_day = 1.5 + index * 0.2
            db.session.add(sheep)
            _create_finance_entries(user_id, sheep, days_offset=index)
        db.session.commit()

    payload = {
        'cohort_by': ['breed'],
        'metrics': ['sheep_count', 'total_cost', 'total_revenue', 'net_profit'],
    }
    resp = authenticated_client.post('/api/bi/cohort-analysis', json=payload)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['metrics'] == payload['metrics']
    assert len(data['items']) >= 1
    first_item = data['items'][0]
    assert 'metrics' in first_item
    assert first_item['metrics']['sheep_count'] >= 1

    with app.app_context():
        db.session.query(CostEntry).delete()
        db.session.query(RevenueEntry).delete()
        db.session.commit()


def test_cost_benefit_endpoint(app, authenticated_client, multiple_test_sheep):
    with app.app_context():
        user_id = multiple_test_sheep[0].user_id
        for sheep in multiple_test_sheep:
            _create_finance_entries(user_id, sheep)
        db.session.commit()

    payload = {
        'group_by': 'month',
        'metrics': ['total_cost', 'total_revenue', 'net_profit', 'avg_cost_per_head'],
    }
    resp = authenticated_client.post('/api/bi/cost-benefit', json=payload)
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'summary' in data
    assert data['summary']['total_revenue'] >= data['summary']['total_cost']
    assert data['items']

    with app.app_context():
        db.session.query(CostEntry).delete()
        db.session.query(RevenueEntry).delete()
        db.session.commit()
