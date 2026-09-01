"""Entry point Sistem Monitoring Efisiensi Energi Bangunan Gedung.

File ini HANYA bertugas: membuat instance FastAPI, menyambungkan seluruh
router (lihat app/routers/), menjalankan init_db() saat startup, dan
menyajikan frontend statis (folder static/) beserta berkas upload (uploads/).

Struktur proyek:
  main.py              <- file ini (entry point, tipis)
  app/
    database.py        <- koneksi MySQL, konfigurasi, init_db()
    auth.py             <- hashing password, token, dependency current_user
    schemas.py          <- model Pydantic request/response
    routers/
      auth.py           <- /api/health, /api/auth/*
      buildings.py      <- /api/buildings/* (data gedung, listrik, air, EBT, dst)
      dashboard.py      <- /api/dashboard/summary
      settings.py       <- /api/settings/logo
      users.py          <- /api/users/*
  static/               <- frontend (index.html, script.js, styles.css)
  uploads/              <- foto gedung & logo yang diunggah pengguna
"""
from __future__ import annotations

import os

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.database import ROOT, UPLOAD_BASE, init_db
from app.routers import auth, buildings, dashboard, settings, users

app = FastAPI(title="EnergiGedung API", version="2.0.0")


@app.exception_handler(RuntimeError)
async def db_error_handler(request: Request, exc: RuntimeError):
    return JSONResponse(status_code=503, content={"detail": str(exc)})


# ---------------------------------------------------------------------------
# Daftarkan seluruh router
# ---------------------------------------------------------------------------
app.include_router(auth.router)
app.include_router(buildings.router)
app.include_router(dashboard.router)
app.include_router(settings.router)
app.include_router(users.router)


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
# Berkas statis: frontend (static/) dan upload pengguna (uploads/)
# ---------------------------------------------------------------------------
if os.getenv("VERCEL"):
    # File yang diupload saat runtime disimpan di /tmp (lihat app/database.py),
    # jadi perlu di-mount terpisah supaya bisa diakses lewat /uploads/...
    UPLOAD_BASE.mkdir(parents=True, exist_ok=True)
    (UPLOAD_BASE / "buildings").mkdir(parents=True, exist_ok=True)
    (UPLOAD_BASE / "branding").mkdir(parents=True, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=UPLOAD_BASE), name="uploads")
else:
    # Lokal (development): upload disimpan langsung di uploads/ dalam project.
    (ROOT / "uploads" / "buildings").mkdir(parents=True, exist_ok=True)
    (ROOT / "uploads" / "branding").mkdir(parents=True, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=ROOT / "uploads"), name="uploads")

app.mount("/", StaticFiles(directory=ROOT / "static", html=True), name="web")
