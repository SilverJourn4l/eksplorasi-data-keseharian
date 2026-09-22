"""Unduh suhu harian Jakarta untuk Edisi 001 dan susun data olahan.

Sumber utama: Open-Meteo Historical Weather API (reanalisis ERA5). Sumber uji silang: NASA POWER
(MERRA-2), diunduh per tahun karena API-nya membatasi rentang per permintaan. Catatan uji
kelayakan sumber ada di README edisi.
"""

import json
import time
from datetime import date
from pathlib import Path

import pandas as pd
import requests

UA = {"User-Agent": "JurnalDataKeseharian/1.0 (jurnal edukasi)"}
MENTAH = Path("data/mentah")
LAT, LON = -6.18, 106.83  # titik Jakarta Pusat
MULAI, AKHIR = "1950-01-01", date.today().isoformat()


def unduh_open_meteo():
    params = {
        "latitude": LAT, "longitude": LON, "start_date": MULAI, "end_date": AKHIR,
        "daily": "temperature_2m_max,temperature_2m_min,temperature_2m_mean",
        "timezone": "Asia/Jakarta",
    }
    r = requests.get("https://archive-api.open-meteo.com/v1/archive", params=params, headers=UA, timeout=90)
    r.raise_for_status()
    body = r.json()
    MENTAH.mkdir(parents=True, exist_ok=True)
    (MENTAH / "open-meteo-era5-jakarta.json").write_text(
        json.dumps({"diminta": params, "koordinat_grid": {k: body.get(k) for k in ("latitude", "longitude", "elevation")},
                    "respons": body},
                   ensure_ascii=False, indent=1),
        encoding="utf-8",
    )
    return body


def unduh_nasa_power():
    MENTAH.mkdir(parents=True, exist_ok=True)
    hasil = {}
    for tahun in range(1984, date.today().year + 1):
        params = {
            "parameters": "T2M_MAX,T2M", "community": "AG", "longitude": LON, "latitude": LAT,
            "start": f"{tahun}0101", "end": f"{tahun}1231", "format": "JSON",
        }
        r = requests.get("https://power.larc.nasa.gov/api/temporal/daily/point", params=params,
                         headers=UA, timeout=60)
        r.raise_for_status()
        hasil[tahun] = r.json()
        time.sleep(0.4)
    (MENTAH / "nasa-power-jakarta.json").write_text(json.dumps(hasil, indent=1), encoding="utf-8")
    return hasil


def susun(open_meteo, power):
    harian = open_meteo["daily"]
    df = pd.DataFrame({
        "tanggal": harian["time"],
        "tmax_era5": harian["temperature_2m_max"],
        "tmin_era5": harian["temperature_2m_min"],
        "tmean_era5": harian["temperature_2m_mean"],
    })

    baris_power = []
    for tahun, body in power.items():
        param = body["properties"]["parameter"]
        for tanggal, nilai in param["T2M"].items():
            baris_power.append({
                "tanggal": f"{tanggal[:4]}-{tanggal[4:6]}-{tanggal[6:]}",
                "tmean_power": None if nilai == -999 else nilai,
                "tmax_power": None if param["T2M_MAX"].get(tanggal, -999) == -999 else param["T2M_MAX"].get(tanggal),
            })
    df = df.merge(pd.DataFrame(baris_power), on="tanggal", how="left")
    df["tanggal"] = pd.to_datetime(df["tanggal"])
    for kolom in df.columns[1:]:
        df[kolom] = pd.to_numeric(df[kolom], errors="coerce")
    df.to_csv("data/suhu-harian-jakarta.csv", index=False)
    return df


def lapor(df):
    print("rentang:", df.tanggal.min().date(), "s.d.", df.tanggal.max().date(), "| baris:", len(df))
    print("hilang per kolom:\n", df.isna().sum().to_string())
    tahun_lengkap = df.groupby(df.tanggal.dt.year).size()
    tahun_parsial = tahun_lengkap[tahun_lengkap < 365]
    print("tahun tidak penuh:", dict(tahun_parsial))


def main():
    open_meteo = unduh_open_meteo()
    power = unduh_nasa_power()
    df = susun(open_meteo, power)
    lapor(df)


if __name__ == "__main__":
    main()
