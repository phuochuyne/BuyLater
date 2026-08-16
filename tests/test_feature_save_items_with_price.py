"""Deterministic contract checks for Save items with price."""

from backend import create_app


def test_feature_routes_are_registered():
    app = create_app(testing=True)
    actual = {
        (rule.rule, method)
        for rule in app.url_map.iter_rules()
        for method in (rule.methods or set())
    }
    expected = (('/api/capability_save_items_with_price_bd77265a/saved-items', 'POST'), ('/api/capability_save_items_with_price_bd77265a/saved-items', 'GET'), ('/api/capability_save_items_with_price_bd77265a/saved-items/<id>', 'GET'))
    assert all(route in actual for route in expected)


def test_protected_routes_reject_missing_authentication():
    client = create_app(testing=True).test_client()
    response = client.post('/api/capability_save_items_with_price_bd77265a/saved-items')
    assert response.status_code == 401
    response = client.get('/api/capability_save_items_with_price_bd77265a/saved-items')
    assert response.status_code == 401
    response = client.get('/api/capability_save_items_with_price_bd77265a/saved-items/test-id')
    assert response.status_code == 401
