"""Save and retrieve priced items for an authenticated user."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from urllib.parse import urlparse

from flask import Blueprint, g, jsonify, request
from sqlalchemy import text

from backend.core.auth import require_auth
from backend.core.db import get_engine


bp = Blueprint("capability_save_items_with_price_bd77265a", __name__)
MAX_PRICE = Decimal("99999999.99")


def _valid_url(value):
    if not isinstance(value, str) or len(value) > 2048:
        return False
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _serialize(row):
    return {
        "id": row[0],
        "user_id": row[1],
        "item_name": row[2],
        "price": float(row[3]),
        "product_link": row[4],
        "created_at": row[5].isoformat() + "Z",
    }


@bp.post("/api/capability_save_items_with_price_bd77265a/saved-items")
@require_auth
def create_saved_item():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"code": "VALIDATION_ERROR", "message": "JSON body is required"}), 400

    item_name = data.get("item_name")
    product_link = data.get("product_link")
    if not isinstance(item_name, str) or not item_name.strip() or len(item_name) > 500:
        return jsonify({"code": "VALIDATION_ERROR", "message": "item_name is invalid"}), 400
    if not _valid_url(product_link):
        return jsonify({"code": "INVALID_URL", "message": "product_link must be an HTTP(S) URL"}), 400
    try:
        price = Decimal(str(data.get("price"))).quantize(Decimal("0.01"))
    except (InvalidOperation, TypeError, ValueError):
        return jsonify({"code": "INVALID_PRICE", "message": "price must be a valid amount"}), 400
    if not price.is_finite() or price < 0 or price > MAX_PRICE:
        return jsonify({"code": "INVALID_PRICE", "message": "price is outside the supported range"}), 400

    item_id = str(uuid.uuid4())
    user_id = g.user_id
    created_at = datetime.now(timezone.utc).replace(tzinfo=None)
    with get_engine().begin() as connection:
        connection.execute(
            text("""
                INSERT INTO f_bd77265a__saved_items
                    (id, user_id, item_name, price, product_link, created_at)
                VALUES
                    (:id, :user_id, :item_name, :price, :product_link, :created_at)
            """),
            {
                "id": item_id,
                "user_id": user_id,
                "item_name": item_name.strip(),
                "price": price,
                "product_link": product_link,
                "created_at": created_at,
            },
        )
    return jsonify({
        "id": item_id,
        "user_id": user_id,
        "item_name": item_name.strip(),
        "price": float(price),
        "product_link": product_link,
        "created_at": created_at.isoformat() + "Z",
    }), 201


@bp.get("/api/capability_save_items_with_price_bd77265a/saved-items")
@require_auth
def get_saved_items():
    with get_engine().connect() as connection:
        rows = connection.execute(
            text("""
                SELECT id, user_id, item_name, price, product_link, created_at
                FROM f_bd77265a__saved_items
                WHERE user_id = :user_id
                ORDER BY created_at DESC
            """),
            {"user_id": g.user_id},
        ).fetchall()
    return jsonify({"items": [_serialize(row) for row in rows]}), 200


@bp.get("/api/capability_save_items_with_price_bd77265a/saved-items/<item_id>")
@require_auth
def get_saved_item_by_id(item_id):
    try:
        uuid.UUID(item_id)
    except (TypeError, ValueError):
        return jsonify({"code": "NOT_FOUND", "message": "Saved item not found"}), 404
    with get_engine().connect() as connection:
        row = connection.execute(
            text("""
                SELECT id, user_id, item_name, price, product_link, created_at
                FROM f_bd77265a__saved_items
                WHERE id = :id AND user_id = :user_id
            """),
            {"id": item_id, "user_id": g.user_id},
        ).fetchone()
    if row is None:
        return jsonify({"code": "NOT_FOUND", "message": "Saved item not found"}), 404
    return jsonify(_serialize(row)), 200
