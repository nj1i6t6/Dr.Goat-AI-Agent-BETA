import json
import os
import sys
from datetime import date, datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.models import (
    ProductBatch,
    BatchSheepAssociation,
    ProcessingStep,
    SheepEvent,
    SheepHistoricalData,
    VerifiableLog,
)


class TestTraceabilityAPI:
    def _create_batch(self, client, sheep=None, batch_number='BATCH-001'):
        payload = {
            'batch_number': batch_number,
            'product_name': '鮮羊乳 946ml',
            'product_type': '乳品',
            'production_date': date.today().isoformat(),
            'is_public': True,
        }
        if sheep is not None:
            payload['sheep_links'] = [
                {
                    'sheep_id': sheep.id,
                    'role': '乳源',
                    'contribution_type': '鮮乳',
                }
            ]
        response = client.post('/api/traceability/batches', json=payload)
        assert response.status_code == 201
        return json.loads(response.data)

    def test_create_batch_with_sheep(self, authenticated_client, test_sheep):
        data = self._create_batch(authenticated_client, sheep=test_sheep, batch_number='BATCH-100')
        assert data['batch_number'] == 'BATCH-100'
        assert data['sheep_links']
        assert data['sheep_links'][0]['sheep_id'] == test_sheep.id

    def test_create_batch_writes_verifiable_log(self, authenticated_client, test_sheep, app):
        data = self._create_batch(authenticated_client, sheep=test_sheep, batch_number='BATCH-LOG')
        with app.app_context():
            entries = VerifiableLog.query.filter_by(entity_type='product_batch', entity_id=data['id']).all()
            assert entries

    def test_add_step_writes_verifiable_log(self, authenticated_client, test_sheep, app):
        batch = self._create_batch(authenticated_client, sheep=test_sheep, batch_number='BATCH-STEP-LOG')
        response = authenticated_client.post(
            f"/api/traceability/batches/{batch['id']}/steps",
            json={'title': '巴氏殺菌', 'sequence_order': 1},
        )
        assert response.status_code == 201
        step = response.get_json()
        with app.app_context():
            entries = VerifiableLog.query.filter_by(entity_type='processing_step', entity_id=step['id']).all()
            assert entries

    def test_list_batches_with_details(self, authenticated_client, test_sheep):
        batch = self._create_batch(authenticated_client, sheep=test_sheep, batch_number='BATCH-LIST')
        response = authenticated_client.get('/api/traceability/batches?include_details=true')
        assert response.status_code == 200
        payload = response.get_json()
        assert any(item['id'] == batch['id'] for item in payload)
        target = next(item for item in payload if item['id'] == batch['id'])
        assert 'sheep_links' in target
        if target.get('steps'):
            assert all('fingerprints' in step for step in target['steps'])

    def test_list_batches_requires_authentication(self, client):
        response = client.get('/api/traceability/batches')
        assert response.status_code == 401

    def test_duplicate_batch_number_rejected(self, authenticated_client):
        payload = {
            'batch_number': 'BATCH-200',
            'product_name': '測試產品',
            'product_type': '乳品',
            'production_date': date.today().isoformat(),
        }
        assert authenticated_client.post('/api/traceability/batches', json=payload).status_code == 201
        response = authenticated_client.post('/api/traceability/batches', json=payload)
        assert response.status_code == 409
        assert 'error' in response.get_json()

    def test_create_batch_requires_json(self, authenticated_client):
        response = authenticated_client.post('/api/traceability/batches', data='plain-text')
        assert response.status_code == 400
        assert response.get_json()['error'] == '請求必須為 JSON'

    def test_create_batch_validation_error(self, authenticated_client):
        response = authenticated_client.post('/api/traceability/batches', json={})
        assert response.status_code == 400
        body = response.get_json()
        assert body['error'] == '資料驗證失敗'
        assert body['details']

    def test_create_batch_invalid_sheep_links(self, authenticated_client):
        payload = {
            'batch_number': 'BATCH-BAD-SHEEP',
            'product_name': '異常批次',
            'product_type': '乳品',
            'production_date': date.today().isoformat(),
            'sheep_links': [
                {
                    'sheep_id': 99999,
                    'role': '乳源',
                    'contribution_type': '鮮乳',
                }
            ],
        }
        response = authenticated_client.post('/api/traceability/batches', json=payload)
        assert response.status_code == 400
        assert '找不到以下羊隻' in response.get_json()['error']

    def test_update_batch_details(self, authenticated_client, test_sheep):
        batch = self._create_batch(authenticated_client, sheep=test_sheep, batch_number='BATCH-101')
        payload = {
            'product_name': '熟成羊乳酪',
            'esg_highlights': '採用牧草飼養，碳排放量低於業界平均。',
            'is_public': False,
        }
        response = authenticated_client.put(f"/api/traceability/batches/{batch['id']}", json=payload)
        assert response.status_code == 200
        updated = json.loads(response.data)
        assert updated['product_name'] == '熟成羊乳酪'
        assert updated['is_public'] is False

    def test_update_batch_requires_json(self, authenticated_client, test_sheep):
        batch = self._create_batch(authenticated_client, sheep=test_sheep, batch_number='BATCH-NO-JSON')
        response = authenticated_client.put(
            f"/api/traceability/batches/{batch['id']}",
            data='plain-text',
        )
        assert response.status_code == 400
        assert response.get_json()['error'] == '請求必須為 JSON'

    def test_update_batch_validation_error(self, authenticated_client, test_sheep):
        batch = self._create_batch(authenticated_client, sheep=test_sheep, batch_number='BATCH-VAL')
        response = authenticated_client.put(
            f"/api/traceability/batches/{batch['id']}",
            json={'sheep_links': [{'role': '缺少羊隻'}]},
        )
        assert response.status_code == 400
        assert 'error' in response.get_json()

    def test_replace_sheep_links(self, authenticated_client, test_sheep, db_session, test_user):
        batch = self._create_batch(authenticated_client, sheep=test_sheep, batch_number='BATCH-102')
        from app.models import Sheep
        new_sheep = Sheep(user_id=test_user.id, EarNum='TEST-S2', Breed='努比亞', Sex='母')
        db_session.add(new_sheep)
        db_session.commit()

        payload = {
            'sheep_links': [
                {
                    'sheep_id': new_sheep.id,
                    'role': '奶源',
                    'notes': '第二批次乳量',
                }
            ]
        }
        response = authenticated_client.post(f"/api/traceability/batches/{batch['id']}/sheep", json=payload)
        assert response.status_code == 200
        result = json.loads(response.data)
        assert len(result['sheep_links']) == 1
        assert result['sheep_links'][0]['sheep_id'] == new_sheep.id

    def test_replace_sheep_links_invalid_id(self, authenticated_client, test_sheep):
        batch = self._create_batch(authenticated_client, sheep=test_sheep, batch_number='BATCH-INVALID-LINK')
        response = authenticated_client.post(
            f"/api/traceability/batches/{batch['id']}/sheep",
            json={'sheep_links': [{'sheep_id': 9999, 'role': '無效'}]},
        )
        assert response.status_code == 400
        assert 'error' in response.get_json()

    def test_replace_sheep_links_requires_json_and_valid_payload(self, authenticated_client, test_sheep):
        batch = self._create_batch(authenticated_client, sheep=test_sheep, batch_number='BATCH-BAD-LINK')
        response = authenticated_client.post(
            f"/api/traceability/batches/{batch['id']}/sheep",
            data='not-json',
        )
        assert response.status_code == 400

        response = authenticated_client.post(
            f"/api/traceability/batches/{batch['id']}/sheep",
            json={},
        )
        assert response.status_code == 400

        response = authenticated_client.post(
            f"/api/traceability/batches/{batch['id']}/sheep",
            json={'sheep_links': [{'sheep_id': 'invalid'}]},
        )
        assert response.status_code == 400
        assert 'error' in response.get_json()

    def test_add_step_requires_json(self, authenticated_client, test_sheep):
        batch = self._create_batch(authenticated_client, sheep=test_sheep, batch_number='BATCH-STEP-JSON')
        response = authenticated_client.post(
            f"/api/traceability/batches/{batch['id']}/steps",
            data='plain-text',
        )
        assert response.status_code == 400
        assert response.get_json()['error'] == '請求必須為 JSON'

    def test_add_step_validation_error(self, authenticated_client, test_sheep):
        batch = self._create_batch(authenticated_client, sheep=test_sheep, batch_number='BATCH-STEP-VAL')
        response = authenticated_client.post(
            f"/api/traceability/batches/{batch['id']}/steps",
            json={'description': '缺少標題'},
        )
        assert response.status_code == 400
        assert response.get_json()['error'] == '資料驗證失敗'

    def test_update_step_requires_json(self, authenticated_client, test_sheep, db_session):
        batch = self._create_batch(authenticated_client, sheep=test_sheep, batch_number='BATCH-STEP-NOJSON')
        step = ProcessingStep(batch_id=batch['id'], title='初始', sequence_order=1)
        db_session.add(step)
        db_session.commit()

        response = authenticated_client.put(
            f"/api/traceability/steps/{step.id}",
            data='plain-text',
        )
        assert response.status_code == 400
        assert response.get_json()['error'] == '請求必須為 JSON'

    def test_update_step_validation_error(self, authenticated_client, test_sheep, db_session):
        batch = self._create_batch(authenticated_client, sheep=test_sheep, batch_number='BATCH-STEP-VALIDATION')
        step = ProcessingStep(batch_id=batch['id'], title='發酵', sequence_order=1)
        db_session.add(step)
        db_session.commit()

        response = authenticated_client.put(
            f"/api/traceability/steps/{step.id}",
            json={'sequence_order': 'not-a-number'},
        )
        assert response.status_code == 400
        assert response.get_json()['error'] == '資料驗證失敗'

    def test_public_trace_endpoint(self, authenticated_client, client, test_sheep, db_session):
        batch = self._create_batch(authenticated_client, sheep=test_sheep, batch_number='BATCH-103')

        step = ProcessingStep(
            batch_id=batch['id'],
            title='巴氏殺菌',
            description='加熱至 72°C',
            sequence_order=1,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )
        db_session.add(step)

        event = SheepEvent(
            sheep_id=test_sheep.id,
            user_id=test_sheep.user_id,
            event_type='疾病治療',
            event_date=date.today().isoformat(),
            description='蹄部清理',
        )
        history = SheepHistoricalData(
            sheep_id=test_sheep.id,
            user_id=test_sheep.user_id,
            record_type='Body_Weight_kg',
            record_date=date.today().isoformat(),
            value=50.0,
        )
        db_session.add_all([event, history])
        db_session.commit()

        response = client.get('/api/traceability/public/BATCH-103')
        assert response.status_code == 200
        story = json.loads(response.data)
        assert story['batch']['batch_number'] == 'BATCH-103'
        assert story['processing_timeline']
        assert story['processing_timeline'][0]['title'] == '巴氏殺菌'
        assert story['sheep_details']
        assert story['sheep_details'][0]['recent_events']
        assert story['sheep_details'][0]['recent_history']

    def test_step_lifecycle(self, authenticated_client, test_sheep):
        batch = self._create_batch(authenticated_client, sheep=test_sheep, batch_number='BATCH-STEP')
        create_payload = {
            'title': '冷卻',
            'description': '降溫至 4°C',
        }
        create_resp = authenticated_client.post(
            f"/api/traceability/batches/{batch['id']}/steps",
            json=create_payload,
        )
        assert create_resp.status_code == 201
        step = create_resp.get_json()

        update_resp = authenticated_client.put(
            f"/api/traceability/steps/{step['id']}",
            json={'description': '降溫與靜置', 'sequence_order': 3},
        )
        assert update_resp.status_code == 200
        assert update_resp.get_json()['sequence_order'] == 3

        delete_resp = authenticated_client.delete(f"/api/traceability/steps/{step['id']}")
        assert delete_resp.status_code == 200
        assert delete_resp.get_json()['success'] is True

    def test_remove_sheep_link(self, authenticated_client, test_sheep):
        batch = self._create_batch(authenticated_client, sheep=test_sheep, batch_number='BATCH-REMOVE')
        response = authenticated_client.delete(
            f"/api/traceability/batches/{batch['id']}/sheep/{test_sheep.id}"
        )
        assert response.status_code == 200
        assert response.get_json()['success'] is True

        response_missing = authenticated_client.delete(
            f"/api/traceability/batches/{batch['id']}/sheep/{test_sheep.id}"
        )
        assert response_missing.status_code == 404

    def test_access_control_on_batches(self, authenticated_client, test_sheep):
        batch = self._create_batch(authenticated_client, sheep=test_sheep, batch_number='BATCH-104')
        authenticated_client.post('/api/auth/logout')
        response = authenticated_client.get(f"/api/traceability/batches/{batch['id']}")
        assert response.status_code == 401

    def test_delete_batch(self, authenticated_client, test_sheep):
        batch = self._create_batch(authenticated_client, sheep=test_sheep, batch_number='BATCH-105')
        response = authenticated_client.delete(f"/api/traceability/batches/{batch['id']}")
        assert response.status_code == 200
        assert response.json['success'] is True
        assert ProductBatch.query.filter_by(id=batch['id']).first() is None
        assert BatchSheepAssociation.query.filter_by(batch_id=batch['id']).count() == 0

    def test_public_trace_not_found(self, client):
        response = client.get('/api/traceability/public/NON-EXISTENT')
        assert response.status_code == 404
