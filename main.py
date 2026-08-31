"""API Sistem Monitoring Efisiensi Energi Bangunan Gedung.

Backend ini terhubung ke MySQL (mis. lewat DBngin di Mac). Konfigurasi koneksi
diambil dari file .env (lihat .env.example). Pastikan database-nya sudah
DIBUAT lebih dulu di MySQL (mis. lewat TablePlus/Sequel Ace atau `mysql` CLI):

    CREATE DATABASE db_energi CHARACTER SET utf8mb4;

Tabel-tabel di dalamnya dibuat otomatis oleh aplikasi saat pertama kali start.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import ssl as ssl_module
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Literal

import pymysql
import pymysql.cursors
from fastapi import Depends, FastAPI, File, HTTPException, Query, Request, UploadFile, status
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr, Field
from dotenv import load_dotenv

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "db_energi")

SECRET = os.getenv("APP_SECRET", "development-only-change-before-deploy")
TOKEN_TTL = 60 * 60 * 8
Role = Literal["super", "editor", "viewer"]
MONTHS = list(range(1, 13))

# Di Vercel, filesystem project bersifat read-only kecuali /tmp — jadi file yang
# diupload user (foto gedung, logo) diarahkan ke /tmp supaya tidak error saat ditulis.
# CATATAN: /tmp bersifat sementara (bisa hilang saat function di-restart/cold start),
# jadi ini cukup untuk demo tapi bukan solusi penyimpanan permanen.
_UPLOAD_BASE = Path("/tmp/uploads") if os.getenv("VERCEL") else (ROOT / "uploads")
UPLOAD_DIR = _UPLOAD_BASE / "buildings"
BRANDING_DIR = _UPLOAD_BASE / "branding"
ALLOWED_IMAGE_TYPES = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp", "image/gif": "gif"}
MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5MB

app = FastAPI(title="EnergiGedung API", version="2.0.0")


@app.exception_handler(RuntimeError)
async def db_error_handler(request: Request, exc: RuntimeError):
    return JSONResponse(status_code=503, content={"detail": str(exc)})


# ---------------------------------------------------------------------------
# Lapisan koneksi database (MySQL via PyMySQL)
# ---------------------------------------------------------------------------
class _ConnWrapper:
    """Bikin pemakaian mirip sqlite3 (con.execute(...).fetchone()) di atas PyMySQL,
    supaya kode di bawah tetap ringkas. Placeholder `?` otomatis dikonversi ke `%s`.
    """

    def __init__(self, raw):
        self._raw = raw

    def execute(self, sql: str, params=()):
        cur = self._raw.cursor()
        cur.execute(sql.replace("?", "%s"), params)
        return cur

    def executescript(self, sql: str):
        cur = self._raw.cursor()
        for stmt in filter(None, (s.strip() for s in sql.split(";"))):
            cur.execute(stmt)

    def commit(self):
        self._raw.commit()

    def rollback(self):
        self._raw.rollback()

    def close(self):
        self._raw.close()


def _ssl_args():
    """Aiven (dan kebanyakan MySQL cloud) mewajibkan koneksi SSL.
    Aktifkan dengan DB_SSL=true. Kalau kamu punya CA certificate dari Aiven,
    tempel isi file .pem-nya ke env var DB_SSL_CA supaya verifikasinya ketat;
    kalau tidak diisi, koneksi tetap terenkripsi tapi tanpa verifikasi sertifikat
    (cukup untuk demo)."""
    if os.getenv("DB_SSL", "false").lower() not in {"1", "true", "yes"}:
        return None
    ca_content = os.getenv("DB_SSL_CA")
    if ca_content:
        ca_path = Path("/tmp/aiven-ca.pem")
        if not ca_path.exists():
            ca_path.write_text(ca_content)
        return ssl_module.create_default_context(cafile=str(ca_path))
    ctx = ssl_module.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl_module.CERT_NONE
    return ctx


@contextmanager
def db():
    try:
        raw = pymysql.connect(
            host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD,
            database=DB_NAME, cursorclass=pymysql.cursors.DictCursor,
            autocommit=False, charset="utf8mb4", ssl=_ssl_args(),
        )
    except (pymysql.err.OperationalError, ssl_module.SSLError, OSError) as exc:
        raise RuntimeError(
            f"Tidak bisa konek ke MySQL di {DB_HOST}:{DB_PORT} (database '{DB_NAME}'). "
            f"Pastikan server MySQL (DBngin) sudah jalan, database sudah dibuat, "
            f"dan kredensial di .env sudah benar. Detail: {exc}"
        ) from exc
    con = _ConnWrapper(raw)
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


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
        user = con.execute("SELECT id,name,username,email,pending_email,role,building_id,must_complete_profile FROM users WHERE id=? AND active=1", (claims["sub"],)).fetchone()
    if not user:
        raise HTTPException(status_code=401, detail="Akun tidak aktif.")
    return user


def require(*allowed: Role):
    def check(user: dict = Depends(current_user)):
        if user["role"] not in allowed:
            raise HTTPException(status_code=403, detail="Anda tidak memiliki izin untuk aksi ini.")
        return user
    return check


def assert_building_access(user: dict, building_id: int, write=False):
    if user["role"] == "super":
        return
    if user["role"] == "editor" and user["building_id"] == building_id:
        return
    if write:
        raise HTTPException(status_code=403, detail="Gedung ini tidak termasuk akses akun Anda.")
    # viewer & editor lain: boleh baca (read-only)


# ---------------------------------------------------------------------------
# Skema request
# ---------------------------------------------------------------------------
class Login(BaseModel):
    identifier: str = Field(min_length=1, max_length=190)  # email ATAU username
    password: str = Field(min_length=8)


class BuildingInput(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    district: str = Field(min_length=2, max_length=100)
    function: str = Field(min_length=2, max_length=100)
    area: float | None = Field(default=None, ge=0)
    address: str | None = Field(default=None, max_length=255)


class UserInput(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    username: str = Field(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9._-]+$")
    email: EmailStr | None = None
    role: Role
    building_id: int | None = None


class UserUpdateInput(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    username: str = Field(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9._-]+$")
    email: EmailStr | None = None
    role: Role
    building_id: int | None = None
    password: str | None = Field(default=None, min_length=8)


class CompleteProfileInput(BaseModel):
    email: EmailStr
    password: str | None = Field(default=None, min_length=8)


class BuildingInfoInput(BaseModel):
    leader_name: str | None = None
    leader_title: str | None = None
    year_built: str | None = None
    year_renovated: str | None = None
    orientation: str | None = None
    floor_count: str | None = None
    total_floor_area: str | None = None
    ac_floor_area: str | None = None
    energy_source: str | None = None
    pln_capacity_kva: str | None = None
    pln_id: str | None = None
    pam_id: str | None = None
    ebt_capacity: str | None = None
    genset_capacity: str | None = None
    staff_count: str | None = None
    working_hours: str | None = None


class ElectricityRow(BaseModel):
    month: int = Field(ge=1, le=12)
    wbp_kwh: float | None = None
    lwbp_kwh: float | None = None
    kvarh: float | None = None
    biaya_wbp: float | None = None
    biaya_lwbp: float | None = None
    biaya_kvarh: float | None = None


class WaterRow(BaseModel):
    month: int = Field(ge=1, le=12)
    total_m3: float | None = None
    rain_capacity_m3: float | None = None
    greywater_pct: float | None = None


class EbtRow(BaseModel):
    month: int = Field(ge=1, le=12)
    production: float | None = None


class EquipmentRow(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    daya_kw: float | None = None
    jumlah: int | None = None


class AcRow(BaseModel):
    floor: str | None = Field(default=None, max_length=50)
    room: str | None = Field(default=None, max_length=150)
    ac_type: str | None = Field(default=None, max_length=100)
    cooling_capacity: str | None = Field(default=None, max_length=100)
    refrigerant_type: str | None = Field(default=None, max_length=100)
    room_capacity: str | None = Field(default=None, max_length=100)
    temp_setting: str | None = Field(default=None, max_length=50)
    temp_measured: str | None = Field(default=None, max_length=50)
    notes: str | None = Field(default=None, max_length=255)


class LightingRow(BaseModel):
    floor: str | None = Field(default=None, max_length=50)
    room: str | None = Field(default=None, max_length=150)
    room_area: str | None = Field(default=None, max_length=50)
    lamp_type_power: str | None = Field(default=None, max_length=150)
    lamp_count: str | None = Field(default=None, max_length=50)
    hours_per_day: str | None = Field(default=None, max_length=50)
    sensor_used: str | None = Field(default=None, max_length=150)
    lux_measurement: str | None = Field(default=None, max_length=100)
    notes: str | None = Field(default=None, max_length=255)


class NotesInput(BaseModel):
    note: str | None = None


# ---------------------------------------------------------------------------
# Setup skema tabel
# ---------------------------------------------------------------------------
def init_db():
    with db() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS buildings (
          id INT AUTO_INCREMENT PRIMARY KEY,
          name VARCHAR(150) NOT NULL,
          district VARCHAR(100) NOT NULL,
          `function` VARCHAR(100) NOT NULL,
          area DOUBLE NULL,
          address VARCHAR(255) NULL,
          photo_path VARCHAR(255) NULL,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

        CREATE TABLE IF NOT EXISTS users (
          id INT AUTO_INCREMENT PRIMARY KEY,
          name VARCHAR(100) NOT NULL,
          username VARCHAR(50) NULL UNIQUE,
          email VARCHAR(190) NULL UNIQUE,
          pending_email VARCHAR(190) NULL,
          password_hash VARCHAR(255) NOT NULL,
          role ENUM('super','editor','viewer') NOT NULL,
          building_id INT NULL,
          must_complete_profile TINYINT(1) NOT NULL DEFAULT 0,
          active TINYINT(1) NOT NULL DEFAULT 1,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          CONSTRAINT fk_users_building FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

        CREATE TABLE IF NOT EXISTS building_info (
          building_id INT PRIMARY KEY,
          leader_name VARCHAR(150) NULL,
          leader_title VARCHAR(150) NULL,
          year_built VARCHAR(20) NULL,
          year_renovated VARCHAR(20) NULL,
          orientation VARCHAR(100) NULL,
          floor_count VARCHAR(20) NULL,
          total_floor_area VARCHAR(50) NULL,
          ac_floor_area VARCHAR(50) NULL,
          energy_source VARCHAR(150) NULL,
          pln_capacity_kva VARCHAR(50) NULL,
          pln_id VARCHAR(100) NULL,
          pam_id VARCHAR(100) NULL,
          ebt_capacity VARCHAR(100) NULL,
          genset_capacity VARCHAR(100) NULL,
          staff_count VARCHAR(20) NULL,
          working_hours VARCHAR(100) NULL,
          updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          CONSTRAINT fk_info_building FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

        CREATE TABLE IF NOT EXISTS electricity_consumption (
          id INT AUTO_INCREMENT PRIMARY KEY,
          building_id INT NOT NULL,
          year INT NOT NULL,
          month TINYINT NOT NULL,
          wbp_kwh DOUBLE NULL,
          lwbp_kwh DOUBLE NULL,
          total_kwh DOUBLE NULL,
          kvarh DOUBLE NULL,
          biaya_wbp DOUBLE NULL,
          biaya_lwbp DOUBLE NULL,
          biaya_kvarh DOUBLE NULL,
          total_biaya DOUBLE NULL,
          UNIQUE KEY uniq_elec (building_id, year, month),
          CONSTRAINT fk_elec_building FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

        CREATE TABLE IF NOT EXISTS water_consumption (
          id INT AUTO_INCREMENT PRIMARY KEY,
          building_id INT NOT NULL,
          year INT NOT NULL,
          month TINYINT NOT NULL,
          total_m3 DOUBLE NULL,
          rain_capacity_m3 DOUBLE NULL,
          greywater_pct DOUBLE NULL,
          UNIQUE KEY uniq_water (building_id, year, month),
          CONSTRAINT fk_water_building FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

        CREATE TABLE IF NOT EXISTS ebt_production (
          id INT AUTO_INCREMENT PRIMARY KEY,
          building_id INT NOT NULL,
          year INT NOT NULL,
          month TINYINT NOT NULL,
          production DOUBLE NULL,
          UNIQUE KEY uniq_ebt (building_id, year, month),
          CONSTRAINT fk_ebt_building FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

        CREATE TABLE IF NOT EXISTS building_equipment (
          id INT AUTO_INCREMENT PRIMARY KEY,
          building_id INT NOT NULL,
          sort_order INT NOT NULL DEFAULT 0,
          name VARCHAR(200) NULL,
          daya_kw DOUBLE NULL,
          jumlah INT NULL,
          CONSTRAINT fk_equipment_building FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

        CREATE TABLE IF NOT EXISTS building_ac_systems (
          id INT AUTO_INCREMENT PRIMARY KEY,
          building_id INT NOT NULL,
          sort_order INT NOT NULL DEFAULT 0,
          floor VARCHAR(50) NULL,
          room VARCHAR(150) NULL,
          ac_type VARCHAR(100) NULL,
          cooling_capacity VARCHAR(100) NULL,
          refrigerant_type VARCHAR(100) NULL,
          room_capacity VARCHAR(100) NULL,
          temp_setting VARCHAR(50) NULL,
          temp_measured VARCHAR(50) NULL,
          notes VARCHAR(255) NULL,
          CONSTRAINT fk_ac_building FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

        CREATE TABLE IF NOT EXISTS building_lighting (
          id INT AUTO_INCREMENT PRIMARY KEY,
          building_id INT NOT NULL,
          sort_order INT NOT NULL DEFAULT 0,
          floor VARCHAR(50) NULL,
          room VARCHAR(150) NULL,
          room_area VARCHAR(50) NULL,
          lamp_type_power VARCHAR(150) NULL,
          lamp_count VARCHAR(50) NULL,
          hours_per_day VARCHAR(50) NULL,
          sensor_used VARCHAR(150) NULL,
          lux_measurement VARCHAR(100) NULL,
          notes VARCHAR(255) NULL,
          CONSTRAINT fk_lighting_building FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

        CREATE TABLE IF NOT EXISTS building_notes (
          building_id INT PRIMARY KEY,
          note TEXT NULL,
          updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          CONSTRAINT fk_notes_building FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

        CREATE TABLE IF NOT EXISTS app_settings (
          `key` VARCHAR(50) PRIMARY KEY,
          value VARCHAR(255) NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        # Migrasi aman untuk instalasi lama (tabel sudah ada sebelum kolom ini ditambahkan)
        for table, column, ddl in [
            ("buildings", "address", "address VARCHAR(255) NULL"),
            ("buildings", "photo_path", "photo_path VARCHAR(255) NULL"),
            ("users", "username", "username VARCHAR(50) NULL UNIQUE"),
            ("users", "pending_email", "pending_email VARCHAR(190) NULL"),
            ("users", "must_complete_profile", "must_complete_profile TINYINT(1) NOT NULL DEFAULT 0"),
        ]:
            exists = con.execute(
                "SELECT COUNT(*) AS c FROM information_schema.columns "
                "WHERE table_schema = DATABASE() AND table_name = ? AND column_name = ?",
                (table, column),
            ).fetchone()
            if not exists["c"]:
                con.execute(f"ALTER TABLE {table} ADD COLUMN {ddl}")

        # Instalasi lama: kolom email semula NOT NULL — perlu dilonggarkan jadi
        # boleh kosong supaya akun tanpa email (login pakai username) bisa dibuat.
        email_col = con.execute(
            "SELECT is_nullable AS is_nullable FROM information_schema.columns "
            "WHERE table_schema = DATABASE() AND table_name = 'users' AND column_name = 'email'"
        ).fetchone()
        if email_col and str(email_col["is_nullable"]).upper() == "NO":
            con.execute("ALTER TABLE users MODIFY email VARCHAR(190) NULL")

        email = os.getenv("SUPER_EDITOR_EMAIL", "admin@jakut.go.id")
        if not con.execute("SELECT 1 FROM users WHERE email=?", (email,)).fetchone():
            con.execute(
                "INSERT INTO users(name,username,email,password_hash,role) VALUES(?,?,?,?,?)",
                ("Super Editor", "super", email, password_hash(os.getenv("SUPER_EDITOR_PASSWORD", "GantiPasswordKuat123!")), "super"),
            )


@app.on_event("startup")
def start():
    try:
        init_db()
    except Exception as exc:  # noqa: BLE001
        # Di lingkungan serverless (Vercel), kalau init_db() gagal (mis. DB belum
        # bisa dihubungi) dan exception dibiarkan lolos, seluruh ASGI app akan
        # dianggap gagal start ("Application startup failed") dan semua request
        # (termasuk request statis) ikut kena 500 tanpa pesan yang jelas.
        # Jadi di sini errornya cuma dicatat; percobaan konek berikutnya tetap
        # terjadi otomatis tiap kali endpoint /api/* dipanggil (lewat db()).
        print(f"[startup] init_db() gagal, akan dicoba lagi saat ada request: {exc}")


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
@app.get("/api/health")
def health():
    try:
        with db() as con:
            con.execute("SELECT 1")
        return {"database": "connected", "name": DB_NAME, "host": f"{DB_HOST}:{DB_PORT}"}
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/api/auth/login")
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


@app.get("/api/auth/me")
def me(user=Depends(current_user)):
    return user


# ---------------------------------------------------------------------------
# Buildings
# ---------------------------------------------------------------------------
@app.get("/api/buildings")
def list_buildings(user=Depends(current_user)):
    # Semua peran boleh MELIHAT seluruh gedung (read-only untuk editor/viewer di
    # luar gedung yang ditugaskan). Pembatasan hanya berlaku untuk aksi tulis
    # (lihat assert_building_access), bukan di sini.
    with db() as con:
        rows = con.execute("SELECT * FROM buildings ORDER BY name").fetchall()
    return rows


@app.post("/api/buildings", status_code=status.HTTP_201_CREATED)
def create_building(data: BuildingInput, user=Depends(require("super"))):
    with db() as con:
        cur = con.execute(
            "INSERT INTO buildings(name,district,`function`,area,address) VALUES(?,?,?,?,?)",
            (data.name, data.district, data.function, data.area, data.address),
        )
        return con.execute("SELECT * FROM buildings WHERE id=?", (cur.lastrowid,)).fetchone()


@app.put("/api/buildings/{building_id}")
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


@app.delete("/api/buildings/{building_id}", status_code=204)
def delete_building(building_id: int, user=Depends(require("super"))):
    with db() as con:
        con.execute("DELETE FROM buildings WHERE id=?", (building_id,))


@app.post("/api/buildings/{building_id}/photo")
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


@app.delete("/api/buildings/{building_id}/photo", status_code=204)
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
@app.get("/api/buildings/{building_id}/info")
def get_building_info(building_id: int, user=Depends(current_user)):
    assert_building_access(user, building_id, write=False)
    with db() as con:
        row = con.execute("SELECT * FROM building_info WHERE building_id=?", (building_id,)).fetchone()
    return row or {"building_id": building_id}


@app.put("/api/buildings/{building_id}/info")
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


@app.get("/api/buildings/{building_id}/electricity")
def get_electricity(building_id: int, year: int = Query(...), user=Depends(current_user)):
    assert_building_access(user, building_id, write=False)
    return _monthly_get("electricity_consumption", building_id, year)


@app.put("/api/buildings/{building_id}/electricity")
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


@app.get("/api/buildings/{building_id}/water")
def get_water(building_id: int, year: int = Query(...), user=Depends(current_user)):
    assert_building_access(user, building_id, write=False)
    return _monthly_get("water_consumption", building_id, year)


@app.put("/api/buildings/{building_id}/water")
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


@app.get("/api/buildings/{building_id}/ebt")
def get_ebt(building_id: int, year: int = Query(...), user=Depends(current_user)):
    assert_building_access(user, building_id, write=False)
    return _monthly_get("ebt_production", building_id, year)


@app.put("/api/buildings/{building_id}/ebt")
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


def _list_replace(table: str, cols: list[str], building_id: int, rows: list[BaseModel]) -> list[dict]:
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


@app.get("/api/buildings/{building_id}/equipment")
def get_equipment(building_id: int, user=Depends(current_user)):
    assert_building_access(user, building_id, write=False)
    return _list_get("building_equipment", building_id)


@app.put("/api/buildings/{building_id}/equipment")
def save_equipment(building_id: int, rows: list[EquipmentRow], user=Depends(require("super", "editor"))):
    assert_building_access(user, building_id, write=True)
    return _list_replace("building_equipment", ["name", "daya_kw", "jumlah"], building_id, rows)


@app.get("/api/buildings/{building_id}/ac-systems")
def get_ac_systems(building_id: int, user=Depends(current_user)):
    assert_building_access(user, building_id, write=False)
    return _list_get("building_ac_systems", building_id)


@app.put("/api/buildings/{building_id}/ac-systems")
def save_ac_systems(building_id: int, rows: list[AcRow], user=Depends(require("super", "editor"))):
    assert_building_access(user, building_id, write=True)
    return _list_replace(
        "building_ac_systems",
        ["floor", "room", "ac_type", "cooling_capacity", "refrigerant_type", "room_capacity", "temp_setting", "temp_measured", "notes"],
        building_id, rows,
    )


@app.get("/api/buildings/{building_id}/lighting")
def get_lighting(building_id: int, user=Depends(current_user)):
    assert_building_access(user, building_id, write=False)
    return _list_get("building_lighting", building_id)


@app.put("/api/buildings/{building_id}/lighting")
def save_lighting(building_id: int, rows: list[LightingRow], user=Depends(require("super", "editor"))):
    assert_building_access(user, building_id, write=True)
    return _list_replace(
        "building_lighting",
        ["floor", "room", "room_area", "lamp_type_power", "lamp_count", "hours_per_day", "sensor_used", "lux_measurement", "notes"],
        building_id, rows,
    )


@app.get("/api/buildings/{building_id}/notes")
def get_notes(building_id: int, user=Depends(current_user)):
    assert_building_access(user, building_id, write=False)
    with db() as con:
        row = con.execute("SELECT * FROM building_notes WHERE building_id=?", (building_id,)).fetchone()
    return row or {"building_id": building_id, "note": ""}


@app.put("/api/buildings/{building_id}/notes")
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


# ---------------------------------------------------------------------------
# Ringkasan Dashboard (agregat lintas gedung, mengikuti filter wilayah/fungsi)
# ---------------------------------------------------------------------------
CO2_FACTOR_KG_PER_KWH = 0.87  # faktor emisi grid nasional Indonesia (perkiraan umum)


@app.get("/api/dashboard/summary")
def dashboard_summary(
    year: int = Query(...),
    district: str | None = None,
    function: str | None = None,
    user=Depends(current_user),
):
    # Semua peran melihat ringkasan seluruh gedung (read-only) — konsisten
    # dengan list_buildings. Hak tulis tetap dibatasi per-gedung di endpoint lain.
    conditions = []
    params: list = []

    if district:
        conditions.append("b.district = ?")
        params.append(district)
    if function:
        conditions.append("b.`function` = ?")
        params.append(function)

    where = " AND ".join(conditions) if conditions else "1=1"

    with db() as con:
        b_row = con.execute(f"SELECT COUNT(*) AS c, COALESCE(SUM(area),0) AS area FROM buildings b WHERE {where}", params).fetchone()
        elec_row = con.execute(
            f"SELECT COALESCE(SUM(e.total_kwh),0) AS total_kwh FROM electricity_consumption e "
            f"JOIN buildings b ON b.id = e.building_id WHERE e.year=? AND {where}",
            [year] + params,
        ).fetchone()
        water_row = con.execute(
            f"SELECT COALESCE(SUM(w.total_m3),0) AS total_m3 FROM water_consumption w "
            f"JOIN buildings b ON b.id = w.building_id WHERE w.year=? AND {where}",
            [year] + params,
        ).fetchone()
        ebt_row = con.execute(
            f"SELECT COALESCE(SUM(x.production),0) AS production FROM ebt_production x "
            f"JOIN buildings b ON b.id = x.building_id WHERE x.year=? AND {where}",
            [year] + params,
        ).fetchone()
        # Baris per gedung (join subquery agar area tidak terduplikasi oleh baris bulanan)
        per_building = con.execute(
            f"""SELECT b.id, b.district, b.area, COALESCE(elec.total_kwh,0) AS total_kwh
                FROM buildings b
                LEFT JOIN (
                    SELECT building_id, SUM(total_kwh) AS total_kwh
                    FROM electricity_consumption WHERE year=? GROUP BY building_id
                ) elec ON elec.building_id = b.id
                WHERE {where}""",
            [year] + params,
        ).fetchall()

    total_kwh = float(elec_row["total_kwh"] or 0)
    total_area = float(b_row["area"] or 0)
    ike = (total_kwh / total_area) if total_area > 0 else None

    def categorize(b_ike: float) -> str:
        if b_ike < 50:
            return "Sangat Efisien"
        if b_ike <= 100:
            return "Efisien"
        if b_ike <= 150:
            return "Cukup Efisien"
        return "Boros"

    district_totals: dict[str, dict[str, float]] = {}
    categories = {"Sangat Efisien": 0, "Efisien": 0, "Cukup Efisien": 0, "Boros": 0}
    no_data_count = 0
    per_building_stats = []
    for r in per_building:
        d = district_totals.setdefault(r["district"], {"kwh": 0.0, "area": 0.0})
        r_area = float(r["area"] or 0)
        r_kwh = float(r["total_kwh"] or 0)
        d["kwh"] += r_kwh
        d["area"] += r_area

        if r_area > 0 and r_kwh > 0:
            b_ike = r_kwh / r_area
            b_cat = categorize(b_ike)
            categories[b_cat] += 1
        else:
            b_ike = None
            b_cat = None
            no_data_count += 1
        per_building_stats.append({"id": r["id"], "ike": b_ike, "category": b_cat})

    by_district = [
        {"district": d, "ike": (v["kwh"] / v["area"]) if v["area"] > 0 else None}
        for d, v in sorted(district_totals.items())
    ]

    return {
        "buildings_count": b_row["c"],
        "total_kwh": total_kwh,
        "ike": ike,
        "total_water_m3": float(water_row["total_m3"] or 0),
        "total_ebt": float(ebt_row["production"] or 0),
        "co2_ton": (total_kwh * CO2_FACTOR_KG_PER_KWH) / 1000,
        "by_district": by_district,
        "by_category": categories,
        "no_data_count": no_data_count,
        "buildings": per_building_stats,
    }


# ---------------------------------------------------------------------------
# Pengaturan aplikasi (logo, dst.) — GET logo TIDAK butuh login karena
# halaman login sendiri perlu menampilkannya.
# ---------------------------------------------------------------------------
def _get_setting(con, key: str) -> str | None:
    row = con.execute("SELECT value FROM app_settings WHERE `key`=?", (key,)).fetchone()
    return row["value"] if row else None


def _set_setting(con, key: str, value: str | None):
    con.execute(
        "INSERT INTO app_settings(`key`,value) VALUES(?,?) ON DUPLICATE KEY UPDATE value=VALUES(value)",
        (key, value),
    )


@app.get("/api/settings/logo")
def get_logo():
    with db() as con:
        path = _get_setting(con, "logo_path")
    return {"logo_path": path}


@app.post("/api/settings/logo")
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


@app.delete("/api/settings/logo", status_code=204)
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


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------
@app.get("/api/users")
def list_users(user=Depends(require("super"))):
    with db() as con:
        rows = con.execute(
            "SELECT u.id,u.name,u.username,u.email,u.pending_email,u.role,u.building_id,u.must_complete_profile,b.name AS building "
            "FROM users u LEFT JOIN buildings b ON b.id=u.building_id ORDER BY u.name"
        ).fetchall()
    return rows


def _generate_temp_password() -> str:
    return "Awal" + secrets.token_hex(3)  # contoh: Awal4f9a21 (10 karakter)


@app.post("/api/users", status_code=201)
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


@app.delete("/api/users/{user_id}", status_code=204)
def delete_user(user_id: int, user=Depends(require("super"))):
    if user_id == user["id"]:
        raise HTTPException(status_code=400, detail="Tidak bisa menghapus akun yang sedang login.")
    with db() as con:
        con.execute("DELETE FROM users WHERE id=?", (user_id,))


@app.put("/api/users/{user_id}")
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


@app.post("/api/auth/complete-profile")
def complete_profile(data: CompleteProfileInput, user=Depends(current_user)):
    """Dipanggil pengguna sendiri (dibuat tanpa email oleh Super Editor) untuk
    mengajukan email aktif + kata sandi baru. Kata sandi langsung berlaku;
    email baru berlaku SETELAH disetujui Super Editor (lihat approve_email)."""
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


@app.post("/api/users/{user_id}/approve-email")
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


@app.post("/api/users/{user_id}/reject-email")
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


if os.getenv("VERCEL"):
    # File yang diupload saat runtime disimpan di /tmp (lihat UPLOAD_DIR/BRANDING_DIR di atas),
    # jadi perlu di-mount terpisah supaya bisa diakses lewat /uploads/...
    _UPLOAD_BASE.mkdir(parents=True, exist_ok=True)
    (_UPLOAD_BASE / "buildings").mkdir(parents=True, exist_ok=True)
    (_UPLOAD_BASE / "branding").mkdir(parents=True, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=_UPLOAD_BASE), name="uploads")
app.mount("/", StaticFiles(directory=ROOT, html=True), name="web")
