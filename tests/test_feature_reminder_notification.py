"""Deterministic contract checks for Reminder notification."""

from backend import create_app


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
