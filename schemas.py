"""Skema request (Pydantic) yang dipakai bersama oleh router-router di app/routers/."""
from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field

from app.auth import Role


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
