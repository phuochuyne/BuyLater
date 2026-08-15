"""Whole-application smoke tests."""

import uuid

from backend import create_app
from backend.core.auth import issue_token
from backend.core.jobs import job_registry


def test_health_endpoint():
    app = create_app(testing=True)
    response = app.test_client().get("/health")
    assert response.status_code == 200
    assert response.get_json()["ok"] is True


def test_expected_function_inventory_is_frozen():
    create_app(testing=True)
    assert job_registry.inventory() == (
        'capability_reminder_notification_fd8968f7.function.process_due_notifications',
        'capability_set_cooling_off_period_ed5144db.function.list_expired_cooling_periods',
    )


def test_auth_routes_validate_credentials_without_database_access():
    client = create_app(testing=True).test_client()
    assert client.post('/api/auth/register', json={}).status_code == 400
    assert client.post('/api/auth/login', json={}).status_code == 400


def test_valid_jwt_populates_user_identity(monkeypatch):
    monkeypatch.setenv('DATABASE_URL', 'mysql+mysqlconnector://unused')
    monkeypatch.setenv('JWT_SECRET', 'test-secret-that-is-long-enough')
    monkeypatch.setenv('JWT_ISSUER', 'test-suite')
    token = issue_token(str(uuid.uuid4()))
    response = create_app(testing=True).test_client().get(
        '/api/capability_save_items_with_price_bd77265a/saved-items/not-a-uuid',
        headers={'Authorization': f'Bearer {token}'},
    )
    assert response.status_code == 404
