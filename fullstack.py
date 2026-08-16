"""Server-owned entry point for the assembled Zorentia application."""

import re
from pathlib import Path

from flask import abort, send_file
from backend import create_app as create_backend_app

PROJECT_ROOT = Path(__file__).resolve().parent
SCREEN_ROUTES = {'/saved-items': 'frontend/features/save_items_with_price/saved_items_list.html', '/saved-items/add': 'frontend/features/save_items_with_price/add_item.html', '/saved-items/{id}': 'frontend/features/save_items_with_price/item_detail.html', '/items/new/cooling-period': 'frontend/features/set_cooling_off_period/select_cooling_off_period.html', '/items': 'frontend/features/countdown_timer/saved_items_list.html', '/settings/notifications': 'frontend/features/reminder_notification/notification_settings.html', '/debug/notifications/{notification_id}': 'frontend/features/reminder_notification/notification_debug.html', '/decision/:item_id': 'frontend/features/buy_skip_decision/decision_screen.html', '/decision/:item_id/skipped': 'frontend/features/buy_skip_decision/skip_confirmation_screen.html', '/savings': 'frontend/features/track_estimated_money_saved/savings_dashboard.html', '/savings/history': 'frontend/features/track_estimated_money_saved/savings_history.html', '/savings/skip-confirmation': 'frontend/features/track_estimated_money_saved/skip_confirmation.html'}


def _flask_route(route):
    route = re.sub(
        r"\{([A-Za-z_][A-Za-z0-9_]*)\}",
        lambda match: "<" + match.group(1) + ">",
        route,
    )
    return re.sub(
        r"(?<=/):([A-Za-z_][A-Za-z0-9_]*)",
        lambda match: "<" + match.group(1) + ">",
        route,
    )


def _project_file(relative_path):
    target = (PROJECT_ROOT / relative_path).resolve()
    if target != PROJECT_ROOT and PROJECT_ROOT not in target.parents:
        raise RuntimeError("frontend_route_path_invalid")
    return target


def create_app(testing=False):
    app = create_backend_app(testing=testing)

    @app.get("/static/css/app.css")
    def frontend_css():
        return send_file(
            _project_file("frontend/static/css/app.css"),
            mimetype="text/css",
        )

    @app.get("/__frontend_assets/<path:relative_path>")
    def frontend_asset(relative_path):
        normalized = str(relative_path or "").replace("\\", "/")
        if not normalized.startswith("frontend/features/") or not normalized.endswith(".js"):
            abort(404)
        return send_file(
            _project_file(normalized),
            mimetype="text/javascript",
        )

    for index, (route, relative_path) in enumerate(SCREEN_ROUTES.items()):
        target = _project_file(relative_path)

        def serve_screen(_target=target, **_route_parameters):
            return send_file(_target, mimetype="text/html")

        app.add_url_rule(
            _flask_route(route),
            endpoint="frontend_screen_" + str(index),
            view_func=serve_screen,
            methods=["GET"],
        )
    return app
