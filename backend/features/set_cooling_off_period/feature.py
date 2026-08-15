"""Cooling-off periods attached to saved items."""

import hmac
import uuid
from datetime import datetime, timedelta, timezone

from flask import Blueprint, g, jsonify, request
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from backend.core.auth import require_auth
from backend.core.config import get_settings
from backend.core.db import get_engine


bp = Blueprint("capability_set_cooling_off_period_ed5144db", __name__)
JOB_ID = "capability_set_cooling_off_period_ed5144db.function.list_expired_cooling_periods"


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _serialize(row):
    return {
        "id": row[0],
        "saved_item_id": row[1],
        "period_days": row[2],
        "started_at": row[3].isoformat() + "Z",
        "expires_at": row[4].isoformat() + "Z",
        "created_at": row[5].isoformat() + "Z",
    }


def require_internal_auth(handler):
    def wrapped(*args, **kwargs):
        authorization = request.headers.get("Authorization", "")
        if not authorization.startswith("Bearer "):
            return jsonify({"error": "UNAUTHORIZED"}), 401
        configured = get_settings().internal_job_token
        supplied = authorization[7:].strip()
        if not configured or not hmac.compare_digest(supplied, configured):
            return jsonify({"error": "FORBIDDEN"}), 403
        return handler(*args, **kwargs)

    wrapped.__name__ = handler.__name__
    return wrapped


@bp.post("/api/capability_set_cooling_off_period_ed5144db/cooling-periods")
@require_auth
def create_cooling_period():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "MISSING_REQUIRED_FIELD"}), 400
    saved_item_id = data.get("saved_item_id")
    period_days = data.get("period_days")
    try:
        uuid.UUID(saved_item_id)
    except (AttributeError, TypeError, ValueError):
        return jsonify({"error": "INVALID_SAVED_ITEM_ID"}), 400
    if type(period_days) is not int or period_days not in {1, 3, 7}:
        return jsonify({"error": "INVALID_PERIOD_DAYS"}), 400

    now = _utcnow()
    cooling_period_id = str(uuid.uuid4())
    try:
        with get_engine().begin() as connection:
            item = connection.execute(
                text("""
                    SELECT id FROM f_bd77265a__saved_items
                    WHERE id = :item_id AND user_id = :user_id
                """),
                {"item_id": saved_item_id, "user_id": g.user_id},
            ).fetchone()
            if item is None:
                return jsonify({"error": "SAVED_ITEM_NOT_FOUND"}), 404
            connection.execute(
                text("""
                    INSERT INTO f_ed5144db__cooling_periods
                        (id, saved_item_id, period_days, started_at, expires_at, created_at)
                    VALUES
                        (:id, :saved_item_id, :period_days, :started_at, :expires_at, :created_at)
                """),
                {
                    "id": cooling_period_id,
                    "saved_item_id": saved_item_id,
                    "period_days": period_days,
                    "started_at": now,
                    "expires_at": now + timedelta(days=period_days),
                    "created_at": now,
                },
            )
    except IntegrityError:
        return jsonify({"error": "COOLING_PERIOD_ALREADY_EXISTS"}), 409

    return jsonify({
        "id": cooling_period_id,
        "saved_item_id": saved_item_id,
        "period_days": period_days,
        "started_at": now.isoformat() + "Z",
        "expires_at": (now + timedelta(days=period_days)).isoformat() + "Z",
        "created_at": now.isoformat() + "Z",
    }), 201


@bp.get("/api/capability_set_cooling_off_period_ed5144db/cooling-periods/<saved_item_id>")
@require_auth
def get_cooling_period(saved_item_id):
    try:
        uuid.UUID(saved_item_id)
    except (TypeError, ValueError):
        return jsonify({"error": "COOLING_PERIOD_NOT_FOUND"}), 404
    with get_engine().connect() as connection:
        row = connection.execute(
            text("""
                SELECT c.id, c.saved_item_id, c.period_days,
                       c.started_at, c.expires_at, c.created_at
                FROM f_ed5144db__cooling_periods AS c
                JOIN f_bd77265a__saved_items AS i ON i.id = c.saved_item_id
                WHERE c.saved_item_id = :saved_item_id AND i.user_id = :user_id
            """),
            {"saved_item_id": saved_item_id, "user_id": g.user_id},
        ).fetchone()
    if row is None:
        return jsonify({"error": "COOLING_PERIOD_NOT_FOUND"}), 404
    response = _serialize(row)
    response["time_remaining_seconds"] = max(0, int((row[4] - _utcnow()).total_seconds()))
    response["is_expired"] = response["time_remaining_seconds"] == 0
    return jsonify(response), 200


def expired_cooling_periods(limit=100, offset=0):
    limit = min(max(int(limit), 1), 1000)
    offset = max(int(offset), 0)
    now = _utcnow()
    with get_engine().connect() as connection:
        total = connection.execute(
            text("SELECT COUNT(*) FROM f_ed5144db__cooling_periods WHERE expires_at <= :now"),
            {"now": now},
        ).scalar_one()
        rows = connection.execute(
            text("""
                SELECT id, saved_item_id, period_days, started_at, expires_at, created_at
                FROM f_ed5144db__cooling_periods
                WHERE expires_at <= :now
                ORDER BY expires_at ASC
                LIMIT :limit OFFSET :offset
            """),
            {"now": now, "limit": limit, "offset": offset},
        ).fetchall()
    return {"cooling_periods": [_serialize(row) for row in rows], "total_count": total}


@bp.get("/api/internal/cooling-periods/expired")
@require_internal_auth
def list_expired_cooling_periods():
    return jsonify(expired_cooling_periods(
        request.args.get("limit", 100, type=int),
        request.args.get("offset", 0, type=int),
    )), 200


def register_background_components(registry):
    registry.register(JOB_ID, expired_cooling_periods)
