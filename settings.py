from __future__ import annotations

import secrets

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.auth import require
from app.database import ALLOWED_IMAGE_TYPES, BRANDING_DIR, MAX_UPLOAD_BYTES, ROOT, db

router = APIRouter(prefix="/api/settings", tags=["settings"])


def _get_setting(con, key: str) -> str | None:
    row = con.execute("SELECT value FROM app_settings WHERE `key`=?", (key,)).fetchone()
    return row["value"] if row else None


def _set_setting(con, key: str, value: str | None):
    con.execute(
        "INSERT INTO app_settings(`key`,value) VALUES(?,?) ON DUPLICATE KEY UPDATE value=VALUES(value)",
        (key, value),
    )


# GET logo TIDAK butuh login karena halaman login sendiri perlu menampilkannya.
@router.get("/logo")
def get_logo():
    with db() as con:
        path = _get_setting(con, "logo_path")
    return {"logo_path": path}


@router.post("/logo")
async def upload_logo(file: UploadFile = File(...), user=Depends(require("super"))):
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=422, detail="Format file harus JPG, PNG, WEBP, atau GIF.")
    contents = await file.read()
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=422, detail="Ukuran file maksimal 5MB.")

    with db() as con:
        old_path = _get_setting(con, "logo_path")

    BRANDING_DIR.mkdir(parents=True, exist_ok=True)
    ext = ALLOWED_IMAGE_TYPES[file.content_type]
    filename = f"logo_{secrets.token_hex(6)}.{ext}"
    (BRANDING_DIR / filename).write_bytes(contents)
    logo_path = f"/uploads/branding/{filename}"

    with db() as con:
        _set_setting(con, "logo_path", logo_path)

    if old_path:
        old_file = ROOT / old_path.lstrip("/")
        if old_file.exists():
            try:
                old_file.unlink()
            except OSError:
                pass
    return {"logo_path": logo_path}


@router.delete("/logo", status_code=204)
def delete_logo(user=Depends(require("super"))):
    with db() as con:
        old_path = _get_setting(con, "logo_path")
        _set_setting(con, "logo_path", None)
    if old_path:
        old_file = ROOT / old_path.lstrip("/")
        if old_file.exists():
            try:
                old_file.unlink()
            except OSError:
                pass
