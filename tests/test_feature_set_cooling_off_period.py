"""Deterministic contract checks for Set cooling-off period."""

from backend import create_app


def test_feature_routes_are_registered():
    app = create_app(testing=True)
    actual = {
        (rule.rule, method)
        for rule in app.url_map.iter_rules()
        for method in (rule.methods or set())
    }
    expected = (('/api/capability_set_cooling_off_period_ed5144db/cooling-periods', 'POST'), ('/api/capability_set_cooling_off_period_ed5144db/cooling-periods/<saved_item_id>', 'GET'))
    assert all(route in actual for route in expected)


def test_protected_routes_reject_missing_authentication():
    client = create_app(testing=True).test_client()
    response = client.post('/api/capability_set_cooling_off_period_ed5144db/cooling-periods')
    assert response.status_code == 401
    response = client.get('/api/capability_set_cooling_off_period_ed5144db/cooling-periods/test-id')
    assert response.status_code == 401
