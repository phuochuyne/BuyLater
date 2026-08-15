"""Deterministic contract checks for Reminder notification."""

import uuid

from backend import create_app
from backend.core.auth import issue_token


def test_feature_routes_are_registered():
    app = create_app(testing=True)
    actual = {
        (rule.rule, method)
        for rule in app.url_map.iter_rules()
        for method in (rule.methods or set())
    }
    expected = (('/api/capability_reminder_notification_fd8968f7/notifications/schedule', 'POST'), ('/api/capability_reminder_notification_fd8968f7/notifications/<notification_id>/cancel', 'PATCH'), ('/api/capability_reminder_notification_fd8968f7/notifications/<notification_id>', 'GET'))
    assert all(route in actual for route in expected)


def test_protected_routes_reject_missing_authentication():
    client = create_app(testing=True).test_client()
    response = client.post('/api/capability_reminder_notification_fd8968f7/notifications/schedule')
    assert response.status_code == 401
    response = client.patch('/api/capability_reminder_notification_fd8968f7/notifications/test-id/cancel')
    assert response.status_code == 401
    response = client.get('/api/capability_reminder_notification_fd8968f7/notifications/test-id')
    assert response.status_code == 401


def test_schedule_rejects_user_id_different_from_token(monkeypatch):
    monkeypatch.setenv('DATABASE_URL', 'mysql+mysqlconnector://unused')
    monkeypatch.setenv('JWT_SECRET', 'test-secret-that-is-long-enough')
    monkeypatch.setenv('JWT_ISSUER', 'test-suite')
    token = issue_token(str(uuid.uuid4()))
    response = create_app(testing=True).test_client().post(
        '/api/capability_reminder_notification_fd8968f7/notifications/schedule',
        headers={'Authorization': f'Bearer {token}'},
        json={'user_id': str(uuid.uuid4())},
    )
    assert response.status_code == 403
    assert response.get_json()['error'] == 'forbidden_user_id'
