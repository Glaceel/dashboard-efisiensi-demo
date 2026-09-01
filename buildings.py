from __future__ import annotations

import secrets

import pymysql
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status

from app.auth import assert_building_access, current_user, require
from app.database import ALLOWED_IMAGE_TYPES, MAX_UPLOAD_BYTES, ROOT, UPLOAD_DIR, db
from app.schemas import (
    AcRow,
    BuildingInfoInput,
    BuildingInput,
    EbtRow,
    ElectricityRow,
    EquipmentRow,
    LightingRow,
    NotesInput,
    WaterRow,
)

router = APIRouter(prefix="/api/buildings", tags=["buildings"])

MONTHS = list(range(1, 13))


# ---------------------------------------------------------------------------
# Data dasar gedung
# ---------------------------------------------------------------------------
@router.get("")
def list_buildings(user=Depends(current_user)):
    # Semua peran boleh MELIHAT seluruh gedung (read-only untuk editor/viewer di
    # luar gedung yang ditugaskan). Pembatasan hanya berlaku untuk aksi tulis
    # (lihat assert_building_access), bukan di sini.
    with db() as con:
        rows = con.execute("SELECT * FROM buildings ORDER BY name").fetchall()
    return rows


@router.post("", status_code=status.HTTP_201_CREATED)
def create_building(data: BuildingInput, user=Depends(require("super"))):
    with db() as con:
        cur = con.execute(
            "INSERT INTO buildings(name,district,`function`,area,address) VALUES(?,?,?,?,?)",
            (data.name, data.district, data.function, data.area, data.address),
        )
        return con.execute("SELECT * FROM buildings WHERE id=?", (cur.lastrowid,)).fetchone()


@router.put("/{building_id}")
def update_building(building_id: int, data: BuildingInput, user=Depends(require("super", "editor"))):
    assert_building_access(user, building_id, write=True)
    with db() as con:
        if not con.execute("SELECT 1 FROM buildings WHERE id=?", (building_id,)).fetchone():
            raise HTTPException(status_code=404, detail="Gedung tidak ditemukan.")
        con.execute(
            "UPDATE buildings SET name=?,district=?,`function`=?,area=?,address=? WHERE id=?",
            (data.name, data.district, data.function, data.area, data.address, building_id),
        )
        return con.execute("SELECT * FROM buildings WHERE id=?", (building_id,)).fetchone()


@router.delete("/{building_id}", status_code=204)
def delete_building(building_id: int, user=Depends(require("super"))):
    with db() as con:
        con.execute("DELETE FROM buildings WHERE id=?", (building_id,))


@router.post("/{building_id}/photo")
async def upload_building_photo(building_id: int, file: UploadFile = File(...), user=Depends(require("super", "editor"))):
    assert_building_access(user, building_id, write=True)
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=422, detail="Format file harus JPG, PNG, WEBP, atau GIF.")
    contents = await file.read()
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=422, detail="Ukuran file maksimal 5MB.")

    with db() as con:
        b = con.execute("SELECT photo_path FROM buildings WHERE id=?", (building_id,)).fetchone()
        if not b:
            raise HTTPException(status_code=404, detail="Gedung tidak ditemukan.")
        old_path = b["photo_path"]

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    ext = ALLOWED_IMAGE_TYPES[file.content_type]
    filename = f"building_{building_id}_{secrets.token_hex(6)}.{ext}"
    (UPLOAD_DIR / filename).write_bytes(contents)
    photo_path = f"/uploads/buildings/{filename}"

    with db() as con:
        con.execute("UPDATE buildings SET photo_path=? WHERE id=?", (photo_path, building_id))
        row = con.execute("SELECT * FROM buildings WHERE id=?", (building_id,)).fetchone()

    if old_path:
        old_file = ROOT / old_path.lstrip("/")
        if old_file.exists():
            try:
                old_file.unlink()
            except OSError:
                pass
    return row


@router.delete("/{building_id}/photo", status_code=204)
def delete_building_photo(building_id: int, user=Depends(require("super", "editor"))):
    assert_building_access(user, building_id, write=True)
    with db() as con:
        b = con.execute("SELECT photo_path FROM buildings WHERE id=?", (building_id,)).fetchone()
        if not b:
            raise HTTPException(status_code=404, detail="Gedung tidak ditemukan.")
        old_path = b["photo_path"]
        con.execute("UPDATE buildings SET photo_path=NULL WHERE id=?", (building_id,))
    if old_path:
        old_file = ROOT / old_path.lstrip("/")
        if old_file.exists():
            try:
                old_file.unlink()
            except OSError:
                pass


# ---------------------------------------------------------------------------
# Informasi Umum (satu baris per gedung)
# ---------------------------------------------------------------------------
@router.get("/{building_id}/info")
def get_building_info(building_id: int, user=Depends(current_user)):
    assert_building_access(user, building_id, write=False)
    with db() as con:
        row = con.execute("SELECT * FROM building_info WHERE building_id=?", (building_id,)).fetchone()
    return row or {"building_id": building_id}


@router.put("/{building_id}/info")
def save_building_info(building_id: int, data: BuildingInfoInput, user=Depends(require("super", "editor"))):
    assert_building_access(user, building_id, write=True)
    fields = data.model_dump()
    cols = list(fields.keys())
    with db() as con:
        if not con.execute("SELECT 1 FROM buildings WHERE id=?", (building_id,)).fetchone():
            raise HTTPException(status_code=404, detail="Gedung tidak ditemukan.")
        placeholders = ",".join(["?"] * (len(cols) + 1))
        updates = ",".join(f"{c}=VALUES({c})" for c in cols)
        sql = (
            f"INSERT INTO building_info(building_id,{','.join(cols)}) VALUES({placeholders}) "
            f"ON DUPLICATE KEY UPDATE {updates}"
        )
        con.execute(sql, (building_id, *[fields[c] for c in cols]))
        return con.execute("SELECT * FROM building_info WHERE building_id=?", (building_id,)).fetchone()


# ---------------------------------------------------------------------------
# Helper generik untuk data bulanan (listrik / air / EBT)
# ---------------------------------------------------------------------------
def _monthly_get(table: str, building_id: int, year: int) -> list[dict]:
    with db() as con:
        rows = con.execute(f"SELECT * FROM {table} WHERE building_id=? AND year=?", (building_id, year)).fetchall()
    by_month = {r["month"]: r for r in rows}
    return [by_month.get(m, {"month": m}) for m in MONTHS]


@router.get("/{building_id}/electricity")
def get_electricity(building_id: int, year: int = Query(...), user=Depends(current_user)):
    assert_building_access(user, building_id, write=False)
    return _monthly_get("electricity_consumption", building_id, year)


@router.put("/{building_id}/electricity")
def save_electricity(building_id: int, year: int, rows: list[ElectricityRow], user=Depends(require("super", "editor"))):
    assert_building_access(user, building_id, write=True)
    with db() as con:
        if not con.execute("SELECT 1 FROM buildings WHERE id=?", (building_id,)).fetchone():
            raise HTTPException(status_code=404, detail="Gedung tidak ditemukan.")
        for r in rows:
            total_kwh = (r.wbp_kwh or 0) + (r.lwbp_kwh or 0) if (r.wbp_kwh is not None or r.lwbp_kwh is not None) else None
            total_biaya = None
            biaya_parts = [x for x in (r.biaya_wbp, r.biaya_lwbp, r.biaya_kvarh) if x is not None]
            if biaya_parts:
                total_biaya = sum(biaya_parts)
            con.execute(
                """INSERT INTO electricity_consumption
                   (building_id,year,month,wbp_kwh,lwbp_kwh,total_kwh,kvarh,biaya_wbp,biaya_lwbp,biaya_kvarh,total_biaya)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?)
                   ON DUPLICATE KEY UPDATE
                     wbp_kwh=VALUES(wbp_kwh), lwbp_kwh=VALUES(lwbp_kwh), total_kwh=VALUES(total_kwh),
                     kvarh=VALUES(kvarh), biaya_wbp=VALUES(biaya_wbp), biaya_lwbp=VALUES(biaya_lwbp),
                     biaya_kvarh=VALUES(biaya_kvarh), total_biaya=VALUES(total_biaya)""",
                (building_id, year, r.month, r.wbp_kwh, r.lwbp_kwh, total_kwh, r.kvarh,
                 r.biaya_wbp, r.biaya_lwbp, r.biaya_kvarh, total_biaya),
            )
    return _monthly_get("electricity_consumption", building_id, year)


@router.get("/{building_id}/water")
def get_water(building_id: int, year: int = Query(...), user=Depends(current_user)):
    assert_building_access(user, building_id, write=False)
    return _monthly_get("water_consumption", building_id, year)


@router.put("/{building_id}/water")
def save_water(building_id: int, year: int, rows: list[WaterRow], user=Depends(require("super", "editor"))):
    assert_building_access(user, building_id, write=True)
    with db() as con:
        if not con.execute("SELECT 1 FROM buildings WHERE id=?", (building_id,)).fetchone():
            raise HTTPException(status_code=404, detail="Gedung tidak ditemukan.")
        for r in rows:
            con.execute(
                """INSERT INTO water_consumption(building_id,year,month,total_m3,rain_capacity_m3,greywater_pct)
                   VALUES(?,?,?,?,?,?)
                   ON DUPLICATE KEY UPDATE
                     total_m3=VALUES(total_m3), rain_capacity_m3=VALUES(rain_capacity_m3), greywater_pct=VALUES(greywater_pct)""",
                (building_id, year, r.month, r.total_m3, r.rain_capacity_m3, r.greywater_pct),
            )
    return _monthly_get("water_consumption", building_id, year)


@router.get("/{building_id}/ebt")
def get_ebt(building_id: int, year: int = Query(...), user=Depends(current_user)):
    assert_building_access(user, building_id, write=False)
    return _monthly_get("ebt_production", building_id, year)


@router.put("/{building_id}/ebt")
def save_ebt(building_id: int, year: int, rows: list[EbtRow], user=Depends(require("super", "editor"))):
    assert_building_access(user, building_id, write=True)
    with db() as con:
        if not con.execute("SELECT 1 FROM buildings WHERE id=?", (building_id,)).fetchone():
            raise HTTPException(status_code=404, detail="Gedung tidak ditemukan.")
        for r in rows:
            con.execute(
                """INSERT INTO ebt_production(building_id,year,month,production) VALUES(?,?,?,?)
                   ON DUPLICATE KEY UPDATE production=VALUES(production)""",
                (building_id, year, r.month, r.production),
            )
    return _monthly_get("ebt_production", building_id, year)


# ---------------------------------------------------------------------------
# Daftar baris dinamis (Peralatan Listrik / Sistem Tata Udara / Sistem Pencahayaan)
# ---------------------------------------------------------------------------
def _list_get(table: str, building_id: int) -> list[dict]:
    with db() as con:
        rows = con.execute(f"SELECT * FROM {table} WHERE building_id=? ORDER BY sort_order, id", (building_id,)).fetchall()
    return rows


def _list_replace(table: str, cols: list[str], building_id: int, rows: list) -> list[dict]:
    with db() as con:
        if not con.execute("SELECT 1 FROM buildings WHERE id=?", (building_id,)).fetchone():
            raise HTTPException(status_code=404, detail="Gedung tidak ditemukan.")
        con.execute(f"DELETE FROM {table} WHERE building_id=?", (building_id,))
        for i, r in enumerate(rows):
            data = r.model_dump()
            placeholders = ",".join(["?"] * (len(cols) + 2))
            con.execute(
                f"INSERT INTO {table}(building_id,sort_order,{','.join(cols)}) VALUES({placeholders})",
                (building_id, i, *[data[c] for c in cols]),
            )
    return _list_get(table, building_id)


@router.get("/{building_id}/equipment")
def get_equipment(building_id: int, user=Depends(current_user)):
    assert_building_access(user, building_id, write=False)
    return _list_get("building_equipment", building_id)


@router.put("/{building_id}/equipment")
def save_equipment(building_id: int, rows: list[EquipmentRow], user=Depends(require("super", "editor"))):
    assert_building_access(user, building_id, write=True)
    return _list_replace("building_equipment", ["name", "daya_kw", "jumlah"], building_id, rows)


@router.get("/{building_id}/ac-systems")
def get_ac_systems(building_id: int, user=Depends(current_user)):
    assert_building_access(user, building_id, write=False)
    return _list_get("building_ac_systems", building_id)


@router.put("/{building_id}/ac-systems")
def save_ac_systems(building_id: int, rows: list[AcRow], user=Depends(require("super", "editor"))):
    assert_building_access(user, building_id, write=True)
    return _list_replace(
        "building_ac_systems",
        ["floor", "room", "ac_type", "cooling_capacity", "refrigerant_type", "room_capacity", "temp_setting", "temp_measured", "notes"],
        building_id, rows,
    )


@router.get("/{building_id}/lighting")
def get_lighting(building_id: int, user=Depends(current_user)):
    assert_building_access(user, building_id, write=False)
    return _list_get("building_lighting", building_id)


@router.put("/{building_id}/lighting")
def save_lighting(building_id: int, rows: list[LightingRow], user=Depends(require("super", "editor"))):
    assert_building_access(user, building_id, write=True)
    return _list_replace(
        "building_lighting",
        ["floor", "room", "room_area", "lamp_type_power", "lamp_count", "hours_per_day", "sensor_used", "lux_measurement", "notes"],
        building_id, rows,
    )


@router.get("/{building_id}/notes")
def get_notes(building_id: int, user=Depends(current_user)):
    assert_building_access(user, building_id, write=False)
    with db() as con:
        row = con.execute("SELECT * FROM building_notes WHERE building_id=?", (building_id,)).fetchone()
    return row or {"building_id": building_id, "note": ""}


@router.put("/{building_id}/notes")
def save_notes(building_id: int, data: NotesInput, user=Depends(require("super", "editor"))):
    assert_building_access(user, building_id, write=True)
    with db() as con:
        if not con.execute("SELECT 1 FROM buildings WHERE id=?", (building_id,)).fetchone():
            raise HTTPException(status_code=404, detail="Gedung tidak ditemukan.")
        con.execute(
            "INSERT INTO building_notes(building_id,note) VALUES(?,?) ON DUPLICATE KEY UPDATE note=VALUES(note)",
            (building_id, data.note),
        )
        return con.execute("SELECT * FROM building_notes WHERE building_id=?", (building_id,)).fetchone()
