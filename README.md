# EnergiGedung

Backend FastAPI + MySQL untuk Sistem Monitoring Efisiensi Energi Bangunan Gedung.

## 1. Siapkan database MySQL (lewat DBngin)

1. Buka **DBngin**, pastikan service MySQL kamu berstatus **jalan** (hijau).
2. Buat database baru bernama `db_energi` — bisa lewat aplikasi database client
   (TablePlus, Sequel Ace, dsb.) yang biasanya sudah tersambung ke DBngin, atau
   lewat terminal:
   ```bash
   mysql -h 127.0.0.1 -P 3306 -u root -e "CREATE DATABASE db_energi CHARACTER SET utf8mb4;"
   ```
   (Kalau MySQL kamu punya password, tambahkan `-p` lalu masukkan passwordnya.)

   Aplikasi ini **tidak membuat database-nya sendiri** — hanya membuat
   tabel-tabel di dalamnya secara otomatis saat pertama kali dijalankan.
   Jadi langkah ini wajib dilakukan sekali di awal.

## 2. Konfigurasi koneksi

```bash
cp .env.example .env
```
Buka file `.env` dan sesuaikan `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`,
`DB_NAME` dengan detail koneksi MySQL di DBngin kamu (defaultnya biasanya
`127.0.0.1`, port `3306`, user `root`, password kosong — cek di aplikasi
DBngin kalau tidak yakin).

## 3. Jalankan

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Buka `http://127.0.0.1:8000`. Dokumentasi API interaktif ada di `/docs`.

Login awal (dibuat otomatis saat pertama kali start, sesuai `.env`):
**`admin@jakut.go.id`** / **`GantiPasswordKuat123!`**

Kalau muncul error saat start terkait koneksi database, baca pesannya —
sudah dibuat jelas menyebutkan kemungkinan penyebabnya (server belum jalan,
database belum dibuat, atau kredensial salah).

## 4. Cek koneksi database dari dalam aplikasi

Setelah login, buka menu **Pengaturan** — ada indikator status koneksi ke
MySQL (✅ terhubung / ❌ gagal, lengkap dengan pesan errornya) yang benar-benar
mengecek koneksi saat itu juga, bukan teks statis.

## Aturan otorisasi

- `super`: CRUD semua gedung, kelola pengguna (tambah/lihat detail/hapus).
- `editor`: membaca semua gedung, tapi hanya boleh **mengubah** gedung yang
  ditugaskan kepadanya.
- `viewer`: hanya membaca (read-only) semua gedung.

Semua endpoint `/api/*` menerapkan aturan ini di sisi server (bukan cuma
disembunyikan di tampilan), jadi tetap aman meski frontend dimodifikasi.

## Fitur yang sudah bisa diisi & tersimpan ke MySQL

- Data dasar gedung (Nama, Kecamatan, Fungsi, Luas, Alamat) — tambah & ubah
- **Informasi Umum** per gedung (nama pimpinan, tahun berdiri, ID PLN/PAM, dst.)
- **Konsumsi Listrik** per bulan (WBP, LWBP, kVArh, biaya) — 12 baris/tahun
- **Konsumsi Air** per bulan (total pemakaian, kapasitas air hujan, daur ulang greywater)
- **Produksi EBT** per bulan
- Kelola pengguna (tambah, lihat detail, hapus) — khusus Super Editor

Semua form di atas punya pola **Edit → isi → Simpan**, dan tersimpan
langsung ke tabel MySQL terkait (lihat `main.py` untuk skema tabelnya).

## Belum tersedia (tahap berikutnya)

Tab **Peralatan Listrik**, **Sistem Tata Udara**, **Sistem Pencahayaan**, dan
**Catatan Tambahan** di halaman detail gedung masih berupa placeholder
(klik akan memunculkan notifikasi) — struktur datanya beda-beda dan belum
dibuatkan tabel serta form-nya. Kabari kalau mau lanjutkan bagian ini.

## Struktur tabel MySQL

Dibuat otomatis saat aplikasi start: `buildings`, `users`, `building_info`,
`electricity_consumption`, `water_consumption`, `ebt_production`,
`building_equipment`, `building_ac_systems`, `building_lighting`,
`building_notes`, `app_settings`. Detail kolomnya ada di fungsi `init_db()`
pada `app/database.py`.

## Struktur Proyek

```
main.py                  # Entry point — hanya setup FastAPI & wiring router
app/
  database.py             # Koneksi MySQL (PyMySQL), konfigurasi, init_db()
  auth.py                 # Hashing password, token akses, dependency current_user
  schemas.py               # Model Pydantic request/response
  routers/
    auth.py                # /api/health, /api/auth/*
    buildings.py            # /api/buildings/* (gedung, listrik, air, EBT, inventaris)
    dashboard.py             # /api/dashboard/summary
    settings.py              # /api/settings/logo
    users.py                 # /api/users/*
static/                  # Frontend (index.html, script.js, styles.css)
uploads/
  buildings/               # Foto gedung yang diunggah
  branding/                 # Logo instansi yang diunggah
```

Menambah endpoint baru cukup dilakukan di file router yang relevan (atau
buat router baru di `app/routers/`), lalu daftarkan lewat
`app.include_router(...)` di `main.py`.
