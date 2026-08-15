"""Track estimated savings for skipped items."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

from flask import Blueprint, g, jsonify, request
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from backend.core.auth import require_auth
from backend.core.db import get_engine


bp = Blueprint("capability_track_estimated_money_saved_66579af4", __name__)
MAX_AMOUNT = Decimal("99999999.99")


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


@bp.post("/api/capability_track_estimated_money_saved_66579af4/savings/record")
@require_auth
def record_savings():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "INVALID_REQUEST"}), 400
    item_id = data.get("item_id")
    try:
        uuid.UUID(item_id)
        amount = Decimal(str(data.get("saved_amount"))).quantize(Decimal("0.01"))
    except (AttributeError, InvalidOperation, TypeError, ValueError):
        return jsonify({"error": "INVALID_REQUEST"}), 400
    if not amount.is_finite() or amount < 0 or amount > MAX_AMOUNT:
        return jsonify({"error": "INVALID_AMOUNT"}), 400

    record_id = str(uuid.uuid4())
    now = _utcnow()
    try:
        with get_engine().begin() as connection:
            item = connection.execute(
                text("""
                    SELECT id FROM f_bd77265a__saved_items
                    WHERE id = :item_id AND user_id = :user_id
                """),
                {"item_id": item_id, "user_id": g.user_id},
            ).fetchone()
            if item is None:
                return jsonify({"error": "ITEM_NOT_FOUND"}), 404
            connection.execute(
                text("""
                    INSERT INTO f_66579af4__user_savings_totals
                        (user_id, total_saved, updated_at)
                    VALUES
                        (:user_id, :amount, :updated_at)
                    ON DUPLICATE KEY UPDATE
                        total_saved = total_saved + VALUES(total_saved),
                        updated_at = VALUES(updated_at)
                """),
                {"user_id": g.user_id, "amount": amount, "updated_at": now},
            )
            connection.execute(
                text("""
                    INSERT INTO f_66579af4__savings_records
                        (id, user_id, item_id, saved_amount, skipped_at, created_at)
                    VALUES
                        (:id, :user_id, :item_id, :amount, :skipped_at, :created_at)
                """),
                {
                    "id": record_id,
                    "user_id": g.user_id,
                    "item_id": item_id,
                    "amount": amount,
                    "skipped_at": now,
                    "created_at": now,
                },
            )
            total = connection.execute(
                text("""
                    SELECT total_saved FROM f_66579af4__user_savings_totals
                    WHERE user_id = :user_id
                """),
                {"user_id": g.user_id},
            ).scalar_one()
    except IntegrityError:
        return jsonify({"error": "SAVINGS_ALREADY_RECORDED"}), 409
    return jsonify({"savings_record_id": record_id, "new_total_saved": float(total)}), 201


@bp.get("/api/capability_track_estimated_money_saved_66579af4/savings/total")
@require_auth
def get_total_savings():
    with get_engine().connect() as connection:
        row = connection.execute(
            text("""
                SELECT total_saved, updated_at
                FROM f_66579af4__user_savings_totals
                WHERE user_id = :user_id
            """),
            {"user_id": g.user_id},
        ).fetchone()
    if row is None:
        return jsonify({"total_saved": 0.0, "updated_at": None}), 200
    return jsonify({
        "total_saved": float(row[0]),
        "updated_at": row[1].isoformat() + "Z",
    }), 200


@bp.get("/api/capability_track_estimated_money_saved_66579af4/savings/history")
@require_auth
def get_savings_history():
    limit = request.args.get("limit", 50, type=int)
    offset = request.args.get("offset", 0, type=int)
    limit = min(max(limit or 50, 1), 100)
    offset = max(offset or 0, 0)
    with get_engine().connect() as connection:
        total = connection.execute(
            text("SELECT COUNT(*) FROM f_66579af4__savings_records WHERE user_id = :user_id"),
            {"user_id": g.user_id},
        ).scalar_one()
        rows = connection.execute(
            text("""
                SELECT id, item_id, saved_amount, skipped_at, created_at
                FROM f_66579af4__savings_records
                WHERE user_id = :user_id
                ORDER BY skipped_at DESC, created_at DESC
                LIMIT :limit OFFSET :offset
            """),
            {"user_id": g.user_id, "limit": limit, "offset": offset},
        ).fetchall()
    return jsonify({
        "records": [{
            "id": row[0],
            "item_id": row[1],
            "saved_amount": float(row[2]),
            "skipped_at": row[3].isoformat() + "Z",
            "created_at": row[4].isoformat() + "Z",
        } for row in rows],
        "total_count": total,
    }), 200
