"""Logika autentikasi & otorisasi: hashing password, token akses (mirip JWT
tapi format custom berbasis HMAC), dependency current_user, dan pemeriksaan
hak akses berbasis role (RBAC).
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from typing import Literal

from fastapi import Depends, HTTPException, Request

from app.database import db

SECRET = os.getenv("APP_SECRET", "development-only-change-before-deploy")
TOKEN_TTL = 60 * 60 * 8

Role = Literal["super", "editor", "viewer"]


def password_hash(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    value = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 310_000)
    return f"{salt}${base64.b64encode(value).decode()}"


def password_matches(password: str, stored: str) -> bool:
    salt, _ = stored.split("$", 1)
    return hmac.compare_digest(password_hash(password, salt), stored)


def token_for(user: dict) -> str:
    payload = {"sub": user["id"], "role": user["role"], "exp": int(time.time()) + TOKEN_TTL}
    raw = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).rstrip(b"=")
    sig = hmac.new(SECRET.encode(), raw, hashlib.sha256).digest()
    return raw.decode() + "." + base64.urlsafe_b64encode(sig).rstrip(b"=").decode()


def payload_from(token: str) -> dict:
    try:
        raw, given = token.split(".")
        expected = base64.urlsafe_b64encode(hmac.new(SECRET.encode(), raw.encode(), hashlib.sha256).digest()).rstrip(b"=").decode()
        if not hmac.compare_digest(given, expected):
            raise ValueError
        payload = json.loads(base64.urlsafe_b64decode(raw + "=" * (-len(raw) % 4)))
        if payload["exp"] < time.time():
            raise ValueError
        return payload
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Sesi tidak valid atau berakhir.") from exc


def current_user(request: Request) -> dict:
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Login diperlukan.")
    claims = payload_from(header[7:])
    with db() as con:
        user = con.execute(
            "SELECT id,name,username,email,pending_email,role,building_id,must_complete_profile "
            "FROM users WHERE id=? AND active=1",
            (claims["sub"],),
        ).fetchone()
    if not user:
        raise HTTPException(status_code=401, detail="Akun tidak aktif.")
    return user


def require(*allowed: Role):
    def check(user: dict = Depends(current_user)):
        if user["role"] not in allowed:
            raise HTTPException(status_code=403, detail="Anda tidak memiliki izin untuk aksi ini.")
        return user
    return check


def assert_building_access(user: dict, building_id: int, write: bool = False):
    if user["role"] == "super":
        return
    if user["role"] == "editor" and user["building_id"] == building_id:
        return
    if write:
        raise HTTPException(status_code=403, detail="Gedung ini tidak termasuk akses akun Anda.")
    # viewer & editor lain: boleh baca (read-only)
