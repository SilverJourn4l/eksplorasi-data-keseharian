"""
Pengambilan data Edisi 007.
"""
from __future__ import annotations

import argparse
import json
import random
import time
from datetime import date
from pathlib import Path

import pandas as pd
import requests

FOLDER = Path(__file__).parent
MENTAH_PH = FOLDER / "data" / "mentah" / "pihps"
MENTAH_OECD = FOLDER / "data" / "mentah" / "oecd"

BULAN_MULAI = (2018, 10)     # agar transisi Des2018->Jan2019 ikut
BULAN_AKHIR = (2026, 8)
TANGGAL_DIMINTA = 15         # pertengahan bulan; server bergeser ke rilis terakhir
KOMODITAS = {i: None for i in range(1, 11)}   # 10 komoditas nasional; nama dari respons
JEDA, JITTER, GAGAL_BERUNTUN_MAKS = 1.4, 0.6, 6

B = "https://www.bi.go.id/hargapangan/WebSite/Home/GetGridData1"
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/125.0 Safari/537.36",
     "X-Requested-With": "XMLHttpRequest", "Referer": "https://www.bi.go.id/hargapangan"}
BULAN_EN = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
BULAN_SINGKAT = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "mei": 5, "jun": 6,
                 "jul": 7, "agu": 8, "sep": 9, "okt": 10, "nov": 11, "des": 12}


def bulan_iter(y0, m0, y1, m1):
    y, m = y0, m0
    while (y, m) <= (y1, m1):
        yield y, m
        m += 1
        if m > 12:
            y, m = y + 1, 1


def label_tanggal(y, m):
    return f"{BULAN_EN[m]} {TANGGAL_DIMINTA}, {y}"


def parse_tanggal_balas(t):
    bagian = (t or "").split()
    if len(bagian) != 3 or bagian[1].lower() not in BULAN_SINGKAT:
        return None
    try:
        return date(2000 + int(bagian[2]), BULAN_SINGKAT[bagian[1].lower()], int(bagian[0]))
    except ValueError:
        return None


def ambil(sesi, y, m, kom):
    nama = MENTAH_PH / f"{kom}_{y}-{m:02d}.json"
    if nama.exists():
        return json.loads(nama.read_text()), 200
    r = sesi.get(B, headers=H, params={"tanggal": label_tanggal(y, m), "commodity": kom,
                                       "priceType": 1, "isPasokan": 1, "jenis": 1,
                                       "periode": 1, "provId": 0, "_": int(time.time() * 1000)},
                 timeout=30)
    if r.status_code != 200:
        return None, r.status_code
    try:
        isi = r.json()
    except ValueError:
        return None, r.status_code
    nama.write_text(json.dumps(isi, ensure_ascii=False))
    return isi, 200


def bangun_csv():
    nas, prov = [], []
    for nama in sorted(MENTAH_PH.glob("*.json")):
        try:
            isi = json.loads(nama.read_text())
        except ValueError:
            continue
        data = isi.get("data", [])
        if not data:
            continue
        tgl = parse_tanggal_balas(data[0].get("Tanggal"))
        if tgl is None:
            continue
        nas.append({"tanggal": tgl.isoformat(), "komoditas": data[0].get("Komoditas"),
                    "harga_nasional": data[0].get("SemuaProvinsi")})
        for b in data:
            prov.append({"tanggal": tgl.isoformat(), "komoditas": b.get("Komoditas"),
                         "provinsi": b.get("Provinsi"), "harga": b.get("Nilai")})
    nasional = (pd.DataFrame(nas).drop_duplicates(["tanggal", "komoditas"])
                  .sort_values(["komoditas", "tanggal"]))
    provinsi = pd.DataFrame(prov).drop_duplicates(["tanggal", "komoditas", "provinsi"])
    nasional.to_csv(FOLDER / "data" / "harga-nasional-bulanan.csv", index=False)
    provinsi.to_csv(FOLDER / "data" / "harga-provinsi-bulanan.csv", index=False)
    return nasional, provinsi


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batasi", type=int, default=0)
    ap.add_argument("--tahap-oecd", action="store_true", help="lewati PIHPS (sudah di-mentah)")
    args = ap.parse_args()
    MENTAH_PH.mkdir(parents=True, exist_ok=True)

    sesi = requests.Session()
    tugas = [(kom, y, m) for y, m in bulan_iter(*BULAN_MULAI, *BULAN_AKHIR) for kom in sorted(KOMODITAS)]
    if args.tahap_oecd:
        tugas = []
    if args.batasi:
        tugas = tugas[: args.batasi]
    n_ambil = n_cache = n_kosong = gagal_run = 0
    for i, (kom, y, m) in enumerate(tugas, 1):
        if (MENTAH_PH / f"{kom}_{y}-{m:02d}.json").exists():
            n_cache += 1
            continue
        isi, kode = ambil(sesi, y, m, kom)
        if isi is None:
            gagal_run += 1
            print(f"[{i}/{len(tugas)}] {y}-{m:02d} kom{kom} GAGAL {kode}")
            if gagal_run >= GAGAL_BERUNTUN_MAKS or kode in (403, 429):
                print("Berhenti sopan: diblok beruntun.")
                break
        else:
            gagal_run = 0
            n_ambil += 1
            if not isi.get("data"):
                n_kosong += 1
            if n_ambil % 200 == 0:
                print(f"[{i}/{len(tugas)}] ambil {n_ambil} | cache {n_cache} | kosong {n_kosong}", flush=True)
        time.sleep(JEDA + random.uniform(0, JITTER))
    nasional, provinsi = bangun_csv()
    n_berkas = len(list(MENTAH_PH.glob("*.json")))
    print(f"Selesai: ambil {n_ambil} cache {n_cache} kosong {n_kosong} berkas {n_berkas}")
    print(f"CSV tidur: nasional {len(nasional)} baris | provinsi {len(provinsi)} baris")


if __name__ == "__main__":
    main()
