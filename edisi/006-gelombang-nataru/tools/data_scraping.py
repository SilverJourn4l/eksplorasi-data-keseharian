"""
Pengambilan data Edisi 006: perjalanan nyata dan niat mencari tiket di masa
Nataru, dari dua sumber terbuka.

Sumber A (perjalanan nyata): Kementerian Perhubungan, katalog HUBNET
"Data Harian Pergerakan Penumpang Angkutan Lebaran, Natal dan Tahun Baru"
(event NATARU 2024 2025, pantauan H-7 s.d. H+10, per moda). Satu panggilan
JSON mengembalikan rangkaian harian; disimpan mentah sekali.

Sumber B (niat): indeks Google Trends (lewat pustaka tak resmi `pytrends`)
untuk frasa pencarian tiket. Dua lapis pengambilan:
- Lintas musim: satu rentang mingguan Sep 2019-Mar 2026 untuk sampai lima
  frasa, sehingga semua titik berbagi skala 0-100 yang sama.
- Zoom harian per musim (Sep-Mar per musim), karena Trends hanya mengembalikan
  resolusi harian untuk rentang pendek; tiap musim dinormalkan sendiri, jadi
  lintas musimnya hanya boleh dibaca dari lapis mingguan.

Keterbatasan yang memang melekat dicatat di data/README.md: indeks Trends
adalah proporsi pencarian (0-100), bukan jumlah orang; dan API ini tak resmi.
Jika server menolak (429), skrip berhenti sopan supaya bisa dilanjutkan nanti
(cache membuatnya incremental).

Jalankan: python3 unduh_data.py
"""

import json
import time
import random
from pathlib import Path

import pandas as pd
import requests

UA = {"User-Agent": "JurnalDataKeseharian/1.0 (riset publik; kontak: pengelola@example.com)"}
URL_KEMENHUB = ("https://hubnet.kemenhub.go.id/dataset/get-data-api/microstrategy/"
                "data_event_kemenpar?event=NATARU%202024%202025&format=json")

FRASA = ["tiket kereta api", "tiket pesawat", "tiket bus"]
GEO = "ID"
MINGGUAN_MULAI, MINGGUAN_AKHIR = "2019-09-01", "2026-03-31"
MUSIM = list(range(2019, 2026))  # 2019/20 s.d. 2025/26
JEDA = 4.0

FOLDER = Path(__file__).parent
MENTAH = FOLDER / "data" / "mentah" / "trends"
MENTAH.mkdir(parents=True, exist_ok=True)


def ambil_kemenhub():
    cache = MENTAH / "kemenhub-nataru-2024-2025.json"
    if not cache.exists():
        r = requests.get(URL_KEMENHUB, headers=UA, timeout=60)
        r.raise_for_status()
        cache.write_text(r.text)
        time.sleep(JEDA)
    d = json.loads(cache.read_text())
    df = pd.DataFrame(d)
    df["tanggal"] = pd.to_datetime(df["tanggal"])
    df = df.sort_values(["moda", "tanggal"])
    df.to_csv(FOLDER / "data" / "pergerakan-nataru-2024-25.csv", index=False)
    print(f"Kemenhub: {len(df)} baris, moda: {sorted(df['moda'].unique())}")
    print(f"  tanggal: {df['tanggal'].min().date()} s.d. {df['tanggal'].max().date()}")
    return df


def klien_trends():
    from pytrends.request import TrendReq
    return TrendReq(hl="id-ID", tz=420, timeout=30)


def ambil_panel(nama_cache, timeframe, frasa, klien):
    cache = MENTAH / nama_cache
    if cache.exists():
        return pd.read_csv(cache, parse_dates=["date"])
    mencoba = 0
    while True:
        mencoba += 1
        try:
            klien.build_payload(frasa, timeframe=timeframe, geo=GEO)
            df = klien.interest_over_time()
            df = df.drop(columns=["isPartial"], errors="ignore").reset_index()
            df.to_csv(cache, index=False)
            print(f"  {nama_cache}: {len(df)} baris")
            time.sleep(JEDA + random.uniform(0, 2))
            return df
        except Exception as e:
            pesan = str(e).lower()
            if ("429" in pesan or "too many" in pesan or mencoba >= 4):
                print(f"  BERHENTI di {nama_cache}: {type(e).__name__} (percobaan {mencoba})")
                return pd.DataFrame()
            tunggu = 30 * mencoba
            print(f"  gagal ({type(e).__name__}); coba lagi dalam {tunggu} dtk...")
            time.sleep(tunggu)


def ambil_trends(klien):
    ambil_panel("trends-mingguan-2019-2026.csv", f"{MINGGUAN_MULAI} {MINGGUAN_AKHIR}", FRASA, klien)
    for musim in MUSIM:
        ambil_panel(f"trends-harian-{musim}.csv", f"{musim}-09-01 {musim + 1}-03-31", FRASA, klien)


def main():
    ambil_kemenhub()
    ambil_trends(klien_trends())
    n = len(list(MENTAH.glob("*.csv")))
    print(f"\nSelesai: {n} berkas cache trends + 1 cache kemenhub")


if __name__ == "__main__":
    main()
