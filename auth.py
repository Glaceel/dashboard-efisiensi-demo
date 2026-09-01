from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.auth import current_user, password_hash, password_matches, token_for
from app.database import DB_HOST, DB_NAME, DB_PORT, db
from app.schemas import CompleteProfileInput, Login

router = APIRouter(prefix="/api", tags=["auth"])


@router.get("/health")
def health():
    try:
        with db() as con:
            con.execute("SELECT 1")
        return {"database": "connected", "name": DB_NAME, "host": f"{DB_HOST}:{DB_PORT}"}
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/auth/login")
def login(data: Login):
    ident = data.identifier.strip().lower()
    with db() as con:
        user = con.execute(
            "SELECT * FROM users WHERE (email=? OR username=?) AND active=1", (ident, ident)
        ).fetchone()
    if not user or not password_matches(data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Email/Username atau kata sandi tidak sesuai.")
    user.pop("password_hash", None)
    return {"access_token": token_for(user), "user": user}


@router.get("/auth/me")
def me(user=Depends(current_user)):
    return user


@router.post("/auth/complete-profile")
def complete_profile(data: CompleteProfileInput, user=Depends(current_user)):
    """Dipanggil pengguna sendiri (dibuat tanpa email oleh Super Editor) untuk
    mengajukan email aktif + kata sandi baru. Kata sandi langsung berlaku;
    email baru berlaku SETELAH disetujui Super Editor (lihat users.approve_email)."""
    email_val = str(data.email).lower()
    with db() as con:
        conflict = con.execute(
            "SELECT id FROM users WHERE (email=? OR pending_email=?) AND id<>?",
            (email_val, email_val, user["id"]),
        ).fetchone()
        if conflict:
            raise HTTPException(status_code=409, detail="Email sudah dipakai atau sedang diajukan pengguna lain.")
        if data.password:
            con.execute(
                "UPDATE users SET password_hash=?, pending_email=?, must_complete_profile=0 WHERE id=?",
                (password_hash(data.password), email_val, user["id"]),
            )
        else:
            con.execute(
                "UPDATE users SET pending_email=?, must_complete_profile=0 WHERE id=?",
                (email_val, user["id"]),
            )
        row = con.execute(
            "SELECT id,name,username,email,pending_email,role,building_id,must_complete_profile FROM users WHERE id=?",
            (user["id"],),
        ).fetchone()
    return row
