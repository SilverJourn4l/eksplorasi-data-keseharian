"""
Pengambilan data Edisi 005: harga harian pangan strategis dari PIHPPS
(Pusat Informasi Harga Pangan Strategis Nasional, bi.go.id/hargapangan).

Mengapa sumber ini: PIHPPS mencatat harga rata-rata tiap provinsi setiap hari
kerja sejak 2018, hasil survei enumerator yang dikoordinasi Bank Indonesia,
dengan titik unduh JSON yang bisa diakses otomatis. Kontrak endpoint sudah
diuji langsung dan didokumentasikan publik; tiga header di bawah ini wajib,
tanpa itu server membalas kosong.

Strategi:
- Empat komoditas (cabai merah, cabai rawit, bawang merah, beras) untuk
  tujuh musim Nataru (Sep-Mar 2019/20 sampai 2025/26).
- Satu permintaan per tanggal hari kerja per komoditas; server membalas
  snapshot 34 provinsi plus rata-rata nasional yang dihitung server.
- Setiap respons disimpan mentah di data/mentah/pihps/, jadi skrip ini
  incremental: jalankan ulang untuk melanjutkan, bukan mengulang.
- Server mengembalikan "tanggal rilis terakhir" bila diminta tanggal tanpa
  rilis baru; tanggal balasan disimpan dan deduplikasi terjadi otomatis
  karena nama berkas tanggal-balasan ditimpa.

Jalankan: python3 unduh_data.py
"""

import argparse
import json
import random
import time
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import requests

BASE = "https://www.bi.go.id/hargapangan/WebSite/Home/GetGridData1"
HEADER = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/125.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://www.bi.go.id/hargapangan",
}

KOMODITAS = {7: "Cabai Merah", 8: "Cabai Rawit", 5: "Bawang Merah", 1: "Beras"}
MUSIM_AWAL = 2019          # musim 2019/20
MUSIM_AKHIR = 2026         # musim 2025/26 (Sep 2025-Mar 2026)
JENDELA = ((9, 1), (3, 31))  # (bulan, tanggal) mulai Sep 1 sampai Mar 31
JEDA = 1.4                 # +jitter; kontrak menyarankan minimal 1,2 dtk
GAGAL_BERUNTUN_MAKS = 6    # berhenti sopan bila diblok (403/429 beruntun)

FOLDER = Path(__file__).parent
MENTAH = FOLDER / "data" / "mentah" / "pihps"
MENTAH.mkdir(parents=True, exist_ok=True)


def hari_kerja(musim_awal, musim_akhir):
    """Daftar tanggal hari kerja dalam jendela Sep-Mar untuk tiap musim."""
    for tahun in range(musim_awal, musim_akhir):
        mulai = date(tahun, JENDELA[0][0], JENDELA[0][1])
        akhir = date(tahun + 1, JENDELA[1][0], JENDELA[1][1])
        t = mulai
        while t <= akhir:
            if t.weekday() < 5:
                yield tahun, t
            t += timedelta(days=1)


def ambil_tanggal(tanggal, komoditas, sesi):
    """Satu snapshot tanggal; kembalikan dict respons atau None bila gagal
    permanen (codec/error), serta kode status HTTP."""
    nama = MENTAH / f"{komoditas}_{tanggal.isoformat()}.json"
    if nama.exists():
        return json.loads(nama.read_text()), 200
    params = {
        "tanggal": tanggal.strftime("%b %-d, %Y"),
        "commodity": komoditas,
        "priceType": 1,
        "isPasokan": 1,
        "jenis": 1,
        "periode": 1,
        "provId": 0,
        "_": int(time.time() * 1000),
    }
    r = sesi.get(BASE, headers=HEADER, params=params, timeout=30)
    if r.status_code != 200:
        return None, r.status_code
    try:
        isi = r.json()
    except ValueError:
        return None, r.status_code
    nama.write_text(json.dumps(isi, ensure_ascii=False))
    return isi, 200


BULAN_SINGKAT = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "mei": 5, "jun": 6,
                 "jul": 7, "agu": 8, "sep": 9, "okt": 10, "nov": 11, "des": 12}


def parse_tanggal_balas(t):
    """Ubah '24 Des 25' menjadi date; kembalikan None bila tidak cocok."""
    bagian = (t or "").split()
    if len(bagian) != 3 or bagian[1].lower() not in BULAN_SINGKAT:
        return None
    try:
        return date(2000 + int(bagian[2]), BULAN_SINGKAT[bagian[1].lower()], int(bagian[0]))
    except ValueError:
        return None


def bangun_csv():
    """Susun dua CSV tidy dari seluruh cache mentah."""
    nas, prov = [], []
    for nama in sorted(MENTAH.glob("*.json")):
        try:
            isi = json.loads(nama.read_text())
        except ValueError:
            continue
        isi_data = isi.get("data", [])
        if not isi_data:
            continue
        tanggal = parse_tanggal_balas(isi_data[0].get("Tanggal"))
        if tanggal is None:
            continue
        for baris in isi_data:
            prov.append({
                "tanggal": tanggal.isoformat(),
                "komoditas": baris.get("Komoditas"),
                "provinsi": baris.get("Provinsi"),
                "harga": baris.get("Nilai"),
            })
        nas.append({
            "tanggal": tanggal.isoformat(),
            "komoditas": isi_data[0].get("Komoditas"),
            "harga_nasional": isi_data[0].get("SemuaProvinsi"),
        })
    nasional = pd.DataFrame(nas).drop_duplicates(["tanggal", "komoditas"]).sort_values(["komoditas", "tanggal"])
    provinsi = pd.DataFrame(prov).drop_duplicates(["tanggal", "komoditas", "provinsi"])
    nasional.to_csv(FOLDER / "data" / "harga-nasional.csv", index=False)
    provinsi.to_csv(FOLDER / "data" / "harga-provinsi.csv", index=False)
    return nasional, provinsi


def main():
    ap = argparse.ArgumentParser(description="Panen harga PIHPPS Edisi 005")
    ap.add_argument("--batasi", type=int, default=0, help="uji cepat N tanggal pertama")
    ap.add_argument("--musim-awal", type=int, default=MUSIM_AWAL)
    ap.add_argument("--musim-akhir", type=int, default=MUSIM_AKHIR)
    ap.add_argument("--komoditas", type=int, nargs="*", default=list(KOMODITAS))
    args = ap.parse_args()

    sesi = requests.Session()
    gagal_run = 0
    n_ambil = n_cache = n_kosong = 0
    tugas = [(kom, t) for _, t in hari_kerja(args.musim_awal, args.musim_akhir)
             for kom in args.komoditas]
    if args.batasi:
        tugas = tugas[: args.batasi]
    total = len(tugas)
    print(f"Tugas: {total} permintaan ({args.musim_awal}-{args.musim_akhir})")
    for i, (kom, t) in enumerate(tugas, 1):
        nama = MENTAH / f"{kom}_{t.isoformat()}.json"
        if nama.exists():
            n_cache += 1
            continue
        isi, kode = ambil_tanggal(t, kom, sesi)
        if isi is None:
            gagal_run += 1
            print(f"[{i}/{total}] {t} kom{kom} GAGAL kode={kode}")
            if gagal_run >= GAGAL_BERUNTUN_MAKS or kode in (403, 429):
                print(f"Berhenti sopan: {gagal_run} gagal beruntun / kode {kode}.")
                break
        else:
            gagal_run = 0
            n_ambil += 1
            if not isi.get("data"):
                n_kosong += 1
            if n_ambil % 100 == 0:
                print(f"[{i}/{total}] terambil {n_ambil}, cache {n_cache}, kosong {n_kosong}")
        time.sleep(JEDA + random.uniform(0, 0.6))
    n_berkas = len(list(MENTAH.glob("*.json")))
    nasional, provinsi = bangun_csv()
    print(f"\nSelesai: ambil {n_ambil}, cache {n_cache}, kosong {n_kosong}, berkas mentah {n_berkas}")
    print(f"CSV: harga-nasional {len(nasional)} baris, harga-provinsi {len(provinsi)} baris")


if __name__ == "__main__":
    main()
