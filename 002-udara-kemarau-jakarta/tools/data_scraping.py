"""Unduh PM2,5 dan curah hujan harian Jakarta untuk Edisi 002 dan susun data olahan.

Sumber utama: Open-Meteo Air Quality API (reanalisis CAMS), kualitas udara per jam sejak
4 Agustus 2022. Sumber pendukung: Open-Meteo Historical Weather (ERA5), curah hujan harian,
untuk verifikasi penandaan musim. Catatan uji kelayakan sumber ada di README edisi.
"""

import json
from datetime import date
from pathlib import Path

import pandas as pd
import requests

UA = {"User-Agent": "JurnalDataKeseharian/1.0 (jurnal edukasi; kontak: pengelola@example.com)"}
MENTAH = Path("data/mentah")
LAT, LON = -6.18, 106.83  # titik Jakarta Pusat
MULAI, AKHIR = "2022-08-01", date.today().isoformat()


def unduh_cams():
    params = {
        "latitude": LAT, "longitude": LON, "start_date": MULAI, "end_date": AKHIR,
        "hourly": "pm2_5,pm10,us_aqi", "timezone": "Asia/Jakarta",
    }
    r = requests.get("https://air-quality-api.open-meteo.com/v1/air-quality",
                     params=params, headers=UA, timeout=90)
    r.raise_for_status()
    body = r.json()
    MENTAH.mkdir(parents=True, exist_ok=True)
    (MENTAH / "cams-udara-jakarta.json").write_text(
        json.dumps({"diminta": params,
                    "koordinat_grid": {k: body.get(k) for k in ("latitude", "longitude", "timezone")},
                    "respons": body},
                   ensure_ascii=False, indent=1),
        encoding="utf-8",
    )
    return body


def unduh_hujan():
    params = {
        "latitude": LAT, "longitude": LON, "start_date": MULAI, "end_date": AKHIR,
        "daily": "precipitation_sum", "timezone": "Asia/Jakarta",
    }
    r = requests.get("https://archive-api.open-meteo.com/v1/archive",
                     params=params, headers=UA, timeout=90)
    r.raise_for_status()
    body = r.json()
    (MENTAH / "era5-hujan-jakarta.json").write_text(
        json.dumps({"diminta": params, "respons": body}, ensure_ascii=False, indent=1),
        encoding="utf-8",
    )
    return body


def susun(cams, hujan):
    jam = cams["hourly"]
    df = pd.DataFrame({"jam": jam["time"], "pm2_5": jam["pm2_5"],
                       "pm10": jam["pm10"], "us_aqi": jam["us_aqi"]})
    df["jam"] = pd.to_datetime(df["jam"])
    for kolom in ("pm2_5", "pm10", "us_aqi"):
        df[kolom] = pd.to_numeric(df[kolom], errors="coerce")
    df["tanggal"] = df.jam.dt.normalize()
    harian = df.groupby("tanggal").agg(
        pm2_5=("pm2_5", "mean"), pm2_5_maks=("pm2_5", "max"),
        pm10=("pm10", "mean"), us_aqi=("us_aqi", "max"),
        jam_terisi=("pm2_5", "count"),
    ).reset_index()
    # rata-rata harian hanya sah bila cukup jam terisi (WHO memakai minimal 18 jam)
    harian.loc[harian.jam_terisi < 18, ["pm2_5", "pm2_5_maks", "pm10", "us_aqi"]] = pd.NA

    h = hujan["daily"]
    hujan_harian = pd.DataFrame({"tanggal": h["time"], "hujan_mm": h["precipitation_sum"]})
    hujan_harian["tanggal"] = pd.to_datetime(hujan_harian["tanggal"])
    out = harian.merge(hujan_harian, on="tanggal", how="left")
    out.to_csv("data/udara-harian-jakarta.csv", index=False)
    return out


def lapor(df):
    print("rentang:", df.tanggal.min().date(), "s.d.", df.tanggal.max().date(), "| baris:", len(df))
    print("hilang per kolom:\n", df.isna().sum().to_string())
    print("hari per tahun:", dict(df.groupby(df.tanggal.dt.year).size()))
    kurang = df[df.jam_terisi < 18]
    print("hari <18 jam terisi (dihapus dari pm2_5):", len(kurang))


def main():
    cams = unduh_cams()
    hujan = unduh_hujan()
    df = susun(cams, hujan)
    lapor(df)


if __name__ == "__main__":
    main()
