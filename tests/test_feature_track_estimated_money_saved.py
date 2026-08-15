"""Deterministic contract checks for Track estimated money saved."""

from backend import create_app


def test_feature_routes_are_registered():
    app = create_app(testing=True)
    actual = {
        (rule.rule, method)
        for rule in app.url_map.iter_rules()
        for method in (rule.methods or set())
    }
    expected = (('/api/capability_track_estimated_money_saved_66579af4/savings/record', 'POST'), ('/api/capability_track_estimated_money_saved_66579af4/savings/total', 'GET'), ('/api/capability_track_estimated_money_saved_66579af4/savings/history', 'GET'))
    assert all(route in actual for route in expected)


def test_protected_routes_reject_missing_authentication():
    client = create_app(testing=True).test_client()
    response = client.post('/api/capability_track_estimated_money_saved_66579af4/savings/record')
    assert response.status_code == 401
    response = client.get('/api/capability_track_estimated_money_saved_66579af4/savings/total')
    assert response.status_code == 401
    response = client.get('/api/capability_track_estimated_money_saved_66579af4/savings/history')
    assert response.status_code == 401
