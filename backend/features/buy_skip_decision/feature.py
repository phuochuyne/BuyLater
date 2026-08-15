"""Record a buy/skip decision after an item's cooling-off period."""

import uuid
from datetime import datetime, timezone

from flask import Blueprint, g, jsonify
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from backend.core.auth import require_auth
from backend.core.db import get_engine


bp = Blueprint("capability_buy_skip_decision_c984506c", __name__)


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _item_query(lock=False):
    suffix = " FOR UPDATE" if lock else ""
    return text("""
        SELECT i.id, i.item_name, i.price, i.product_link, c.expires_at
        FROM f_bd77265a__saved_items AS i
        LEFT JOIN f_ed5144db__cooling_periods AS c ON c.saved_item_id = i.id
        WHERE i.id = :item_id AND i.user_id = :user_id
    """ + suffix)


def _valid_item_id(item_id):
    try:
        uuid.UUID(item_id)
        return True
    except (TypeError, ValueError):
        return False


def _cooling_error(item):
    if item is None:
        return jsonify({"code": "ITEM_NOT_FOUND"}), 404
    if item[4] is None:
        return jsonify({"code": "COOLING_PERIOD_NOT_FOUND"}), 409
    if _utcnow() < item[4]:
        return jsonify({"code": "COOLING_OFF_NOT_ENDED"}), 409
    return None


@bp.get("/api/capability_buy_skip_decision_c984506c/items/<item_id>/decision")
@require_auth
def get_decision_screen_data(item_id):
    if not _valid_item_id(item_id):
        return jsonify({"code": "ITEM_NOT_FOUND"}), 404
    with get_engine().connect() as connection:
        item = connection.execute(
            _item_query(), {"item_id": item_id, "user_id": g.user_id}
        ).fetchone()
        error = _cooling_error(item)
        if error:
            return error
        existing = connection.execute(
            text("""
                SELECT decision_type FROM f_c984506c__item_decisions
                WHERE item_id = :item_id AND user_id = :user_id
            """),
            {"item_id": item_id, "user_id": g.user_id},
        ).fetchone()
        total = connection.execute(
            text("SELECT total_saved FROM f_c984506c__user_savings WHERE user_id = :user_id"),
            {"user_id": g.user_id},
        ).scalar()
    return jsonify({
        "item_id": item[0],
        "item_name": item[1],
        "item_price": float(item[2]),
        "item_link": item[3],
        "current_total_saved": float(total or 0),
        "already_decided": existing is not None,
        "decision_type": existing[0] if existing else None,
    }), 200


def _record_decision(item_id, decision_type):
    if not _valid_item_id(item_id):
        return jsonify({"code": "ITEM_NOT_FOUND"}), 404
    now = _utcnow()
    decision_id = str(uuid.uuid4())
    try:
        with get_engine().begin() as connection:
            item = connection.execute(
                _item_query(lock=True),
                {"item_id": item_id, "user_id": g.user_id},
            ).fetchone()
            error = _cooling_error(item)
            if error:
                return error
            connection.execute(
                text("""
                    INSERT INTO f_c984506c__item_decisions
                        (id, item_id, user_id, decision_type, item_price, decided_at)
                    VALUES
                        (:id, :item_id, :user_id, :decision_type, :item_price, :decided_at)
                """),
                {
                    "id": decision_id,
                    "item_id": item_id,
                    "user_id": g.user_id,
                    "decision_type": decision_type,
                    "item_price": item[2],
                    "decided_at": now,
                },
            )
            total = None
            if decision_type == "skip":
                connection.execute(
                    text("""
                        INSERT INTO f_c984506c__user_savings
                            (id, user_id, total_saved, updated_at)
                        VALUES
                            (:id, :user_id, :amount, :updated_at)
                        ON DUPLICATE KEY UPDATE
                            total_saved = total_saved + VALUES(total_saved),
                            updated_at = VALUES(updated_at)
                    """),
                    {
                        "id": str(uuid.uuid4()),
                        "user_id": g.user_id,
                        "amount": item[2],
                        "updated_at": now,
                    },
                )
                total = connection.execute(
                    text("SELECT total_saved FROM f_c984506c__user_savings WHERE user_id = :user_id"),
                    {"user_id": g.user_id},
                ).scalar_one()
    except IntegrityError:
        return jsonify({"code": "ALREADY_DECIDED"}), 409

    response = {
        "decision_id": decision_id,
        "item_id": item_id,
        "decision_type": decision_type,
        "decided_at": now.isoformat() + "Z",
    }
    if decision_type == "buy":
        response["product_link"] = item[3]
    else:
        response["price_saved"] = float(item[2])
        response["new_total_saved"] = float(total)
    return jsonify(response), 200


@bp.post("/api/capability_buy_skip_decision_c984506c/items/<item_id>/decide/buy")
@require_auth
def record_buy_decision(item_id):
    return _record_decision(item_id, "buy")


@bp.post("/api/capability_buy_skip_decision_c984506c/items/<item_id>/decide/skip")
@require_auth
def record_skip_decision(item_id):
    return _record_decision(item_id, "skip")


@bp.get("/api/capability_buy_skip_decision_c984506c/users/me/savings")
@require_auth
def get_user_savings():
    with get_engine().connect() as connection:
        row = connection.execute(
            text("""
                SELECT total_saved, updated_at
                FROM f_c984506c__user_savings
                WHERE user_id = :user_id
            """),
            {"user_id": g.user_id},
        ).fetchone()
    if row is None:
        return jsonify({"user_id": g.user_id, "total_saved": 0.0, "updated_at": None}), 200
    return jsonify({
        "user_id": g.user_id,
        "total_saved": float(row[0]),
        "updated_at": row[1].isoformat() + "Z",
    }), 200
