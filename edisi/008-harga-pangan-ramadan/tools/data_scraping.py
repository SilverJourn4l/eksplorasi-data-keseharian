"""Pengambilan data Edisi 008: harga pangan mingguan PIHPPS sekitar Ramadan.

Kontrak sumber: sama seperti Edisi 005/007 (PIHPS, bi.go.id/hargapangan,
WebSite/Home/GetGridData1, tiga header wajib). Di sini titik waktunya padat:

- 8 tahun Ramadan (2019/20 sampai 2025/26), masing-masing jendela:
  mulai 56 hari sebelum 1 Ramadan, selesai 42 hari setelah 1 Syawal.
  Tanggal 1 Ramadan/1 Syawal = ketetapan pemerintah (sidag isbat Kemenag),
  dirangkum dari siaran resmi dan Kompas/ANTARA (lihat `data/tanggal-ramadan.csv`).
- Satu snapshot per Rabu per jendela, masing-masing per 10 komoditas nasional
  (id 1-10); server membalas snapshot 34 provinsi plus rata-rata nasionalnya.
- Cache mentah di data/mentah/pihps/ membuat skrip ini incremental
  (jalankan ulang = melanjutkan). Server bergeser ke rilis terakhir bila
  tanggal diminta tanpa rilis baru; CSV dibangun dari tanggal balasan.

Jalankan: python3 unduh_data.py
"""

from __future__ import annotations

import argparse
import json
import random
import time
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import requests

FOLDER = Path(__file__).parent
MENTAH = FOLDER / "data" / "mentah" / "pihps"

# Ketetapan pemerintah (sidag isbat Kemenag). 1 Syawal masiji.
RAMADAN = {
    2019: (date(2019, 5, 6), date(2019, 6, 5)),
    2020: (date(2020, 4, 24), date(2020, 5, 24)),
    2021: (date(2021, 4, 14), date(2021, 5, 13)),
    2022: (date(2022, 4, 3), date(2022, 5, 2)),
    2023: (date(2023, 3, 23), date(2023, 4, 22)),
    2024: (date(2024, 3, 12), date(2024, 4, 10)),
    2025: (date(2025, 3, 1), date(2025, 3, 31)),
    2026: (date(2026, 2, 19), date(2026, 3, 21)),
}
JENDELA_SEBELUM, JENDELA_SESUDAH = 56, 42
KOMODITAS = list(range(1, 11))
JEDA, JITTER, GAGAL_BERUNTUN_MAKS = 1.4, 0.6, 6

BASE = "https://www.bi.go.id/hargapangan/WebSite/Home/GetGridData1"
HEADER = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/125.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://www.bi.go.id/hargapangan",
}
BULAN_EN = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
BULAN_SINGKAT = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "mei": 5, "jun": 6,
                 "jul": 7, "agu": 8, "sep": 9, "okt": 10, "nov": 11, "des": 12}


def tulis_tanggal_csv():
    pd.DataFrame(
        [{"tahun_hijri": hij + 1440, "tahun": th, "puasa_mulai": p.isoformat(),
          "lebaran": l.isoformat()} for (th, (p, l)), hij in
         zip(sorted(RAMADAN.items()), range(len(RAMADAN)))]).to_csv(
        FOLDER / "data" / "tanggal-ramadan.csv", index=False)


def rabu_jendela():
    for th, (puasa, lebaran) in RAMADAN.items():
        mulai = puasa - timedelta(days=JENDELA_SEBELUM)
        akhir = lebaran + timedelta(days=JENDELA_SESUDAH)
        t = mulai + timedelta(days=(2 - mulai.weekday()) % 7)
        while t <= akhir:
            yield th, t
            t += timedelta(days=7)


def parse_tanggal_balas(t):
    bagian = (t or "").split()
    if len(bagian) != 3 or bagian[1].lower() not in BULAN_SINGKAT:
        return None
    try:
        return date(2000 + int(bagian[2]), BULAN_SINGKAT[bagian[1].lower()], int(bagian[0]))
    except ValueError:
        return None


def ambil(sesi, tanggal, kom):
    nama = MENTAH / f"{kom}_{tanggal.isoformat()}.json"
    if nama.exists():
        return json.loads(nama.read_text()), 200
    r = sesi.get(BASE, headers=HEADER, params={
        "tanggal": f"{BULAN_EN[tanggal.month]} {tanggal.day}, {tanggal.year}",
        "commodity": kom, "priceType": 1, "isPasokan": 1, "jenis": 1,
        "periode": 1, "provId": 0, "_": int(time.time() * 1000)}, timeout=30)
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
    for nama in sorted(MENTAH.glob("*.json")):
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
    (pd.DataFrame(nas).drop_duplicates(["tanggal", "komoditas"])
       .sort_values(["komoditas", "tanggal"])
       .to_csv(FOLDER / "data" / "harga-nasional-mingguan.csv", index=False))
    (pd.DataFrame(prov).drop_duplicates(["tanggal", "komoditas", "provinsi"])
       .to_csv(FOLDER / "data" / "harga-provinsi-mingguan.csv", index=False))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batasi", type=int, default=0)
    args = ap.parse_args()
    MENTAH.mkdir(parents=True, exist_ok=True)
    tulis_tanggal_csv()

    sesi = requests.Session()
    tugas = [(kom, th, t) for th, t in rabu_jendela() for kom in KOMODITAS]
    if args.batasi:
        tugas = tugas[: args.batasi]
    n_ambil = n_cache = n_kosong = gagal_run = 0
    total = len(tugas)
    print(f"Tugas: {total} permintaan (8 Ramadan x mingguan x 10 komoditas)")
    for i, (kom, th, t) in enumerate(tugas, 1):
        if (MENTAH / f"{kom}_{t.isoformat()}.json").exists():
            n_cache += 1
            continue
        isi, kode = ambil(sesi, t, kom)
        if isi is None:
            gagal_run += 1
            print(f"[{i}/{total}] {t} kom{kom} GAGAL {kode}")
            if gagal_run >= GAGAL_BERUNTUN_MAKS or kode in (403, 429):
                print("Berhenti sopan: diblok beruntun.")
                break
        else:
            gagal_run = 0
            n_ambil += 1
            if not isi.get("data"):
                n_kosong += 1
            if n_ambil % 200 == 0:
                print(f"[{i}/{total}] ambil {n_ambil} | cache {n_cache} | kosong {n_kosong}", flush=True)
        time.sleep(JEDA + random.uniform(0, JITTER))
    bangun_csv()
    n_berkas = len(list(MENTAH.glob("*.json")))
    print(f"Selesai: ambil {n_ambil} cache {n_cache} kosong {n_kosong} berkas {n_berkas}")


if __name__ == "__main__":
    main()
