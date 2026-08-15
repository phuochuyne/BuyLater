"""Schedule, inspect, cancel, and deliver reminder notifications."""

import uuid
from datetime import datetime, timezone

from flask import Blueprint, g, jsonify, request
from sqlalchemy import text

from backend.core.auth import require_auth
from backend.core.db import get_engine
from backend.core.integrations import integration_registry


bp = Blueprint("capability_reminder_notification_fd8968f7", __name__)
JOB_ID = "capability_reminder_notification_fd8968f7.function.process_due_notifications"


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _parse_timestamp(value):
    if not isinstance(value, str):
        raise ValueError("timestamp_required")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).replace(tzinfo=None)


@bp.post("/api/capability_reminder_notification_fd8968f7/notifications/schedule")
@require_auth
def schedule_notification():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "invalid_request"}), 400
    if data.get("user_id") not in {None, g.user_id}:
        return jsonify({"error": "forbidden_user_id"}), 403

    item_id = data.get("item_id")
    try:
        uuid.UUID(item_id)
        scheduled_for = _parse_timestamp(data.get("scheduled_for"))
    except (AttributeError, TypeError, ValueError):
        return jsonify({"error": "invalid_request"}), 400
    fields = {
        "notification_title": 100,
        "notification_body": 200,
        "deep_link_target": 500,
    }
    for field, maximum in fields.items():
        value = data.get(field)
        if not isinstance(value, str) or not value.strip() or len(value) > maximum:
            return jsonify({"error": "invalid_request", "field": field}), 400
    if scheduled_for <= _utcnow():
        return jsonify({"error": "scheduled_for_must_be_in_the_future"}), 400

    notification_id = str(uuid.uuid4())
    created_at = _utcnow()
    with get_engine().begin() as connection:
        item = connection.execute(
            text("""
                SELECT id FROM f_bd77265a__saved_items
                WHERE id = :item_id AND user_id = :user_id
            """),
            {"item_id": item_id, "user_id": g.user_id},
        ).fetchone()
        if item is None:
            return jsonify({"error": "item_not_found"}), 404
        connection.execute(
            text("""
                INSERT INTO f_fd8968f7__scheduled_notifications
                    (id, item_id, user_id, scheduled_for, status,
                     notification_title, notification_body, deep_link_target, created_at)
                VALUES
                    (:id, :item_id, :user_id, :scheduled_for, 'pending',
                     :notification_title, :notification_body, :deep_link_target, :created_at)
            """),
            {
                "id": notification_id,
                "item_id": item_id,
                "user_id": g.user_id,
                "scheduled_for": scheduled_for,
                "notification_title": data["notification_title"].strip(),
                "notification_body": data["notification_body"].strip(),
                "deep_link_target": data["deep_link_target"].strip(),
                "created_at": created_at,
            },
        )
    return jsonify({
        "id": notification_id,
        "status": "pending",
        "scheduled_for": scheduled_for.isoformat() + "Z",
    }), 201


def send_push_notification(user_id, title, body, deep_link):
    client = integration_registry.require("push_notifications")
    return client.send(
        user_id=user_id,
        title=title,
        body=body,
        deep_link=deep_link,
    )


def process_due_notifications(limit=100):
    processed = sent = failed = 0
    with get_engine().begin() as connection:
        rows = connection.execute(
            text("""
                SELECT id, user_id, notification_title, notification_body, deep_link_target
                FROM f_fd8968f7__scheduled_notifications
                WHERE status = 'pending' AND scheduled_for <= :now
                ORDER BY scheduled_for ASC
                LIMIT :limit
                FOR UPDATE SKIP LOCKED
            """),
            {"now": _utcnow(), "limit": min(max(int(limit), 1), 1000)},
        ).fetchall()
        for row in rows:
            processed += 1
            try:
                send_push_notification(row[1], row[2], row[3], row[4])
                connection.execute(
                    text("""
                        UPDATE f_fd8968f7__scheduled_notifications
                        SET status = 'sent', sent_at = :sent_at
                        WHERE id = :id AND status = 'pending'
                    """),
                    {"id": row[0], "sent_at": _utcnow()},
                )
                sent += 1
            except Exception:
                connection.execute(
                    text("""
                        UPDATE f_fd8968f7__scheduled_notifications
                        SET status = 'failed'
                        WHERE id = :id AND status = 'pending'
                    """),
                    {"id": row[0]},
                )
                failed += 1
    return {"processed": processed, "sent": sent, "failed": failed}


@bp.patch("/api/capability_reminder_notification_fd8968f7/notifications/<notification_id>/cancel")
@require_auth
def cancel_notification(notification_id):
    try:
        uuid.UUID(notification_id)
    except (TypeError, ValueError):
        return jsonify({"error": "not_found"}), 404
    with get_engine().begin() as connection:
        row = connection.execute(
            text("""
                SELECT status FROM f_fd8968f7__scheduled_notifications
                WHERE id = :id AND user_id = :user_id
                FOR UPDATE
            """),
            {"id": notification_id, "user_id": g.user_id},
        ).fetchone()
        if row is None:
            return jsonify({"error": "not_found"}), 404
        if row[0] == "sent":
            return jsonify({"error": "already_sent"}), 409
        if row[0] != "cancelled":
            connection.execute(
                text("""
                    UPDATE f_fd8968f7__scheduled_notifications
                    SET status = 'cancelled'
                    WHERE id = :id AND user_id = :user_id
                """),
                {"id": notification_id, "user_id": g.user_id},
            )
    return jsonify({"id": notification_id, "status": "cancelled"}), 200


@bp.get("/api/capability_reminder_notification_fd8968f7/notifications/<notification_id>")
@require_auth
def get_notification_status(notification_id):
    try:
        uuid.UUID(notification_id)
    except (TypeError, ValueError):
        return jsonify({"error": "not_found"}), 404
    with get_engine().connect() as connection:
        row = connection.execute(
            text("""
                SELECT id, user_id, item_id, scheduled_for, status, sent_at, created_at
                FROM f_fd8968f7__scheduled_notifications
                WHERE id = :id AND user_id = :user_id
            """),
            {"id": notification_id, "user_id": g.user_id},
        ).fetchone()
    if row is None:
        return jsonify({"error": "not_found"}), 404
    return jsonify({
        "id": row[0],
        "user_id": row[1],
        "item_id": row[2],
        "scheduled_for": row[3].isoformat() + "Z",
        "status": row[4],
        "sent_at": row[5].isoformat() + "Z" if row[5] else None,
        "created_at": row[6].isoformat() + "Z",
    }), 200


def register_background_components(registry):
    registry.register(JOB_ID, process_due_notifications)
