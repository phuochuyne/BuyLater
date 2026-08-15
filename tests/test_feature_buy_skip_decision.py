"""Deterministic contract checks for Buy/Skip decision."""

from backend import create_app


def test_feature_routes_are_registered():
    app = create_app(testing=True)
    actual = {
        (rule.rule, method)
        for rule in app.url_map.iter_rules()
        for method in (rule.methods or set())
    }
    expected = (('/api/capability_buy_skip_decision_c984506c/items/<item_id>/decision', 'GET'), ('/api/capability_buy_skip_decision_c984506c/items/<item_id>/decide/buy', 'POST'), ('/api/capability_buy_skip_decision_c984506c/items/<item_id>/decide/skip', 'POST'), ('/api/capability_buy_skip_decision_c984506c/users/me/savings', 'GET'))
    assert all(route in actual for route in expected)


def test_protected_routes_reject_missing_authentication():
    client = create_app(testing=True).test_client()
    response = client.get('/api/capability_buy_skip_decision_c984506c/items/test-id/decision')
    assert response.status_code == 401
    response = client.post('/api/capability_buy_skip_decision_c984506c/items/test-id/decide/buy')
    assert response.status_code == 401
    response = client.post('/api/capability_buy_skip_decision_c984506c/items/test-id/decide/skip')
    assert response.status_code == 401
    response = client.get('/api/capability_buy_skip_decision_c984506c/users/me/savings')
    assert response.status_code == 401
