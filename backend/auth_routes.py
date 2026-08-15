"""User registration and login endpoints."""

import uuid

from flask import Blueprint, jsonify, request
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from backend.core.auth import hash_password, issue_token, verify_password
from backend.core.db import get_engine


bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def _credentials():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None, None
    email = str(data.get("email") or "").strip().lower()
    password = data.get("password")
    if not email or "@" not in email or not isinstance(password, str) or len(password) < 8:
        return None, None
    return email, password


@bp.post("/register")
def register():
    email, password = _credentials()
    if not email:
        return jsonify({"error": "invalid_credentials"}), 400

    user_id = str(uuid.uuid4())
    token = issue_token(user_id)
    try:
        with get_engine().begin() as connection:
            connection.execute(
                text("""
                    INSERT INTO users (id, email, password_hash)
                    VALUES (:id, :email, :password_hash)
                """),
                {
                    "id": user_id,
                    "email": email,
                    "password_hash": hash_password(password),
                },
            )
    except IntegrityError:
        return jsonify({"error": "email_already_registered"}), 409

    return jsonify({"user_id": user_id, "token": token}), 201


@bp.post("/login")
def login():
    email, password = _credentials()
    if not email:
        return jsonify({"error": "invalid_credentials"}), 400

    with get_engine().connect() as connection:
        row = connection.execute(
            text("SELECT id, password_hash FROM users WHERE email = :email"),
            {"email": email},
        ).fetchone()
    if row is None or not verify_password(password, row[1]):
        return jsonify({"error": "invalid_credentials"}), 401
    return jsonify({"user_id": row[0], "token": issue_token(row[0])}), 200
