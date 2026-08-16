"""Smoke tests for every assembled frontend screen route."""

from fullstack import create_app


def test_all_frontend_screen_routes_serve_html():
    client = create_app(testing=True).test_client()
    sample_id = "11111111-1111-1111-1111-111111111111"
    routes = (
        "/saved-items",
        "/saved-items/add",
        f"/saved-items/{sample_id}",
        "/items/new/cooling-period",
        "/items",
        "/settings/notifications",
        f"/debug/notifications/{sample_id}",
        f"/decision/{sample_id}",
        f"/decision/{sample_id}/skipped",
        "/savings",
        "/savings/history",
        "/savings/skip-confirmation",
    )

    for route in routes:
        response = client.get(route)
        assert response.status_code == 200, route
        assert response.content_type.startswith("text/html"), route
