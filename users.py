from __future__ import annotations

import secrets

import pymysql
from fastapi import APIRouter, Depends, HTTPException

from app.auth import password_hash, require
from app.database import db
from app.schemas import UserInput, UserUpdateInput

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("")
def list_users(user=Depends(require("super"))):
    with db() as con:
        rows = con.execute(
            "SELECT u.id,u.name,u.username,u.email,u.pending_email,u.role,u.building_id,u.must_complete_profile,b.name AS building "
            "FROM users u LEFT JOIN buildings b ON b.id=u.building_id ORDER BY u.name"
        ).fetchall()
    return rows


def _generate_temp_password() -> str:
    return "Awal" + secrets.token_hex(3)  # contoh: Awal4f9a21 (10 karakter)


@router.post("", status_code=201)
def create_user(data: UserInput, user=Depends(require("super"))):
    if data.role == "editor" and not data.building_id:
        raise HTTPException(status_code=422, detail="Editor wajib ditugaskan ke satu gedung.")
    temp_password = _generate_temp_password()
    must_complete = 0 if data.email else 1
    with db() as con:
        try:
            cur = con.execute(
                "INSERT INTO users(name,username,email,password_hash,role,building_id,must_complete_profile) VALUES(?,?,?,?,?,?,?)",
                (
                    data.name, data.username.lower(),
                    str(data.email).lower() if data.email else None,
                    password_hash(temp_password), data.role, data.building_id, must_complete,
                ),
            )
        except pymysql.err.IntegrityError as exc:
            raise HTTPException(status_code=409, detail="Username atau email sudah dipakai.") from exc
        return {"id": cur.lastrowid, "message": "Pengguna dibuat", "generated_password": temp_password}


@router.delete("/{user_id}", status_code=204)
def delete_user(user_id: int, user=Depends(require("super"))):
    if user_id == user["id"]:
        raise HTTPException(status_code=400, detail="Tidak bisa menghapus akun yang sedang login.")
    with db() as con:
        con.execute("DELETE FROM users WHERE id=?", (user_id,))


@router.put("/{user_id}")
def update_user(user_id: int, data: UserUpdateInput, user=Depends(require("super"))):
    if data.role == "editor" and not data.building_id:
        raise HTTPException(status_code=422, detail="Editor wajib ditugaskan ke satu gedung.")
    with db() as con:
        if not con.execute("SELECT 1 FROM users WHERE id=?", (user_id,)).fetchone():
            raise HTTPException(status_code=404, detail="Pengguna tidak ditemukan.")
        email_val = str(data.email).lower() if data.email else None
        try:
            if data.password:
                con.execute(
                    "UPDATE users SET name=?,username=?,email=?,role=?,building_id=?,password_hash=? WHERE id=?",
                    (data.name, data.username.lower(), email_val, data.role, data.building_id, password_hash(data.password), user_id),
                )
            else:
                con.execute(
                    "UPDATE users SET name=?,username=?,email=?,role=?,building_id=? WHERE id=?",
                    (data.name, data.username.lower(), email_val, data.role, data.building_id, user_id),
                )
        except pymysql.err.IntegrityError as exc:
            raise HTTPException(status_code=409, detail="Username atau email sudah dipakai pengguna lain.") from exc
        row = con.execute(
            "SELECT u.id,u.name,u.username,u.email,u.pending_email,u.role,u.building_id,u.must_complete_profile,b.name AS building "
            "FROM users u LEFT JOIN buildings b ON b.id=u.building_id WHERE u.id=?",
            (user_id,),
        ).fetchone()
        return row


@router.post("/{user_id}/approve-email")
def approve_email(user_id: int, user=Depends(require("super"))):
    with db() as con:
        row = con.execute("SELECT pending_email FROM users WHERE id=?", (user_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Pengguna tidak ditemukan.")
        if not row["pending_email"]:
            raise HTTPException(status_code=400, detail="Tidak ada email yang menunggu verifikasi.")
        try:
            con.execute("UPDATE users SET email=?, pending_email=NULL WHERE id=?", (row["pending_email"], user_id))
        except pymysql.err.IntegrityError as exc:
            raise HTTPException(status_code=409, detail="Email sudah dipakai pengguna lain.") from exc
        result = con.execute(
            "SELECT u.id,u.name,u.username,u.email,u.pending_email,u.role,u.building_id,b.name AS building "
            "FROM users u LEFT JOIN buildings b ON b.id=u.building_id WHERE u.id=?",
            (user_id,),
        ).fetchone()
    return result


@router.post("/{user_id}/reject-email")
def reject_email(user_id: int, user=Depends(require("super"))):
    with db() as con:
        if not con.execute("SELECT 1 FROM users WHERE id=?", (user_id,)).fetchone():
            raise HTTPException(status_code=404, detail="Pengguna tidak ditemukan.")
        con.execute("UPDATE users SET pending_email=NULL WHERE id=?", (user_id,))
        result = con.execute(
            "SELECT u.id,u.name,u.username,u.email,u.pending_email,u.role,u.building_id,b.name AS building "
            "FROM users u LEFT JOIN buildings b ON b.id=u.building_id WHERE u.id=?",
            (user_id,),
        ).fetchone()
    return result
