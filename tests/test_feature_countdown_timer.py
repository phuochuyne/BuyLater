"""Deterministic contract checks for Countdown timer."""

from backend import create_app


def test_feature_routes_are_registered():
    app = create_app(testing=True)
    actual = {
        (rule.rule, method)
        for rule in app.url_map.iter_rules()
        for method in (rule.methods or set())
    }
    expected = (
        ('/api/countdown-timer/calculate', 'POST'),
        ('/api/countdown-timer/status', 'GET'),
        ('/api/countdown-timer/format', 'POST'),
        ('/api/countdown-timer/health', 'GET'),
    )
    assert all(route in actual for route in expected)

def test_calculate_accepts_utc_timestamp():
    client = create_app(testing=True).test_client()
    response = client.post('/api/countdown-timer/calculate', json={
        'start_time': '2024-01-01T10:00:00Z',
        'duration_seconds': 3600,
    })
    assert response.status_code == 200
    assert response.get_json()['is_expired'] is True
