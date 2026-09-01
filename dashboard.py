from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.auth import current_user
from app.database import db

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

CO2_FACTOR_KG_PER_KWH = 0.87  # faktor emisi grid nasional Indonesia (perkiraan umum)


@router.get("/summary")
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
