from werkzeug.security import generate_password_hash


def test_create_farm_with_owner_membership(authenticated_client, app):
    response = authenticated_client.post('/api/farm', json={'name': 'Goat Ranch'})
    assert response.status_code == 201
    payload = response.get_json()

    assert payload['farm']['name'] == 'Goat Ranch'
    assert payload['membership']['role'] == 'Owner'
    assert payload['membership']['status'] == 'active'
    assert len(payload['farm']['code']) > 0


def test_join_and_approve_flow(client, app):
    from app import db
    from app.models import User

    with app.app_context():
        existing_owner = User.query.filter_by(username='testuser').first()
        if not existing_owner:
            owner = User(username='testuser', password_hash=generate_password_hash('testpass'))
            db.session.add(owner)
            db.session.commit()

    # Owner creates farm
    client.post('/api/auth/login', json={'username': 'testuser', 'password': 'testpass'})
    create_resp = client.post('/api/farm', json={'name': 'Sheep Valley'})
    farm = create_resp.get_json()['farm']

    # Create worker user
    from app import db
    from app.models import User

    with app.app_context():
        worker = User(username='worker', password_hash=generate_password_hash('pw123'))
        db.session.add(worker)
        db.session.commit()
        worker_id = worker.id

    client.post('/api/auth/logout')
    client.post('/api/auth/login', json={'username': 'worker', 'password': 'pw123'})
    join_resp = client.post('/api/farm/join', json={'farm_code': farm['code'], 'role': 'Worker'})
    assert join_resp.status_code == 201
    membership_id = join_resp.get_json()['membership']['id']
    assert join_resp.get_json()['membership']['status'] == 'pending'

    # Owner approves
    client.post('/api/auth/logout')
    client.post('/api/auth/login', json={'username': 'testuser', 'password': 'testpass'})
    approve_resp = client.post(
        f"/api/farm/{farm['id']}/members/{membership_id}/approve",
        json={'role': 'Manager'},
    )
    assert approve_resp.status_code == 200
    assert approve_resp.get_json()['membership']['status'] == 'active'
    assert approve_resp.get_json()['membership']['role'] == 'Manager'

    # Manager listing works
    client.post('/api/auth/logout')
    client.post('/api/auth/login', json={'username': 'worker', 'password': 'pw123'})
    members_resp = client.get(f"/api/farm/{farm['id']}/members")
    assert members_resp.status_code == 200

