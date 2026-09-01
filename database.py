"""Koneksi & inisialisasi database MySQL (via PyMySQL).

Backend ini terhubung ke MySQL (mis. lewat DBngin di Mac, atau Aiven di
produksi). Konfigurasi koneksi diambil dari environment variable / file .env
(lihat .env.example). Pastikan database-nya sudah DIBUAT lebih dulu di MySQL:

    CREATE DATABASE db_energi CHARACTER SET utf8mb4;

Tabel-tabel di dalamnya dibuat otomatis oleh init_db() saat aplikasi start.
"""
from __future__ import annotations

import os
import ssl as ssl_module
from contextlib import contextmanager
from pathlib import Path

import pymysql
import pymysql.cursors
from dotenv import load_dotenv

# ROOT menunjuk ke root project (satu tingkat di atas folder app/)
ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "db_energi")

# Di Vercel, filesystem project bersifat read-only kecuali /tmp — jadi file yang
# diupload user (foto gedung, logo) diarahkan ke /tmp supaya tidak error saat ditulis.
# CATATAN: /tmp bersifat sementara (bisa hilang saat function di-restart/cold start),
# jadi ini cukup untuk demo tapi bukan solusi penyimpanan permanen.
UPLOAD_BASE = Path("/tmp/uploads") if os.getenv("VERCEL") else (ROOT / "uploads")
UPLOAD_DIR = UPLOAD_BASE / "buildings"
BRANDING_DIR = UPLOAD_BASE / "branding"
ALLOWED_IMAGE_TYPES = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp", "image/gif": "gif"}
MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5MB


class _ConnWrapper:
    """Bikin pemakaian mirip sqlite3 (con.execute(...).fetchone()) di atas PyMySQL,
    supaya kode di endpoint tetap ringkas. Placeholder `?` otomatis dikonversi ke `%s`.
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

        # Import di sini (bukan di top-level) untuk menghindari circular import
        # dengan app.auth, yang juga meng-import dari app.database.
        from app.auth import password_hash

        email = os.getenv("SUPER_EDITOR_EMAIL", "admin@jakut.go.id")
        if not con.execute("SELECT 1 FROM users WHERE email=?", (email,)).fetchone():
            con.execute(
                "INSERT INTO users(name,username,email,password_hash,role) VALUES(?,?,?,?,?)",
                ("Super Editor", "super", email, password_hash(os.getenv("SUPER_EDITOR_PASSWORD", "GantiPasswordKuat123!")), "super"),
            )
